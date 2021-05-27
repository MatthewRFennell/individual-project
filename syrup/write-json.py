#!/bin/python3

import gdb
import json

class CheckpointRecorder:
	def __init__(self):
		self.hit_checkpoints = []

	def __call__(self, event):
		frame = gdb.selected_frame()
		self.hit_checkpoints.append(
				{"thread": gdb.selected_thread().num, "hits": f"*{hex(frame.pc())}"})
		gdb.execute("continue")

	def get_hit_checkpoints(self):
		return self.hit_checkpoints

def entry_points():
	return ["increment"]

def set_shared_variable_breakpoints():
	gdb.Breakpoint("counter", gdb.BP_WATCHPOINT, gdb.WP_ACCESS)

def main():
	CHECKPOINT_JSON_TAG = "checkpoints"
	ENTRYPOINT_JSON_TAG = "entry_points"
	OUTPUT_FILE = "./checkpoints.json"
	OUTPUT_FILE_INDENT_WIDTH = 2

	checkpoint_recorder = CheckpointRecorder()
	gdb.events.stop.connect(checkpoint_recorder)
	set_shared_variable_breakpoints()
	gdb.execute("run")

	replay = {}
	replay[CHECKPOINT_JSON_TAG] = checkpoint_recorder.get_hit_checkpoints()
	replay[ENTRYPOINT_JSON_TAG] = entry_points()

	with open(OUTPUT_FILE, "w+") as thread_switch_file:
		json.dump(replay, thread_switch_file, indent=OUTPUT_FILE_INDENT_WIDTH)

if __name__ == "__main__":
	main()
