#!/bin/python3

# GDB requires that we source our python script from within GDB to run it. This
# means that the current directory is not included in the path, which means it
# is not possible to import local modules. Therefore, we need to add the current
# directory to the path to allow it to be run from within GDB. This has the
# consequence that GDB must be launched from the directory outside the syrup
# directory.
import sys
CURRENT_DIRECTORY = "syrup"
sys.path.append(CURRENT_DIRECTORY)

LOG_FILENAME = "log"
CHECKPOINT_LOCATION_TAG = "hits"

import gdb
import json
import collections
from pprint import pprint
from replay_reader.checkpoint_parser import checkpoint_parser

class ThreadManager:
	def __init__(self, checkpoints):
		self._alive_threads = set([1])
		self._checkpoints = checkpoints

	def get_all_threads(self):
		return set(map(lambda checkpoint: checkpoint["thread"], self._checkpoints))

	def update_alive_threads(self):
		print("I MADE IT TO update_alive_threads")
		self._alive_threads = self._currently_alive_threads()

	def _currently_alive_threads(self):
		return set(
				map(lambda thread: thread.global_num, gdb.inferiors()[0].threads())
		)

	def newly_alive_threads(self):
		return self._currently_alive_threads().difference(self._alive_threads)

	def get_thread_out_of_assembly_code(self, thread, thread_to_switch_back_to):
		print("HELLO FROM get_thread_out_of_assembly_code")
		print(f"GET {thread} OUT OF ASSEMBLY CODE")
		gdb_execute(f"thread {thread}")
		print(f"HELLO1")
		gdb_execute("info threads")
		# TODO instead of finish, maybe consider breaking here and see if that fixes
		# the running thread problem. Might need to properly formulate what the
		# program should do as well
		gdb_execute("finish")
		print(f"HELLO2")
		gdb_execute(f"thread {thread_to_switch_back_to}")
		print(f"HELLO3")

class BreakpointManager:
	def __init__(self, checkpoints):
		self.checkpoints = checkpoints
		for checkpoint in self.checkpoints:
			checkpoint.update({"hit": False})

	def set_next_breakpoint_for_thread(self, thread):
		next_checkpoint = self._next_checkpoint_for(thread)[CHECKPOINT_LOCATION_TAG]
		next_breakpoint = gdb_breakpoint_at(next_checkpoint, temporary=True)
		next_breakpoint.thread = thread

	def get_next_checkpoint(self):
		return next(filter(
				lambda checkpoint: checkpoint["hit"] == False, self.checkpoints))

	def mark_next_checkpoint_as_hit(self):
		self.get_next_checkpoint()["hit"] = True
		pprint(self.checkpoints)

	def is_next_breakpoint(self, breakpoint):
		return breakpoint.location == \
				self.get_next_checkpoint()[CHECKPOINT_LOCATION_TAG] and \
				breakpoint.thread == self.get_next_checkpoint()["thread"]

	def next_checkpoint_for_thread(self, thread):
		assert len(self._checkpoints_for_thread(thread)) > 0, \
				"Tried to get the next checkpoint of a thread for whom all the \
						checkpoints have been hit"
		return self._checkpoints_for_thread(thread)[0]

	def _checkpoints_for_thread(self, thread):
		return list(filter(lambda checkpoint: checkpoint["thread"] == thread and \
				not checkpoint["hit"], self.checkpoints))
	
	def thread_should_finish(self, thread):
		return len(self._checkpoints_for_thread(thread)) == 1

	def _next_checkpoint_for(self, thread):
		return next(iter(self._checkpoints_for_thread(thread)))

