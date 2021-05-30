#!/bin/python3

import gdb
import json

class SyscallRecorder:
	def __init__(self):
		self.checkpoints = set()

	def __call__(self, event):
		self.checkpoints.add(hex(gdb.selected_frame().pc()))
		gdb.execute("continue")

# This class records the order in which checkpoints are hit when the program
# executes. A checkpoint is an assembly instruction which reads from or writes
# to a variable that is shared between threads.
class CheckpointRecorder:
	THREAD_ID_TAG = "thread"
	CHECKPOINT_LOCATION_TAG = "hits"

	def __init__(self, thread_creation_checkpoints):
		self._thread_creation_checkpoints = thread_creation_checkpoints
		self.hit_checkpoints = []
		self._created_threads = set([1])
		self._is_constrained_execution = False

	def __call__(self, event):
		self._record_hit_checkpoint()
		gdb.execute("continue")

	def _record_hit_checkpoint(self):
		thread_id = gdb.selected_thread().num
		checkpoint_location = hex(gdb.selected_frame().pc())
		if self._is_constrained_execution:
			self._resume_unconstrained_execution()
		elif self._is_thread_create() and not self._is_new_thread(thread_id):
			self._handle_newly_created_thread(thread_id)
			return
		self._add_checkpoint(thread_id, checkpoint_location)

	def _add_checkpoint(self, thread_id, checkpoint_location):
		print("ADDING CHECKPOINT")
		self.hit_checkpoints.append({
				self.THREAD_ID_TAG: thread_id,
				self.CHECKPOINT_LOCATION_TAG: f"*{checkpoint_location}"
		})

	def _is_thread_create(self):
		result = hex(gdb.selected_frame().pc()) in self._thread_creation_checkpoints
		print(f"IS_THREAD_CREATE?: {result}")
		return result

	def _handle_newly_created_thread(self, thread_id):
		print("IS_NEW_THREAD_CLONE_BREAKPOINT = TRUE")
		gdb.execute("info threads")
		self._created_threads.add(thread_id)
		self._constrain_execution_to_new_thread(thread_id)

	def _resume_unconstrained_execution(self):
		print("IS_CONSTRAINED_EXECUTION = TRUE")
		print("SCHEDULER LOCKING OFF")
		self._is_constrained_execution = False
		gdb.execute("set scheduler-locking off")

	def _constrain_execution_to_new_thread(self, thread_id):
		print("SCHEDULER LOCKING ON")
		gdb.execute("set scheduler-locking on")
		gdb.execute(f"thread {thread_id}")
		self._is_constrained_execution = True

	def _is_new_thread(self, thread):
		result = thread not in self._created_threads
		print(f"IS_NEW_THREAD?: {result}")
		return result

	def get_hit_checkpoints(self):
		return self.hit_checkpoints

# We want the interleavings of threads with respect to shared variables to be
# recorded. Therefore, we only need to record the ordering of writes and reads
# to shared variables.
def set_shared_variable_breakpoints():
	shared_variables = ["counter"]
	for shared_variable in shared_variables:
		gdb.Breakpoint(shared_variable, gdb.BP_WATCHPOINT, gdb.WP_ACCESS)

def set_syscall_breakpoints(checkpoints):
	for checkpoint in checkpoints:
		gdb.execute(f"break *{checkpoint}")

def get_thread_creation_checkpoints():
	gdb.execute("catch syscall clone")
	syscall_recorder = SyscallRecorder()
	gdb.events.stop.connect(syscall_recorder)
	gdb.execute("run")
	gdb.execute("delete")
	gdb.events.stop.disconnect(syscall_recorder)
	return syscall_recorder.checkpoints

def set_thread_start_routine_breakpoints():
	start_routines = ["increment"]
	for start_routine in start_routines:
		gdb.Breakpoint(start_routine)

def pause_target_at_start():
	gdb.Breakpoint("main")
	gdb.execute("run")

def main():
	CHECKPOINT_TAG = "checkpoints"
	OUTPUT_FILE = "./checkpoints.json"
	OUTPUT_FILE_INDENT_WIDTH = 2

	thread_creation_checkpoints = get_thread_creation_checkpoints()
	pause_target_at_start()
	set_syscall_breakpoints(thread_creation_checkpoints)
	set_shared_variable_breakpoints()
	set_thread_start_routine_breakpoints()
	checkpoint_recorder = CheckpointRecorder(thread_creation_checkpoints)
	gdb.events.stop.connect(checkpoint_recorder)
	gdb.execute("continue")

	replay = {}
	replay[CHECKPOINT_TAG] = checkpoint_recorder.get_hit_checkpoints()

	with open(OUTPUT_FILE, "w+") as output_file:
		json.dump(replay, output_file, indent=OUTPUT_FILE_INDENT_WIDTH)

if __name__ == "__main__":
	main()
