#!/bin/sh


kill $(pgrep -f 'liveDCReader.py')
sleep 1


kill $(pgrep -f 'liveLNReader.py')
sleep 1


