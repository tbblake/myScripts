#!/bin/bash
# Download new marked.min.js
D=$(dirname $0)
cd $D
echo Before:
./versions.sh
echo
echo mv marked.min.js marked.min.js.bk.$(date +%Y%m%d-%H%M%S) | bash -x
echo
echo curl -LO https://cdn.jsdelivr.net/npm/marked/marked.min.js | bash -x
echo
echo After:
./versions.sh
echo
echo Re-checking in Zabbix:
/root/scripts/checkItem.py -n -i 39397 -i 39393
