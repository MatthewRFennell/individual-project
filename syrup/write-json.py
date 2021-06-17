#!/bin/python3

import gdb
import json
from pprint import pprint

START_ROUTINE_TAG = "thread_start_routines"
THREAD_ID_TAG = "thread"
CHECKPOINT_LOCATION_TAG = "location"
CHECKPOINT_ID_TAG = "id"
CHECKPOINT_ACTION_TAG = "action"
CHECKPOINT_ACTION_CREATOR_THREAD_TAG = "creator_thread"
CHECKPOINT_ACTION_CREATED_THREAD_TAG = "created_thread"
CHECKPOINT_ACTION_UNTRACKED_TAG = ""
MAIN_THREAD_ID = 1

class ThreadCreationListener:
	def __init__(self):
		self._created_threads = set([MAIN_THREAD_ID])
		self._is_constrained_execution = False
		self._thread_creations = []

	def __call__(self, event):
		newly_created_thread = self._newly_created_thread()
		self._record_new_thread_creation(event.inferior_thread.num,
				newly_created_thread)
		self._handle_newly_created_thread(newly_created_thread)
		self._constrain_execution_to_thread(newly_created_thread)
		self._run_thread_to_start_routine(newly_created_thread)
		self._resume_unconstrained_execution()

	def get_thread_creations(self):
		return self._thread_creations

	def _record_new_thread_creation(self, creator_thread, created_thread):
		self._thread_creations.append({
				"creator_thread": creator_thread,
				"created_thread": created_thread
		})

	def _run_thread_to_start_routine(self, thread):
		gdb.execute("continue")

	def _newly_created_thread(self):
		alive_threads = set(map(lambda thread: thread.global_num,
				gdb.inferiors()[0].threads()))
		newly_created_threads = alive_threads.difference(self._created_threads)
		assert len(newly_created_threads) == 1, "More than one newly created thread"
		return next(iter(newly_created_threads))

	def _handle_newly_created_thread(self, thread_id):
		self._created_threads.add(thread_id)

	def _constrain_execution_to_thread(self, thread_id):
		gdb.execute("set scheduler-locking on")
		gdb.execute(f"thread {thread_id}")
		self._is_constrained_execution = True

	def _resume_unconstrained_execution(self):
		self._is_constrained_execution = False
		gdb.execute("set scheduler-locking off")

class SyscallRecorder:
	def __init__(self):
		self.checkpoints = set()

	def __call__(self, event):
		self.checkpoints.add(hex(gdb.selected_frame().older().pc()))
		gdb.execute("continue")

# This class records the order in which checkpoints are hit when the program
# executes. A checkpoint is an assembly instruction which reads from or writes
# to a variable that is shared between threads.
class CheckpointRecorder:
	def __init__(self, thread_creation_checkpoints):
		self._thread_creation_checkpoints = thread_creation_checkpoints
		self.hit_checkpoints = []
		self._checkpoint_id = 0

	def __call__(self, event):
		self._record_hit_checkpoint()
		gdb.execute("continue")

	def _record_hit_checkpoint(self):
		thread_id = gdb.selected_thread().num
		checkpoint_location = hex(gdb.selected_frame().pc())
		self._add_checkpoint(thread_id, checkpoint_location, self._checkpoint_id)
		self._checkpoint_id += 1

	def _add_checkpoint(self, thread_id, checkpoint_location, checkpoint_id):
		self.hit_checkpoints.append({
				CHECKPOINT_ID_TAG: checkpoint_id,
				THREAD_ID_TAG: thread_id,
				CHECKPOINT_LOCATION_TAG: checkpoint_location
		})

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

