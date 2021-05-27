#!/bin/python3

import gdb
import json
import sys
from pprint import pprint
from enum import Enum

# This class records checkpoints that are hit during execution of the program.
# A checkpoint is when a variable that is shared between threads is read from or
# written to.
class CheckpointRecorder:
	def __init__(self, entry_points_to_ignore):
		self.entry_points_to_ignore = entry_points_to_ignore
		self.hit_checkpoints = []

	# This function is called by gdb whenever a breakpoint is hit. However, we
	# only want to record breakpoints that correspond to a shared variable
	# changing. We also register breakpoints on each thread's start routine in
	# order to control execution.
	def __call__(self, event):
		if event.breakpoint not in self.entry_points_to_ignore:
			frame = gdb.selected_frame()
			self.hit_checkpoints.append(
					{"thread": gdb.selected_thread().num, "hits": f"*{hex(frame.pc())}"})
		gdb.execute("continue")

	def get_hit_checkpoints(self):
		return self.hit_checkpoints

def entry_points():
	entry_point = gdb.Breakpoint("increment", gdb.BP_BREAKPOINT)
	entry_point.enabled = False
	return [entry_point]

def shared_variables():
	counter = gdb.Breakpoint("counter", gdb.BP_WATCHPOINT, gdb.WP_ACCESS)
	return [counter]

def main():
	CHECKPOINT_JSON_TAG = "checkpoints"
	ENTRYPOINT_JSON_TAG = "entry_points"
	OUTPUT_FILE = "./checkpoints.json"
	OUTPUT_FILE_INDENT_WIDTH = 2

	replay = {}
	replay[CHECKPOINT_JSON_TAG] = []
	replay[ENTRYPOINT_JSON_TAG] = list(
			set(map(lambda breakpoint: breakpoint.location, entry_points())))
	shared_variable_breakpoints = shared_variables()
	listener = CheckpointRecorder(replay[ENTRYPOINT_JSON_TAG])
	gdb.events.stop.connect(listener)
	gdb.execute("run")
	replay[CHECKPOINT_JSON_TAG] = listener.get_hit_checkpoints()
	with open(OUTPUT_FILE, "w+") as thread_switch_file:
		json.dump(replay, thread_switch_file, indent=OUTPUT_FILE_INDENT_WIDTH)

if __name__ == "__main__":
	main()
