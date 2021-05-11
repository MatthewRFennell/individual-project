#!/bin/python3

import gdb
from pprint import pprint
from enum import Enum

class BreakListener:
	def __init__(self, thread_hit_list):
		self.hit_breakpoints = thread_hit_list

	def __call__(self, event):
		#pprint(dir(event.breakpoints[0]))
		print("HELLO")
		print(event.breakpoints[0].type)
		self.hit_breakpoints += tuple([gdb.selected_thread().num, hex(gdb.selected_frame().pc())])
		gdb.execute("continue")

hit_breakpoints = []

counter = gdb.Breakpoint("counter", gdb.BP_WATCHPOINT, gdb.WP_ACCESS)
pthread_create = gdb.Breakpoint("pthread_create", gdb.BP_BREAKPOINT)
pthread_join = gdb.Breakpoint("pthread_join", gdb.BP_BREAKPOINT)
listener = BreakListener(hit_breakpoints)
gdb.events.stop.connect(listener)
gdb.execute("run")
print(hit_breakpoints)
