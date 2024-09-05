#!/bin/sh

kill $(pgrep -f 'python3 liveDCReader.py')
sleep 1
python3 liveDCReader.py &

kill $(pgrep -f 'python3 liveLNReader.py')
sleep 1
python3 liveLNReader.py &


