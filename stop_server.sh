#!/bin/bash
PID=`ps -ef | grep python | grep main.py | awk '{print $2}'`
kill -15 $PID