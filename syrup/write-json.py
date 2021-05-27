#!/bin/python3

import gdb
import json

# This class records the order in which checkpoints are hit when the program
# executes. A checkpoint is an assembly instruction which reads from or writes
# to a variable that is shared between threads.
class CheckpointRecorder:
	THREAD_ID_TAG = "thread"
	CHECKPOINT_LOCATION_TAG = "hits"

	def __init__(self):
		self.hit_checkpoints = []

	# This function is called by GDB whenever a breakpoint is hit. We only set
	# breakpoints for reads and writes to shared variables.
	def __call__(self, event):
		self._record_hit_checkpoint()
		gdb.execute("continue")

	def _record_hit_checkpoint(self):
		thread_id = gdb.selected_thread().num
		checkpoint_location = hex(gdb.selected_frame().pc())
		self.hit_checkpoints.append({
				self.THREAD_ID_TAG: thread_id,
				self.CHECKPOINT_LOCATION_TAG: f"*{checkpoint_location}"
		})

	def get_hit_checkpoints(self):
		return self.hit_checkpoints

# We record the names of the start routines of each thread for use in the replay 
# later. This allows the replay tool to synchronise threads correctly.
def thread_start_routines():
	return ["increment"]

# We want the interleavings of threads with respect to shared variables to be 
# recorded. Therefore, we only need to record the ordering of writes and reads
# to shared variables.
def set_shared_variable_breakpoints():
	shared_variables = ["counter"]
	for shared_variable in shared_variables:
		gdb.Breakpoint(shared_variable, gdb.BP_WATCHPOINT, gdb.WP_ACCESS)

def main():
	CHECKPOINT_JSON_TAG = "checkpoints"
	START_ROUTINE_JSON_TAG = "thread_start_routines"
	OUTPUT_FILE = "./checkpoints.json"
	OUTPUT_FILE_INDENT_WIDTH = 2

	checkpoint_recorder = CheckpointRecorder()
	gdb.events.stop.connect(checkpoint_recorder)
	set_shared_variable_breakpoints()
	gdb.execute("run")

	replay = {}
	replay[CHECKPOINT_JSON_TAG] = checkpoint_recorder.get_hit_checkpoints()
	replay[START_ROUTINE_JSON_TAG] = thread_start_routines()

	with open(OUTPUT_FILE, "w+") as output_file:
		json.dump(replay, output_file, indent=OUTPUT_FILE_INDENT_WIDTH)

if __name__ == "__main__":
	main()
