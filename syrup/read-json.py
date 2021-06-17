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
from gdb_wrapper import gdb_wrapper
from collections import Counter
from pprint import pprint
from replay_reader.checkpoint_parser import checkpoint_parser
from logger.logger import log

CHECKPOINT_LOCATION_TAG = "location"
CHECKPOINT_THREAD_TAG = "thread"
CHECKPOINT_ACTION_TAG = "action"
CHECKPOINT_IS_HIT_TAG = "is_hit"
ACTION_CREATE_THREAD_TAG = "create_thread"
CHECKPOINT_FILE_LOCATION = "./checkpoints.json"
MAIN_THREAD = 1

class CheckpointManager:
	def __init__(self, checkpoints):
		self.checkpoints = checkpoints
		for checkpoint in self.checkpoints:
			checkpoint.update({CHECKPOINT_IS_HIT_TAG: False})
		self.set_breakpoints_for_thread(MAIN_THREAD)
		self._alive_threads = set([MAIN_THREAD])

	# Public methods
	def update_alive_threads(self):
		self._alive_threads = self._currently_alive_threads()

	def newly_created_thread(self):
		newly_created_threads = self._currently_alive_threads().difference(self._alive_threads)
		assert len(newly_created_threads) == 1, "More than one thread created since last check"
		return next(iter(newly_created_threads))

	def mark_next_checkpoint_as_hit_for_thread(self, thread):
		next_checkpoint = self._next_checkpoint_for_thread(thread)
		next_checkpoint[CHECKPOINT_IS_HIT_TAG] = True
		log(f"Marked {next_checkpoint} as hit")

	def set_breakpoints_for_thread(self, thread):
		for location in self._breakpoints_for_thread(thread):
			gdb_wrapper.immediate_breakpoint_at(location, thread)

	def switch_to_thread_for_next_checkpoint(self):
		next_thread = self._next_checkpoint()[CHECKPOINT_THREAD_TAG]
		log(f"Next thread: {next_thread}")
		gdb_wrapper.enqueue_execute(f"thread {next_thread}")

	def current_thread_should_finish(self):
		log("Called current_thread_should_finish")
		remaining_thread_checkpoints = len(self._checkpoints_left_for_thread(self.current_thread()))
		log(f"{remaining_thread_checkpoints} checkpoints left for current thread")
		return remaining_thread_checkpoints == 0

	def current_thread(self):
		current_thread = gdb.selected_thread().global_num
		log(f"Current thread: {current_thread}")
		return current_thread

	# Private methods
	def _checkpoints_left_for_thread(self, thread):
		log(f"Called _checkpoints_for_thread {thread}")
		remaining_checkpoints = list(filter(
			lambda checkpoint: checkpoint[CHECKPOINT_THREAD_TAG] == thread and
			not checkpoint[CHECKPOINT_IS_HIT_TAG], self.checkpoints
		))
		return remaining_checkpoints


	def _next_checkpoint(self):
		next_checkpoint = next(filter(
			lambda checkpoint: not checkpoint[CHECKPOINT_IS_HIT_TAG], self.checkpoints
		))
		log("I want to hit this checkpoint next:")
		pprint(next_checkpoint)
		return next_checkpoint

	def _next_checkpoint_for_thread(self, thread):
		next_checkpoint = next(filter(
			lambda checkpoint: not checkpoint[CHECKPOINT_IS_HIT_TAG] and \
					checkpoint[CHECKPOINT_THREAD_TAG] == thread,
			self.checkpoints
		))
		return next_checkpoint

	def _currently_alive_threads(self):
		return set(
				map(lambda thread: thread.global_num, gdb.inferiors()[0].threads())
		)

	def _breakpoints_for_thread(self, thread):
		return set(map(
			lambda checkpoint: checkpoint[CHECKPOINT_LOCATION_TAG],
			self._checkpoints_for_thread(thread)
		))

	def _checkpoints_for_thread(self, thread):
		return list(filter(
			lambda checkpoint: checkpoint[CHECKPOINT_THREAD_TAG] == thread,
			self.checkpoints
		))

class BreakListener:
	def __init__(self, checkpoint_manager):
		self._checkpoint_manager = checkpoint_manager

	def __call__(self, event):
		log("BreakListener hit!")
		self._checkpoint_manager.mark_next_checkpoint_as_hit_for_thread(
			self._checkpoint_manager.current_thread()
		)
		if self._checkpoint_manager.current_thread_should_finish():
			log(f"Finishing current thread as all checkpoints have been hit")
			gdb_wrapper.enqueue_execute("continue")
		self._checkpoint_manager.switch_to_thread_for_next_checkpoint()
		gdb_wrapper.enqueue_execute("continue")

class ThreadCreationListener:
	def __init__(self, checkpoint_manager):
		self._checkpoint_manager = checkpoint_manager

	def __call__(self, event):
		log("ThreadCreationListener hit!")
		creator_thread = event.inferior_thread.num
		created_thread = self._checkpoint_manager.newly_created_thread()
		log(f"creator_thread: {creator_thread}, created_thread: {created_thread}")
		self._checkpoint_manager.update_alive_threads()
		self._checkpoint_manager.set_breakpoints_for_thread(created_thread)
		self._checkpoint_manager.switch_to_thread_for_next_checkpoint()

def setup_gdb():
	configure_gdb_to_run_as_a_script()
	pause_target_at_beginning()

def configure_gdb_to_run_as_a_script():
	gdb_wrapper.immediate_execute("set confirm off")
	gdb_wrapper.immediate_execute("set pagination off")

def pause_target_at_beginning():
	entry_breakpoint = gdb_wrapper.immediate_breakpoint_at("main", is_temporary=True)
	gdb_wrapper.immediate_execute("run")
	gdb_wrapper.immediate_execute("set scheduler-locking on")

def connect_listeners(checkpoint_manager):
	gdb_wrapper.immediate_connect(gdb.events.stop, BreakListener(checkpoint_manager))
	gdb_wrapper.immediate_connect(gdb.events.new_thread, ThreadCreationListener(checkpoint_manager))

def main():
	setup_gdb()
	checkpoint_manager = CheckpointManager(
		checkpoint_parser(CHECKPOINT_FILE_LOCATION).get_checkpoints()
	)
	connect_listeners(checkpoint_manager)
	gdb_wrapper.enqueue_execute("continue")

if __name__ == "__main__":
	main()
