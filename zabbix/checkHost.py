#!/root/scripts/venv/bin/python3

# pip3 install \
#     requests==2.27.1 \
#     python-dotenv==0.20.0 \
#     rich==12.6.0

import argparse
import requests
import json
import sys
import dotenv
import traceback
import os

# suppress InsecureRequestWarning warning
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# https://www.zabbix.com/documentation/6.4/en/manual/api/reference/item/object
# https://www.zabbix.com/documentation/6.4/en/manual/api/reference/task/create
allowedItemTypes=["0","3","5","10","11","12","13","14","15","16","18","19","20"]

itemTypes={
	"0": "Zabbix agent",           #  0 - Allowed
	"1": "",                       #  1 - Undefined
	"2": "Zabbix trapper",         #  2 - Not allowed
	"3": "Simple check",           #  3 - Allowed
	"4": "",                       #  4 - Undefined
	"5": "Zabbix internal",        #  5 - Allowed
	"6": "",                       #  6 - Undefined
	"7": "Zabbix agent (active)",  #  7 - Not allowed
	"8": "",                       #  8 - Undefined
	"9": "Web item",               #  9 - Not allowed
	"10": "External check",        # 10 - Allowed
	"11": "Database monitor",      # 11 - Allowed
	"12": "IPMI agent",            # 12 - Allowed
	"13": "SSH agent",             # 13 - Allowed
	"14": "TELNET agent",          # 14 - Allowed
	"15": "Calculated",            # 15 - Allowed
	"16": "JMX agent",             # 16 - Allowed
	"17": "SNMP trap",             # 17 - Not allowed
	"18": "Dependent item",        # 18 - Allowed
	"19": "HTTP agent",            # 19 - Allowed
	"20": "SNMP agent",            # 20 - Allowed
	"21": "Script"                 # 21 - Not allowed
}

def main():
	parser = argparse.ArgumentParser(
		description='Submit tasks for zabbix processing',
		epilog=f"example: %(prog)s -s somehost.lan -k agent.ping -k 'icmpping[,,,]'")
	parser.add_argument('-s',dest='hosts',action='append',default=[],help='Host(s) to submit tasks for, one or more required, or -l option')
	parser.add_argument('-k',dest='items',action='append',default=[],help='Item key(s) to submit tasks for, multiple allowed')
	parser.add_argument('-l',dest='listall',action='store_true',default=False,help='List all available hosts and items, or restrict to hosts requested')
	parser.add_argument('-d',dest='dryrun',action='store_true',default=False,help='Dry run (don\'t send request to Zabbix)')

	# no args?  print help
	if len(sys.argv)==1:
		parser.print_help(sys.stdout)
		sys.exit()
	args = parser.parse_args()

	reqHosts=args.hosts
	reqItems=args.items
	dryRun=args.dryrun
	listAll=args.listall

	# Using the dotenv module, looking for authID and apiURL options within .zbx.env in the script directory.
	# e.g.
	# $ cat .zbx.env
	# authID=abcdefabcdefabcdefabcdefabcdefab
	# apiURL=http://myzabbix.local/zabbix/api_jsonrpc.php

	config = dotenv.dotenv_values(sys.path[0]+"/.zbx.env")
	if 'authID' not in config.keys():
		print(f'authID not in configuration file .zbx.env')
		sys.exit()
	if 'apiURL' not in config.keys():
		print(f'apiURL not in configuration file .zbx.env')
		sys.exit()

	authID=config['authID'] 
	apiURL=config['apiURL']

	if len(reqHosts) == 0 and not listAll:
		print('ERROR: At least one host required, or the list (-l) flag')
		parser.print_help(sys.stdout)
		sys.exit()

	# search zabbix for all requested hosts
	foundHosts=getHostByHost(hosts=reqHosts,url=apiURL,authID=authID)
	
	if listAll:
		if len(foundHosts) == 0:
			print(f"No matching hosts found")
			
		for host in foundHosts:
			hostName=host["host"]
			for item in host['items']+host['discoveries']:
				key=item["key_"]
				name=item["name"]
				type=itemTypes[item["type"]]
				itemOrLLDType=itemOrLLD(item)
				print(f'{hostName} - {itemOrLLDType} - {name} - {key} - {type}')
		sys.exit()
	
	# get back a list of item IDs we can submit tasks for
	taskItemIDs=getTaskItems(reqHosts=reqHosts,reqItems=reqItems,foundHosts=foundHosts)

	# no hosts/items matching what was requested
	if len(taskItemIDs) == 0:
		print(f"No matching hosts and/or allowable items found")
		sys.exit()
		
	# build our request object
	params=[]
	for itemID in taskItemIDs:
		params.append({"type": "6","request": {"itemid":itemID}})
	apiReq= { "jsonrpc": "2.0",
		"method": "task.create",
		"params": params,
		"auth": authID,
		"id": 1
	}
	# send it to Zabbix, print out task IDs
	if dryRun:
		print(f'!!!! dry run set, not sending request !!!!')
		sys.exit()
	apiRes=sendZabbixRequest(req=apiReq,url=apiURL)
	print('Tasks(s) submitted: ',end='')
	print(f'{apiRes["result"]["taskids"][0]}',end='')
	if len(apiRes["result"]["taskids"]) > 1:
		for taskID in apiRes["result"]["taskids"][1:]:
			print(f',{taskID}',end='')
	print()

