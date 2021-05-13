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
		frame = gdb.selected_frame()
		if event.breakpoint in thread_related_breakpoints:
			frame = gdb.selected_frame().older()
		thread_event = ""
		if event.breakpoint == pthread_create:
			thread_event = "pthread_create"
		elif event.breakpoint == pthread_join:
			thread_event = "pthread_join"
		self.hit_breakpoints.append({"thread": gdb.selected_thread().num, "hits": hex(frame.pc()), "thread_event": thread_event})
		gdb.execute("continue")

hit_breakpoints = {}
hit_breakpoints["checkpoints"] = []
thread_related_breakpoints = []

counter = gdb.Breakpoint("counter", gdb.BP_WATCHPOINT, gdb.WP_ACCESS)
pthread_create = gdb.Breakpoint("pthread_create", gdb.BP_BREAKPOINT)
pthread_join = gdb.Breakpoint("pthread_join", gdb.BP_BREAKPOINT)
thread_related_breakpoints.extend([pthread_create, pthread_join])
listener = BreakListener(hit_breakpoints["checkpoints"])
gdb.events.stop.connect(listener)
gdb.execute("run")
with open("checkpoints.json", "w+") as thread_switch_file:
	json.dump(hit_breakpoints, thread_switch_file, indent=2)
