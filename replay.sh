#!/bin/bash
../gdb-build/bin/gdb ./examples/counter-2-threads/a.out -x syrup/read-json.py > replay.log 2>&1 && cat execution.log
