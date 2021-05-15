#!/bin/python3

import gdb
import json
from pprint import pprint

def execute_program_following(checkpoints):
	current_threads = set(map(lambda thread: thread.global_num, gdb.inferiors()[0].threads()))


def breakpoint_thread_entry_points(entry_points):
	for entry_point in entry_points:
		gdb.Breakpoint(entry_point)

entry_breakpoint = gdb.Breakpoint("main")
gdb.execute("run")
gdb.execute("set scheduler-locking on")

with open("./checkpoints.json") as checkpoint_file:
	information = json.load(checkpoint_file)
	entry_points = information["entry_points"]
	breakpoint_thread_entry_points(entry_points)
	checkpoints = information["checkpoints"]
	execute_program_following(checkpoints)
