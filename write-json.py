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
		if event.breakpoint not in entrypoint_breakpoints:
			frame = gdb.selected_frame()
			self.hit_breakpoints.append(
					{"thread": gdb.selected_thread().num, "hits": f"*{hex(frame.pc())}"})
		gdb.execute("continue")

hit_breakpoints = {}
hit_breakpoints["checkpoints"] = []
entrypoint_breakpoints = []

entry_point = gdb.Breakpoint("increment", gdb.BP_BREAKPOINT)
entrypoint_breakpoints = [entry_point]
hit_breakpoints["entry_points"] = list(
		set(map(lambda breakpoint: breakpoint.location, entrypoint_breakpoints)))
counter = gdb.Breakpoint("counter", gdb.BP_WATCHPOINT, gdb.WP_ACCESS)
listener = BreakListener(hit_breakpoints["checkpoints"])
gdb.events.stop.connect(listener)
gdb.execute("run")
modified_hit_breakpoints = []
if len(hit_breakpoints["checkpoints"]) == 1:
	modified_hit_breakpoints = hit_breakpoints["checkpoints"]
else:
	for i in range(len(hit_breakpoints["checkpoints"]) - 1):
		if hit_breakpoints["checkpoints"][i]["thread"] != \
				hit_breakpoints["checkpoints"][i + 1]["thread"]:
			modified_hit_breakpoints.append(hit_breakpoints["checkpoints"][i])
if len(hit_breakpoints["checkpoints"]) >= 2 and \
		hit_breakpoints["checkpoints"][-2]["thread"] != \
		hit_breakpoints["checkpoints"][-1]["thread"]:
	modified_hit_breakpoints.append(hit_breakpoints["checkpoints"][-1])
pprint(hit_breakpoints)
hit_breakpoints["checkpoints"] = modified_hit_breakpoints

with open("checkpoints.json", "w+") as thread_switch_file:
	json.dump(hit_breakpoints, thread_switch_file, indent=2)
