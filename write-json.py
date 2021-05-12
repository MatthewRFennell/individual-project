#!/bin/python3

import gdb
import json
import sys
from pprint import pprint
from enum import Enum

class BreakListener:
	def __init__(self, thread_hit_list):
		self.hit_breakpoints = thread_hit_list

	def __call__(self, event):
		if event.breakpoints[0].type == 9:
			frame = gdb.selected_frame()
		else:
			frame = gdb.selected_frame().older()
		self.hit_breakpoints.append({"thread": gdb.selected_thread().num, "hits": hex(frame.pc())})
		gdb.execute("continue")

hit_breakpoints = {}
hit_breakpoints["checkpoints"] = []

counter = gdb.Breakpoint("counter", gdb.BP_WATCHPOINT, gdb.WP_ACCESS)
pthread_create = gdb.Breakpoint("pthread_create", gdb.BP_BREAKPOINT)
pthread_join = gdb.Breakpoint("pthread_join", gdb.BP_BREAKPOINT)
increment = gdb.Breakpoint("increment", gdb.BP_BREAKPOINT)
listener = BreakListener(hit_breakpoints["checkpoints"])
gdb.events.stop.connect(listener)
gdb.execute("run")
with open("checkpoints.json", "w+") as thread_switch_file:
	json.dump(hit_breakpoints, thread_switch_file, indent=2)
