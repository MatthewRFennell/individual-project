#!/bin/python3

import gdb
import json
import collections
from pprint import pprint
from .checkpoint_parser import checkpoint_parser

THREADS_TO_COMPARE_COUNT = 2

thread_breakpoints_have_been_hit = {1: True, 2: False, 3: False}

class ThreadManager:
	pass

class BreakpointManager:
	pass

# Functions + classes
class BreakListener:
	def __call__(self, event):
		record_if_initial_breapoint_has_been_hit(event.breakpoints)
		set_newly_created_thread_breakpoints()
		current_thread = breakpoints[0]["thread"]
		breakpoints_to_consider = set(filter(lambda breakpoint: \
				breakpoint.thread == current_thread, event.breakpoints))
		for breakpoint in breakpoints_to_consider:
			if breakpoint_corresponds_to_checkpoint(breakpoint, breakpoints[0]):
				set_next_breakpoint()
		if current_thread not in breakpoints_by_thread().keys():
			gdb.execute("continue")
		if len(breakpoints) > 0:
			next_thread_to_switch_to = breakpoints[0]["thread"]
			gdb.execute(f"thread {next_thread_to_switch_to}")
			gdb.execute("continue")
		gdb.execute("info threads")

def record_if_initial_breapoint_has_been_hit(breakpoints):
	for breakpoint in breakpoints:
		if breakpoint.location in entry_points:
			thread_breakpoints_have_been_hit[gdb.selected_thread().global_num] = True

def reach_thread_starting_point(thread_id):
	if thread_breakpoints_have_been_hit[thread_id]:
		return
	current_thread = gdb.selected_thread()
	gdb.execute(f"thread {thread_id}")
	gdb.execute("continue")
	gdb.execute(f"thread {current_thread}")

def set_next_breakpoint():
	thread = breakpoints.popleft()["thread"]
	if thread in breakpoints_by_thread().keys():
		breakpoints_by_thread()[thread].popleft()
		next_checkpoint = breakpoints_by_thread()[thread][0]
		next_breakpoint = gdb.Breakpoint(next_checkpoint, temporary=True)
		next_breakpoint.thread = thread

def breakpoint_corresponds_to_checkpoint(gdb_breakpoint, checkpoint):
	return gdb_breakpoint.location == checkpoint["hits"] and \
			gdb_breakpoint.thread == checkpoint["thread"]

def breakpoints_by_thread():
	threads = set()
	for checkpoint in breakpoints:
		threads.add(checkpoint["thread"])
	breakpoints_by_thread = {}
	for thread in threads:
		breakpoints_by_thread[thread] = collections.deque()
	for checkpoint in breakpoints:
		breakpoints_by_thread[checkpoint["thread"]].append(checkpoint["hits"])
	return breakpoints_by_thread

def initialise_breakpoints(checkpoints):
	for checkpoint in checkpoints:
		breakpoints.append(checkpoint)

def set_newly_created_thread_breakpoints():
	threads.appendleft(
			set(map(lambda thread: thread.global_num, gdb.inferiors()[0].threads())))
	newly_created_threads = threads[0].difference(threads[1])
	for thread in newly_created_threads:
		next_breakpoint = breakpoints_by_thread()[thread][0]
		thread_first_breakpoint = gdb.Breakpoint(next_breakpoint, temporary=True)
		thread_first_breakpoint.thread = thread
		reach_thread_starting_point(thread)

def breakpoint_thread_entry_points(entry_points):
	for entry_point in entry_points:
		breakpoint = gdb.Breakpoint(entry_point)

def main():
	parser = checkpoint_parser("./checkpoints.json")
	entry_points = parser.get_entry_points()
	checkpoints = parser.get_checkpoints()
	pprint(entry_points)
	pprint(checkpoints)

if __name__ == "__main__":
	main()

## Shared between set_newly_created_thread_breakpoints and BreakListener
#threads = collections.deque([{}] * 2, 2)
## Shared between BreakListener, set_next_breakpoint, breakpoints_by_thread and initialise_breakpoints
#breakpoints = collections.deque()
#entry_breakpoint = gdb.Breakpoint("main")
#gdb.execute("run")
#gdb.execute("set scheduler-locking on")
## Shared in record_if_initial_breapoint_has_been_hit, which is called from BreakListener
#entry_points = {}
#listener = BreakListener()
#gdb.events.stop.connect(listener)
#with open("./checkpoints.json") as checkpoint_file:
#	information = json.load(checkpoint_file)
#	entry_points = information["entry_points"]
#	breakpoint_thread_entry_points(entry_points)
#	checkpoints = information["checkpoints"]
#	initialise_breakpoints(checkpoints)
#	set_newly_created_thread_breakpoints()
#	gdb.execute("continue")

#	with open("./checkpoints.json") as checkpoint_file:
#		information = json.load(checkpoint_file)
#		entry_points = information["entry_points"]
#		breakpoint_thread_entry_points(entry_points)
#		checkpoints = information["checkpoints"]
#		initialise_breakpoints(checkpoints)
#		set_newly_created_thread_breakpoints()
#		gdb.execute("continue")