class CheckpointMatcher:
	def __init__(self, checkpoints, thread_creations,
			thread_creation_checkpoints):
		self._checkpoints = checkpoints
		self._thread_creations = thread_creations
		self._thread_creation_checkpoints = thread_creation_checkpoints
		self._unmatched_created_thread_checkpoint_ids = []
		self._unmatched_creator_thread_checkpoint_ids = []
		self._seen_threads = set([MAIN_THREAD_ID])
		self._required_reorderings = set()

	def checkpoints_with_correctly_ordered_thread_creations(self):
		return self._associated_checkpoints()

	def _associated_checkpoints(self):
		main_thread_id = 1
		seen_threads = set([main_thread_id])
		for checkpoint in self._checkpoints:
			self._handle_checkpoint(checkpoint)
		assert len(self._unmatched_creator_thread_checkpoint_ids) == 0, \
				"Unmatched creator threads remain after matching"
		assert len(self._unmatched_created_thread_checkpoint_ids) == 0, \
				"Unmatched created threads remain after matching"
		return self._reordered_checkpoints()

	def _reordered_checkpoints(self):
		for reordering in self._required_reorderings:
			self._apply_reordering(reordering)
		return self._checkpoints

	def _apply_reordering(self, reordering):
		checkpoint_to_move_id = reordering[0]
		checkpoint_to_move_to_id = reordering[1]
		checkpoint_to_move_index = \
				self._get_checkpoint_index_by_id(checkpoint_to_move_id)
		checkpoint_to_move_to_index = \
				self._get_checkpoint_index_by_id(checkpoint_to_move_to_id)
		self._move(checkpoint_to_move_index, checkpoint_to_move_to_index)

	def _move(self, index_to_move_from, index_to_move_to):
		checkpoint_to_move = self._checkpoints[index_to_move_from]
		self._checkpoints.pop(index_to_move_from)
		self._checkpoints.insert(index_to_move_to, checkpoint_to_move)

	def _get_checkpoint_index_by_id(self, checkpoint_id):
		return self._checkpoints.index(next(filter(lambda checkpoint: \
				checkpoint[CHECKPOINT_ID_TAG] == checkpoint_id, self._checkpoints)))

	def _handle_checkpoint(self, checkpoint):
		if checkpoint[THREAD_ID_TAG] not in self._seen_threads:
			self._handle_created_thread(checkpoint)
		elif checkpoint[CHECKPOINT_LOCATION_TAG] in \
				self._thread_creation_checkpoints:
			self._handle_creator_thread(checkpoint)
		self._attempt_to_match()

	def _handle_creator_thread(self, checkpoint):
		checkpoint[CHECKPOINT_ACTION_TAG] = CHECKPOINT_ACTION_CREATOR_THREAD_TAG
		self._unmatched_creator_thread_checkpoint_ids.append(checkpoint)

	def _handle_created_thread(self, checkpoint):
		checkpoint[CHECKPOINT_ACTION_TAG] = CHECKPOINT_ACTION_CREATED_THREAD_TAG
		self._unmatched_created_thread_checkpoint_ids.append(checkpoint)
		self._seen_threads.add(checkpoint[THREAD_ID_TAG])

	def _attempt_to_match(self):
		for checkpoint in self._unmatched_creator_thread_checkpoint_ids:
			next_thread_creation = \
					self._next_thread_creation_by_thread(checkpoint[THREAD_ID_TAG])
			match = self._matching_checkpoint(next_thread_creation["created_thread"])
			if match != None and not self._is_correct_order(checkpoint, match):
				self._add_reorder(checkpoint[CHECKPOINT_ID_TAG],
						match[CHECKPOINT_ID_TAG])
			if match != None:
				self._remove_checkpoints_for_reordering(checkpoint[CHECKPOINT_ID_TAG],
						match[CHECKPOINT_ID_TAG])
				self._remove_thread_creation(checkpoint[THREAD_ID_TAG],
						match[THREAD_ID_TAG])
				return

	def _is_correct_order(self, potential_creator_checkpoint,
			potential_created_checkpoint):
		return potential_creator_checkpoint[CHECKPOINT_ID_TAG] < \
				potential_created_checkpoint[CHECKPOINT_ID_TAG]

	def _remove_thread_creation(self, creator_thread_checkpoint_id,
			created_thread_checkpoint_id):
		thread_creation_to_remove = ({
				"creator_thread": creator_thread_checkpoint_id,
				"created_thread": created_thread_checkpoint_id
		})
		self._thread_creations.remove(thread_creation_to_remove)

	def _remove_checkpoints_for_reordering(self, creator_thread_checkpoint_id,
			created_thread_checkpoint_id):
		self._unmatched_creator_thread_checkpoint_ids = \
				self._remove_checkpoint_with_id(
						self._unmatched_creator_thread_checkpoint_ids,
						creator_thread_checkpoint_id
				)
		self._unmatched_created_thread_checkpoint_ids = \
				self._remove_checkpoint_with_id(
						self._unmatched_created_thread_checkpoint_ids,
						created_thread_checkpoint_id
				)

	def _remove_checkpoint_with_id(self, checkpoint_list, checkpoint_id):
		return list(filter(lambda checkpoint: \
				checkpoint[CHECKPOINT_ID_TAG] != checkpoint_id, checkpoint_list))

	def _add_reorder(self, creator_thread_checkpoint_id,
			created_thread_checkpoint_id):
		self._required_reorderings.add((
				creator_thread_checkpoint_id,
				created_thread_checkpoint_id
		))

	def _matching_checkpoint(self, thread_id):
		matched_checkpoint = next(filter(lambda checkpoint: \
				checkpoint[THREAD_ID_TAG] == thread_id,
				self._unmatched_created_thread_checkpoint_ids), None)
		return matched_checkpoint

	def _next_thread_creation_by_thread(self, thread_id):
		return next(filter(lambda thread_creation:
				thread_creation["creator_thread"] == thread_id, self._thread_creations))

