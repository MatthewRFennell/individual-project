#!/bin/python3

import gdb

entry_breakpoint = gdb.Breakpoint("main")
gdb.execute("run")
gdb.execute("set scheduler-locking on")

gdb.execute("break increment")
