#!/bin/python3

import gdb
import json

def thread_switches():
	with open("./checkpoints.json") as checkpoint_file:
		checkpoints = json.load(checkpoint_file)["checkpoints"]
		instructions = []
		for checkpoint in checkpoints:
			gdb.execute(f"thread {checkpoint['thread']}")
			gdb.execute(f"tbreak *{checkpoint['hits']} thread {checkpoint['thread']}")
			gdb.execute("continue")

entry_breakpoint = gdb.Breakpoint("main")
gdb.execute("run")
gdb.execute("set scheduler-locking on")

print("CARRYING OUT JSON SWITCHES")
thread_switches()