def get_start_routines():
	return ["increment"]

def configure_gdb_to_run_as_a_script():
	gdb.execute("set pagination off")
	gdb.execute("set confirm off")

def main():
	CHECKPOINT_TAG = "checkpoints"
	OUTPUT_FILE = "./checkpoints.json"
	OUTPUT_FILE_INDENT_WIDTH = 2

	thread_creation_checkpoints = get_thread_creation_checkpoints()
	configure_gdb_to_run_as_a_script()
	pause_target_at_start()
	set_syscall_breakpoints(thread_creation_checkpoints)
	set_shared_variable_breakpoints()
	set_thread_start_routine_breakpoints()
	checkpoint_recorder = CheckpointRecorder(thread_creation_checkpoints)
	gdb.events.stop.connect(checkpoint_recorder)
	thread_creation_listener = ThreadCreationListener()
	gdb.events.new_thread.connect(thread_creation_listener)
	gdb.execute("continue")

	replay = {}
	checkpoint_matcher = CheckpointMatcher(
			checkpoint_recorder.get_hit_checkpoints(),
			thread_creation_listener.get_thread_creations(),
			thread_creation_checkpoints
	)

	checkpoints = \
			checkpoint_matcher.checkpoints_with_correctly_ordered_thread_creations()
	replay[CHECKPOINT_TAG] = checkpoints

	start_routines = get_start_routines()
	replay[START_ROUTINE_TAG] = start_routines

	for checkpoint in checkpoints:
		checkpoint[CHECKPOINT_LOCATION_TAG] = \
				"*" + checkpoint[CHECKPOINT_LOCATION_TAG]

	for checkpoint in checkpoints:
		if CHECKPOINT_ACTION_TAG not in checkpoint:
			checkpoint[CHECKPOINT_ACTION_TAG] = CHECKPOINT_ACTION_UNTRACKED_TAG

	with open(OUTPUT_FILE, "w+") as output_file:
		json.dump(replay, output_file, indent=OUTPUT_FILE_INDENT_WIDTH)

	gdb.execute("quit")

if __name__ == "__main__":
	main()
