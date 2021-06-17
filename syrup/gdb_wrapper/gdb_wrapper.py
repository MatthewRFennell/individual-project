#!/bin/python3
import gdb
import inspect
from logger.logger import log

# Breakpoints
class Breakpoint:
	def __init__(self, breakpoint_location, thread, is_temporary, breakpoint_type, wp_class):
		self._breakpoint_location = breakpoint_location
		self._thread = thread
		self._is_temporary = is_temporary
		self._breakpoint_type = breakpoint_type
		self._wp_class = wp_class

	def __call__(self):
		log(f"Creating a new breakpoint for thread {self._thread} at {self._breakpoint_location}")
		print_stack_depth()
		if self._breakpoint_type is None and self._wp_class is None:
			breakpoint = gdb.Breakpoint(self._breakpoint_location, temporary=self._is_temporary)
		else:
			breakpoint = gdb.Breakpoint(
				self._breakpoint_location,
				self._breakpoint_type,
				self._wp_class,
				temporary=self._is_temporary
			)
		if self._thread is not None:
			breakpoint.thread = self._thread

	def __str__(self):
		return f"Breakpoint for thread {self._thread} at {self._breakpoint_location}"

def immediate_breakpoint_at(
		location,
		thread=None,
		is_temporary=False,
		breakpoint_type=None,
		wp_class=None):
	Breakpoint(location, thread, is_temporary, breakpoint_type, wp_class)()

def enqueue_breakpoint_at(
		location,
		thread=None,
		is_temporary=False,
		breakpoint_type=None,
		wp_class=None):
	post_event(Breakpoint(location, thread, is_temporary, breakpoint_type, wp_class))

# Instructions
class Instruction:
	def __init__(self, instruction):
		self._instruction = instruction

	def __call__(self):
		log(f"{self._instruction}")
		print_stack_depth()
		gdb.execute(self._instruction)

	def __str__(self):
		return f"{self._instruction}"

def immediate_execute(instruction):
	Instruction(instruction)()

def enqueue_execute(instruction):
	post_event(Instruction(instruction))

# Connections
class Connection:
	def __init__(self, event_registry, event_listener):
		self._event_registry = event_registry
		self._event_listener = event_listener

	def __call__(self):
		log(f"Connecting {self._event_listener} to {self._event_registry}")
		print_stack_depth()
		self._event_registry.connect(self._event_listener)

	def __str__(self):
		return f"Connection of {self._event_listener} to {self._event_registry}"

def immediate_connect(event_registry, event_listener):
	Connection(event_registry, event_listener)()

def enqueue_connect(event_registry, event_listener):
	post_event(Connection(event_registry, event_listener))

# Disconnects
class Disconnect:
	def __init__(self, event_registry, event_listener):
		self._event_registry = event_registry
		self._event_listener = event_listener

	def __call__(self):
		log(f"Disconnecting {self._event_listener} from {self._event_registry}")
		print_stack_depth()
		self._event_registry.disconnect(self._event_listener)

	def __str__(self):
		return f"Disconnection of {self._event_listener} from {self._event_registry}"

def immediate_disconnect(event_registry, event_listener):
	Disconnect(event_registry, event_listener)()

def enqueue_disconnect(event_registry, event_listener):
	post_event(Disconnect(event_registry, event_listener))

# Convenience functions
def post_event(action):
	log(f"Posting {action} to the event queue")
	print_stack_depth()
	result = gdb.post_event(action)

def print_stack_depth():
	stack_depth = len(inspect.stack())
	if stack_depth > 10:
		log(f"stack depth: {len(inspect.stack())}")