# search for hosts by name, return found hosts, item information, and LLD information
def getHostByHost(*,hosts,url,authID):
	apiReq={
		"jsonrpc": "2.0",
		"method": "host.get",
		"params": {
			"output": [
				"host",
				"status"
			],
			"selectItems": [
				"master_itemid",
				"itemid",
				"key_",
				"name",
				"status",
				"type"
			],
			"selectDiscoveries": [
				"master_itemid",
				"itemid",
				"key_",
				"name",
				"status",
				"type",
				"discover"
			],
			"filter": {
				"host": hosts
			}
		},
		"auth": authID,
		"id": 1
	}

	apiRes=sendZabbixRequest(req=apiReq,url=url)
	return apiRes["result"]

# pass in a list of requested hosts, requested items, and found hosts, get back
# a list of item ids we can submit tasks for
def getTaskItems(*,reqHosts,reqItems,foundHosts):
	taskItems=[]
	foundHostsByHost={h["host"]:h for h in foundHosts} # dict indexed by host
	for host in reqHosts: # loop through hosts requested on the command line
		if host not in foundHostsByHost.keys(): # host does not exist in Zabbix
			print(f'{host} - does not exist in Zabbix')
		elif foundHostsByHost[host]["status"] != "0": # host is not enabled
			print(f'{host} - not enabled (status "{foundHostsByHost[host]["status"]}")')
		else: # host is in Zabbix and enabled, let's iterate through keys
			allHostItems=foundHostsByHost[host]["items"]+foundHostsByHost[host]["discoveries"] # list of all items on the current host
			if len(reqItems) == 0: # requested items is empty, make searchItems the host's whole list of items
				searchItems=list((x["key_"] for x in allHostItems)) # list of all keys on the host
			else:
				searchItems=reqItems

			for item in searchItems:
				itemID,message=validateItem(host=host,item=item,foundItems=allHostItems,taskItems=taskItems)
				print(message)
				if itemID:
					taskItems.append(itemID)

	return taskItems

# pass in a hostname, item key, a list of available items, and a list of already found itemids
# return an itemID & message if the item is valid for submission or False if not & message
def validateItem(*,host,item,foundItems,taskItems): # item key to look for, all items we're searching, and list of taskItems we've already found
	hostReturnStr=f'{host} - '
	foundItemsByKey={it["key_"]:it for it in foundItems} # all keys on the host, indexed by key_
	foundItemsById={it["itemid"]:it for it in foundItems}# all keys on the host, indexed by itemid
	
	if item not in foundItemsByKey.keys(): # item does not exist in this host, return False
		return False,f'{hostReturnStr}item {item} does not exist'
	
	# item exists on the host, extract some details about it
	itemOrLLDType=itemOrLLD(foundItemsByKey[item])
	itemId=foundItemsByKey[item]["itemid"]
	masterItemId=foundItemsByKey[item]["master_itemid"]	
	itemStatus=foundItemsByKey[item]["status"]
	itemType=foundItemsByKey[item]["type"]
	itemTypeText=itemTypes[itemType]
	if masterItemId != "0": # item is a dependent item, let's get some master item details
		printMasterItemKey=foundItemsById[masterItemId]["key_"]
		masterItemOrLLDType=itemOrLLD(foundItemsById[masterItemId])
		masterItemType=foundItemsById[masterItemId]["type"]
		masterItemTypeText=itemTypes[masterItemType]
		masterItemStatus=foundItemsById[masterItemId]["status"]

	# item exists on this host, but is not enabled, return False
	if itemStatus != "0": # item is not enabled
		return False,f'{hostReturnStr}{itemOrLLDType} {item} not submitted (item disabled)'
	
	# item is enabled, but item type is not allowed, return False
	if itemType not in allowedItemTypes: # item type not allowed
		return False,f'{hostReturnStr}{itemOrLLDType} {item} not submitted (type {itemTypeText})'

	# item type allowed
	if masterItemId != "0": # it's a dependent item, need to check it's master item, return failures or success

		if masterItemStatus != "0": # master item is not enabled
			return False,f'{hostReturnStr}{itemOrLLDType} {item} not submitted due to master {masterItemOrLLDType} {printMasterItemKey} (master item disabled)'

		if masterItemType not in allowedItemTypes: # master item type not allowed, return False
			return False,f'{hostReturnStr}{itemOrLLDType} {item} not submitted due to master {masterItemOrLLDType} {printMasterItemKey} (type {masterItemTypeText})'

		if masterItemId in taskItems: # master item is already in list
			return False,f'{hostReturnStr}{itemOrLLDType} {item} master {masterItemOrLLDType} {printMasterItemKey} already submitted'

		# master item id not in list and allowed, return master item id
		return masterItemId,f'{hostReturnStr}{itemOrLLDType} {item} master {masterItemOrLLDType} {printMasterItemKey} submitted'
	
	# regular item & submittable, but already in task list, return False
	if itemId in taskItems: # already in task list
		return False,f'{hostReturnStr}{itemOrLLDType} {item} already submitted'

	# regular item & submittable, but already in task list
	return itemId,f'{hostReturnStr}{itemOrLLDType} {item} submitted'

# determine if this is a regular item or LLD rule item
def itemOrLLD(item):
		if "discover" in item.keys():
			return "LLD rule"
		else:
			return "item"

def sendZabbixRequest(*,url,req):
	headers = {
		'Content-type': 'application/json'
	}

	try:
		r=requests.post(url,data=json.dumps(req),headers=headers,verify=False)
		if not r.ok: # exit with an error and text if we don't get a 200
			print(f'API ERROR: {r.status_code} - {r.text}')
			sys.exit()

		res=json.loads(r.text)
		if 'result' in res.keys(): # result field?  return it
			return json.loads(r.text)

		# error within the JSON, just dump the JSON results
		print(f'ERROR:')
		print(json.dumps(res,indent=4,sort_keys=True))
		sys.exit()
	except Exception:
		traceback.print_exc()
		sys.exit()

if __name__ == '__main__':
	main()
