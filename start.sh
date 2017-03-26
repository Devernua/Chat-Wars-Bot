#!/bin/sh
for i in `seq 1338 1348`;
do
	python3 main.py --admin devernua --order BlueOysterBot --port $i > /dev/null &
done
