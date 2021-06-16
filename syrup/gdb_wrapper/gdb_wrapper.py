#!/bin/python3
import gdb

# Breakpoints
class Breakpoint:
	def __init__(self, breakpoint_location, thread, is_temporary):
		self._breakpoint_location = breakpoint_location
		self._thread = thread
		self._is_temporary = is_temporary

	def __call__(self):
		print(f"Creating a new breakpoint for thread {self._thread} at {self._breakpoint_location}")
		breakpoint = gdb.Breakpoint(self._breakpoint_location, temporary=self._is_temporary)
		if self._thread is not None:
			breakpoint.thread = self._thread

def breakpoint_at(location, thread=None, is_temporary=False):
	Breakpoint(location, thread, is_temporary)()

def enqueue_breakpoint_at(location, thread=None, is_temporary=False):
	post_event(Breakpoint(location, thread, is_temporary))

# Instructions
class Instruction:
	def __init__(self, instruction):
		self._instruction = instruction

	def __call__(self):
		print(f"Executing {self._instruction}")
		gdb.execute(self._instruction)

def execute(instruction):
	Instruction(instruction)()

def enqueue_execute(instruction):
	post_event(Instruction(instruction))

# Connections
class Connection:
	def __init__(self, event_registry, event_listener):
		self._event_registry = event_registry
		self._event_listener = event_listener

	def __call__(self):
		print(f"Connecting {self._event_listener} to {self._event_registry}")
		self._event_registry.connect(self._event_listener)

def connect(event_registry, event_listener):
	Connection(event_registry, event_listener)()

def enqueue_connect(event_registry, event_listener):
	post_event(Connection(event_registry, event_listener))

# Convenience functions
def post_event(action):
	print(f"Posting {action} to the event queue")
	result = gdb.post_event(action)
