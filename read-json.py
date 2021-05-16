#!/bin/python3

import gdb
import json
import collections
from pprint import pprint

class BreakListener:
	def __call__(self, event):
		set_newly_created_thread_breakpoints()
		if breakpoint_corresponds_to_checkpoint(event.breakpoint, breakpoints[0]):
			update_next_breakpoint()
		next_thread_to_switch_to = breakpoints[0]["thread"]
		gdb.execute(f"thread {next_thread_to_switch_to}")
		print(f"SWITCHING TO THREAD {next_thread_to_switch_to}, hoping to hit {breakpoints[0]}")
		gdb.execute("continue")

def set_next_breakpoint():
	thread = breakpoints.popleft()["thread"]
	if len(breakpoints_by_thread[thread]) > 0:
		breakpoints_by_thread[thread].popleft()
		next_checkpoint = breakpoints_by_thread[thread][0]
		next_breakpoint = gdb.Breakpoint(next_checkpoint, temporary=True)
		next_breakpoint.thread = thread

		print("==== HOUSEKEEPING - BEFORE: ====")
		pprint(breakpoints)
		pprint(breakpoints_by_thread[thread])

		breakpoints.popleft()
		breakpoints_by_thread[thread].popleft()

		print("==== HOUSEKEEPING - AFTER: ====")
		pprint(breakpoints)
		pprint(breakpoints_by_thread[thread])

def update_next_breakpoint():
	set_next_breakpoint()

def breakpoint_corresponds_to_checkpoint(gdb_breakpoint, checkpoint):
	print(gdb_breakpoint.location)
	print(checkpoint["hits"])
	print(gdb_breakpoint.thread)
	print(checkpoint["thread"])
	return gdb_breakpoint.location == checkpoint["hits"] and gdb_breakpoint.thread == checkpoint["thread"]

threads = collections.deque([{}] * 2, 2)
breakpoints = collections.deque()
breakpoints_by_thread = {}
next_breakpoint = {}

def initialise_breakpoints_by_thread(checkpoints):
	threads = set()
	for checkpoint in checkpoints:
		threads.add(checkpoint["thread"])
	for thread in threads:
		breakpoints_by_thread[thread] = collections.deque()
	for checkpoint in checkpoints:
		breakpoints_by_thread[checkpoint["thread"]].append(checkpoint["hits"])

def initialise_breakpoints(checkpoints):
	for checkpoint in checkpoints:
		breakpoints.append(checkpoint)

def set_breakpoints(checkpoints):
	initialise_breakpoints(checkpoints)
	initialise_breakpoints_by_thread(checkpoints)

def set_newly_created_thread_breakpoints():
	threads.appendleft(set(map(lambda thread: thread.global_num, gdb.inferiors()[0].threads())))
	newly_created_threads = threads[0].difference(threads[1])
	for thread in newly_created_threads:
		next_breakpoint = breakpoints_by_thread[thread][0]
		thread_first_breakpoint = gdb.Breakpoint(next_breakpoint, temporary=True)
		thread_first_breakpoint.thread = thread
		print(f"Added new breakpoint for {thread} at {next_breakpoint}")

def breakpoint_thread_entry_points(entry_points):
	for entry_point in entry_points:
		gdb.Breakpoint(entry_point)

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
	set_breakpoints(checkpoints)
	set_newly_created_thread_breakpoints()
	gdb.execute("continue")
