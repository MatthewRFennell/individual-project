#!/bin/python3

import gdb
import json
import collections
from pprint import pprint

# Functions + classes
class BreakListener:
	def __call__(self, event):
		print("STATUS BEFORE")
		pprint(breakpoints)
		pprint(breakpoints_by_thread())
		set_newly_created_thread_breakpoints()
		print("LIST ALL BREAKPOINT THREADS:")
		current_thread = breakpoints[0]["thread"]
		breakpoints_to_consider = set(filter(lambda breakpoint: breakpoint.thread == current_thread, event.breakpoints))
		print("BREAKPOINTS TO CONSIDER:=====")
		print(breakpoints_to_consider)
		for breakpoint in breakpoints_to_consider:
			if breakpoint_corresponds_to_checkpoint(breakpoint, breakpoints[0]):
				set_next_breakpoint()
		print("STATUS AFTER")
		pprint(breakpoints)
		pprint(breakpoints_by_thread())
		if current_thread not in breakpoints_by_thread().keys():
			print(f"REACHED THE END OF THREAD {current_thread}, FINISHING")
			gdb.execute("continue")
		if len(breakpoints) > 0:
			next_thread_to_switch_to = breakpoints[0]["thread"]
			print(f"SWITCHING TO THREAD {next_thread_to_switch_to}")
			gdb.execute(f"thread {next_thread_to_switch_to}")
			gdb.execute("continue")

def set_next_breakpoint():
	thread = breakpoints.popleft()["thread"]
	print(f"INSIDE SET NEXT BREAKPOINT - THREAD {thread} HIT")
	if thread in breakpoints_by_thread().keys():
		print(f"THREAD {thread} HAS AT LEAST ONE BREAKPOINT LEFT")
		breakpoints_by_thread()[thread].popleft()
		next_checkpoint = breakpoints_by_thread()[thread][0]
		next_breakpoint = gdb.Breakpoint(next_checkpoint, temporary=True)
		next_breakpoint.thread = thread

def breakpoint_corresponds_to_checkpoint(gdb_breakpoint, checkpoint):
	print("TESTING BREAKPOINT FOR EQUALITY")
	print(gdb_breakpoint.location)
	print(checkpoint["hits"])
	print(gdb_breakpoint.thread)
	print(checkpoint["thread"])
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

def breakpoint_thread_entry_points(entry_points):
	for entry_point in entry_points:
		breakpoint = gdb.Breakpoint(entry_point)

# Main
threads = collections.deque([{}] * 2, 2)
breakpoints = collections.deque()
entry_breakpoint = gdb.Breakpoint("main")
gdb.execute("run")
gdb.execute("set scheduler-locking on")
listener = BreakListener()
gdb.events.stop.connect(listener)

with open("./checkpoints.json") as checkpoint_file:
	information = json.load(checkpoint_file)
	entry_points = information["entry_points"]
	breakpoint_thread_entry_points(entry_points)
	checkpoints = information["checkpoints"]
	initialise_breakpoints(checkpoints)
	set_newly_created_thread_breakpoints()
	gdb.execute("continue")

# TODO add a checkpoint at the end of each thread, or a special case when there
# are no more instructions left in that thread's queue
