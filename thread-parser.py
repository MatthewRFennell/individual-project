#!/bin/python3
import json

def setup():
	return """break main
run
set scheduler-locking on"""

def entry_routines():
	return """break increment
commands
thread 1
continue
end"""

def thread_switches():
	with open("./test.json") as thread_switch_file:
		thread_switches = json.load(thread_switch_file)["thread_switches"]
		instructions = []
		for thread_switch in thread_switches:
			if thread_switch["at"] == "end":
				instructions.append("""finish
finish""")
			else:
				instructions.append(f"tbreak *{thread_switch['at']}")
				instructions.append(f"continue")
			instructions.append(f"thread {thread_switch['to_thread']}")
		return "\n".join(instructions)

def finish():
	return """continue"""

def print_full_instructions():
	print(setup())
	print(entry_routines())
	print(thread_switches())
	print(finish())

print_full_instructions()
