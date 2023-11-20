#!/bin/bash

# Run the script to fix config file
result=$(python3 ./autoFix.py "$1")
res=$?
# If return code is 0, send result of runed the command to zabbix server.
if [ $res = 0 ]; then
    zabbix_sender -z 192.168.3.26 -p 10051 -s "test01" -k zabbixTrapper -o "$result"
# If return code is not 0, send error message to zabbix server.
else
    zabbix_sender -z 192.168.3.26 -p 10051 -s "test01" -k zabbixTrapper -o "Error runed script."
fi