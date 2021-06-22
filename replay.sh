#!/bin/bash
gdb ./examples/counter-2-threads/a.out -x syrup/read-json.py > /dev/null 2>&1 && cat log.txt
