#!/bin/bash
now=$(date +"%T")
SERVICE="python3"

sudo /usr/bin/python3 /home/pi/NewDot/test.py
ip_wlan0=$(ip addr show wlan0|grep link/ether|grep -v inet6|awk '{print $2}'|awk '{split($0,a,"/"); print a[1]}')
serial_port="/dev/ttyS0"
sudo /usr/bin/python3 /home/pi/NewDot/serialClient_final.py $serial_port &
sudo /usr/bin/python3 /home/pi/BDotAI/src/algtest_noRaw.py $ip_wlan0

# shell script will not execute the next command unless it finishes the current one, that's why we use "&" to let them run together. 


if pgrep -x "$SERVICE" >/dev/null
then
    echo "$SERVICE is running at $now" > /home/pi/NewDot/log.txt
else
    echo "$SERVICE stopped at $now" > /home/pi/NewDot/log.txt
    #nohup sudo /usr/bin/python3 /home/pi/NewDot/serialClient_final.py /dev/ttyS0 > /home/pi/NewDot/log.txt &

fi
