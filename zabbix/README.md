# Zabbix
Scripts to use with [Zabbix](https://www.zabbix.com)

houseKeeperLogParser.html -- A javascript housekeeper log parser.  Paste your zabbix_server.log in here to parse out the useful stats from the housekeeper.  Support for 4.0, 6.0, and 6.4.

checkHost.py -- Submit tasks for Zabbix to check one or mote items on one or more hosts

problems.py -- lists problems, options to ack, add message, and close

unsupportedItems.py -- lists all unsupported items


All .py scripts requite a .zbx.env file in the directory with the script, formatted like the below with an authID and apiURL parameter.  The authID can be obtained using the user.login API call or via User settings --> API tokens in the web UI.

```
authID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
apiURL=https://zabbix.host.com/api_jsonrpc.php
```
