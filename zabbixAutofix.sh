#!/bin/bash

# Run the script to fix config file
result=$(python3 ./autoFix.py "$1")
res=$?
# If return code is 0, send result of runed the command to zabbix server.
if [ $res = 0 ]; then
    zabbix_sender -z <zabbix server ip> -p 10051 -s "<target hostname>" -k zabbixTrapper -o "$result"
# If return code is not 0, send error message to zabbix server.
else
    zabbix_sender -z <zabbix server ip> -p 10051 -s "<target hostname>" -k zabbixTrapper -o "Error runed script."
fi