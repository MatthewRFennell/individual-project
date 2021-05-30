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

import gdb
import json
import collections
from pprint import pprint
from replay_reader.checkpoint_parser import checkpoint_parser

class ThreadManager:
	def __init__(self, checkpoints):
		self._alive_threads = set()
		self._checkpoints = checkpoints

	def get_all_threads(self):
		return set(map(lambda checkpoint: checkpoint["thread"], self._checkpoints))

	def update_alive_threads(self):
		print("I MADE IT TO update_alive_threads")
		self._alive_threads = set(
				map(lambda thread: thread.global_num, gdb.inferiors()[0].threads())
		)

	def _is_in_assembly_code(self):
		return gdb.selected_frame().function() is None

	def _get_thread_out_of_assembly_code(self, thread):
		current_thread = gdb.selected_thread().global_num
		gdb.execute(f"thread {thread}")
		if self._is_in_assembly_code():
			gdb.execute("finish")
		gdb.execute(f"thread {current_thread}")

	def get_all_threads_out_of_assembly_code(self):
		print("I MADE IT TO get_all_threads_out_of_assembly_code")
		print(self._alive_threads)
		for thread in self._alive_threads:
			self._get_thread_out_of_assembly_code(thread)
		print("ALL THREADS SHOULD BE OUT OF ASSEMBLY CODE AT THIS POINT")
		gdb.execute("info threads")

class BreakpointManager:
	def __init__(self, checkpoints):
		self.checkpoints = checkpoints
		for checkpoint in self.checkpoints:
			checkpoint.update({"hit": False})

	def set_next_breakpoint_for_thread(self, thread):
		next_checkpoint = self._next_checkpoint_for(thread)["hits"]
		next_breakpoint = gdb.Breakpoint(next_checkpoint, temporary=True)
		next_breakpoint.thread = thread

	def get_next_checkpoint(self):
		return next(filter(
				lambda checkpoint: checkpoint["hit"] == False, self.checkpoints))

	def mark_next_checkpoint_as_hit(self):
		self.get_next_checkpoint()["hit"] = True
		pprint(self.checkpoints)

	def is_next_breakpoint(self, breakpoint):
		return breakpoint.location == self.get_next_checkpoint()["hits"] and \
				breakpoint.thread == self.get_next_checkpoint()["thread"]

	def _checkpoints_for_thread(self, thread):
		return list(filter(lambda checkpoint: checkpoint["thread"] == thread and \
				checkpoint["hit"] == False, self.checkpoints))
	
	def thread_should_finish(self, thread):
		return len(self._checkpoints_for_thread(thread)) == 1

	def _next_checkpoint_for(self, thread):
		return next(iter(self._checkpoints_for_thread(thread)))

class ExecutionManager:
	def __init__(self, breakpoint_manager, thread_manager):
		self._breakpoint_manager = breakpoint_manager
		self._thread_manager = thread_manager

	def update_alive_threads(self):
		self._thread_manager.update_alive_threads()

	def run_to_next_checkpoint(self):
		if self._target_is_running():
			self._continue_until_next_checkpoint_or_end(
					self._breakpoint_manager.get_next_checkpoint()["thread"]
			)

	def run_to_next_checkpoint_if_hit(self, breakpoint):
		self.update_alive_threads()
		if self._breakpoint_manager.is_next_breakpoint(breakpoint):
			self._breakpoint_manager.mark_next_checkpoint_as_hit()
			self._thread_manager.get_all_threads_out_of_assembly_code()
			self.run_to_next_checkpoint()

	def _continue_until_next_checkpoint(self, thread):
		self._breakpoint_manager.set_next_breakpoint_for_thread(thread)
		self.continue_thread(thread)

	def _continue_until_next_checkpoint_or_end(self, thread):
		if self._breakpoint_manager.thread_should_finish(thread):
			self.continue_thread(thread)
			return
		self._continue_until_next_checkpoint(thread)

	def _target_is_running(self):
		return True

	def _current_thread(self):
		return gdb.selected_thread().global_num

	def continue_thread(self, thread):
		gdb.execute(f"thread {thread}")
		gdb.execute("continue")

# Functions + classes
class BreakListener:
	def __init__(self, execution_manager):
		self._execution_manager = execution_manager

	def __call__(self, event):
		if not self._is_checkpoint(event):
			return
		self._execution_manager.run_to_next_checkpoint_if_hit(event.breakpoint)
	
	def _is_checkpoint(self, event):
		return hasattr(event, "breakpoint")

def pause_target_at_beginning():
	entry_breakpoint = gdb.Breakpoint("main")
	gdb.execute("run")
	gdb.execute("set scheduler-locking on")

def main():
	pause_target_at_beginning()

	parser = checkpoint_parser("./checkpoints.json")

	checkpoints = parser.get_checkpoints()
	breakpoint_manager = BreakpointManager(checkpoints)
	thread_manager = ThreadManager(checkpoints)
	execution_manager = ExecutionManager(breakpoint_manager, thread_manager)
	gdb.events.stop.connect(BreakListener(execution_manager))
	execution_manager.run_to_next_checkpoint()

if __name__ == "__main__":
	main()
