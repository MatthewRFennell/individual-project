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

CHECKPOINT_LOCATION_TAG = "location"
CHECKPOINT_THREAD_TAG = "thread"
CHECKPOINT_ACTION_TAG = "action"
CHECKPOINT_HIT_TAG = "is_hit"
ACTION_CREATE_THREAD_TAG = "create_thread"
CHECKPOINT_FILE_LOCATION = "./checkpoints.json"
MAIN_THREAD = 1

class CheckpointManager:
	def __init__(self, checkpoints):
		self.checkpoints = checkpoints
		for checkpoint in self.checkpoints:
			checkpoint.update({CHECKPOINT_HIT_TAG: False})
		self._set_breakpoints_for_thread(MAIN_THREAD)

	def _set_breakpoints_for_thread(self, thread):
		for location in self._breakpoints_for_thread(thread):
			gdb_wrapper.breakpoint_at(location, thread)

	def _breakpoints_for_thread(self, thread):
		checkpoints_to_set = list(filter(
			lambda checkpoint: checkpoint[CHECKPOINT_ACTION_TAG] != ACTION_CREATE_THREAD_TAG,
			self._checkpoints_for_thread(thread)
		))
		return set(map(
			lambda checkpoint: checkpoint[CHECKPOINT_LOCATION_TAG],
			checkpoints_to_set
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
		pass

class ThreadCreationListener:
	def __init__(self, checkpoint_manager):
		self._checkpoint_manager = checkpoint_manager

	def __call__(self, event):
		pass

def setup_gdb():
	configure_gdb_to_run_as_a_script()
	pause_target_at_beginning()

def configure_gdb_to_run_as_a_script():
	gdb_wrapper.execute("set confirm off")
	gdb_wrapper.execute("set pagination off")

def pause_target_at_beginning():
	entry_breakpoint = gdb_wrapper.breakpoint_at("main", is_temporary=True)
	gdb_wrapper.execute("run")
	gdb_wrapper.execute("set scheduler-locking on")

def connect_listeners(checkpoint_manager):
	gdb_wrapper.connect(gdb.events.stop, BreakListener(checkpoint_manager))
	gdb_wrapper.connect(gdb.events.new_thread, ThreadCreationListener(checkpoint_manager))

def main():
	setup_gdb()
	checkpoint_manager = CheckpointManager(
		checkpoint_parser(CHECKPOINT_FILE_LOCATION).get_checkpoints()
	)
	connect_listeners(checkpoint_manager)

if __name__ == "__main__":
	main()