class ExecutionManager:
	def __init__(self, breakpoint_manager, thread_manager):
		self._breakpoint_manager = breakpoint_manager
		self._thread_manager = thread_manager
		self._is_exiting_thread = False

	def update_alive_threads(self):
		self._thread_manager.update_alive_threads()

	def run_to_next_checkpoint(self):
		if self._target_is_running():
			self._continue_until_next_checkpoint_or_end(
					self._breakpoint_manager.get_next_checkpoint()["thread"]
			)

	def run_to_next_checkpoint_if_hit(self, breakpoint):
		self.update_execution_state()
		if self._breakpoint_manager.is_next_breakpoint(breakpoint):
			self.mark_next_checkpoint_as_hit()
			self.run_to_next_checkpoint()

	def is_next_breakpoint(self, breakpoint):
		return self._breakpoint_manager.is_next_breakpoint(breakpoint)

	def mark_next_checkpoint_as_hit(self):
		self._breakpoint_manager.mark_next_checkpoint_as_hit()

	def is_exiting_thread(self):
		return self._is_exiting_thread

	def mark_thread_as_exited(self):
		self._is_exiting_thread = False

	def update_execution_state(self):
		self.update_alive_threads()

	def newly_alive_threads(self):
		return self._thread_manager.newly_alive_threads()

	def get_thread_out_of_assembly_code(self, thread, thread_to_switch_back_to):
		self._thread_manager.get_thread_out_of_assembly_code(
				thread, thread_to_switch_back_to
		)

	def next_checkpoint_for_thread(self, thread):
		return self._breakpoint_manager.next_checkpoint_for_thread(thread)

	def _continue_until_next_checkpoint(self, thread):
		print("I MADE IT TO continue_until_next_checkpoint")
		self._breakpoint_manager.set_next_breakpoint_for_thread(thread)
		self.continue_thread(thread)

	def _continue_until_next_checkpoint_or_end(self, thread):
		print(f"I MADE IT TO continue_until_next_checkpoint_or_end: {thread}")
		gdb_execute("info threads")
		if self._breakpoint_manager.thread_should_finish(thread):
			self._continue_until_end(thread)
			return
		self._continue_until_next_checkpoint(thread)

	def _continue_until_end(self, thread):
		self._is_exiting_thread = True
		self.continue_thread(thread)

	def _target_is_running(self):
		return True

	def _current_thread(self):
		return gdb.selected_thread().global_num

	def continue_thread(self, thread):
		print(f"I MADE IT TO continue_thread: continuing thread {thread}")
		gdb_execute(f"thread {thread}")
		gdb_execute("continue")

class BreakListener:
	def __init__(self, execution_manager):
		self._execution_manager = execution_manager

	def __call__(self, event):
		if not self._is_checkpoint(event) and not \
				self._execution_manager.is_exiting_thread():
			return
		is_guaranteed_hit = self._execution_manager.is_exiting_thread()
		if is_guaranteed_hit:
			self._execution_manager.update_execution_state()
			self._execution_manager.mark_next_checkpoint_as_hit()
			self._execution_manager.run_to_next_checkpoint()
			return
		self._execution_manager.run_to_next_checkpoint_if_hit(event.breakpoint)
	
	def _is_checkpoint(self, event):
		return hasattr(event, "breakpoint")

class ThreadCreationListener:
	def __init__(self, execution_manager):
		self._execution_manager = execution_manager

	def __call__(self, event):
		print(f"CREATED THREAD {event.inferior_thread}")
		write_to_log("\"Hit start routine of new thread\"")
		assert len(self._execution_manager.newly_alive_threads()) == 1, \
				"More than one newly created thread detected by ThreadCreationListener"
		creator_thread = event.inferior_thread.num
		newly_created_thread = next(iter(
				self._execution_manager.newly_alive_threads()
		))
		# At this point neither the creator thread or created thread checkpoints
		# have been hit
		breakpoint = gdb_breakpoint_at(
				self._execution_manager.next_checkpoint_for_thread(
						newly_created_thread
				)[CHECKPOINT_LOCATION_TAG],
				temporary=True
		)
		gdb_execute(f"thread {creator_thread}")
		gdb_execute("continue")

	def _get_thread_to_start_routine(self, thread):
		self._execution_manager.mark_next_checkpoint_as_hit()
		pprint(self._execution_manager._thread_manager._checkpoints)
		self._execution_manager.run_to_next_checkpoint()

def pause_target_at_beginning():
	entry_breakpoint = gdb_breakpoint_at("main")
	gdb_execute("run")
	gdb_execute("set scheduler-locking on")

def reset_log():
	open("log", "w").close()

def write_to_log(instruction):
	with open(LOG_FILENAME, "a") as log:
		log.write(f"{instruction}\n")

def gdb_execute(instruction):
	write_to_log(instruction)
	gdb.execute(instruction)

def gdb_breakpoint_at(location, temporary=False):
	print(f"GDB BREAKPOINT AT {location}, TEMPORARY={temporary}")
	breakpoint_prefix = ""
	if temporary:
		breakpoint_prefix = "t"
	write_to_log(f"{breakpoint_prefix}b {location}")
	return gdb.Breakpoint(location, temporary=temporary)

def configure_gdb_to_run_as_a_script():
	gdb_execute("set confirm off")
	gdb_execute("set pagination off")

def main():
	reset_log()

	configure_gdb_to_run_as_a_script()
	pause_target_at_beginning()

	parser = checkpoint_parser("./checkpoints.json")

	checkpoints = parser.get_checkpoints()
	breakpoint_manager = BreakpointManager(checkpoints)
	thread_manager = ThreadManager(checkpoints)
	execution_manager = ExecutionManager(breakpoint_manager, thread_manager)
	gdb.events.stop.connect(BreakListener(execution_manager))
	gdb.events.new_thread.connect(ThreadCreationListener(execution_manager))
	execution_manager.run_to_next_checkpoint()
	gdb_execute("quit")

if __name__ == "__main__":
	main()
