#!/bin/bash
nohup python3 main.py 1>/dev/null 2>&1 &
ps -ef | grep python | grep main