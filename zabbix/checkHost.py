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
from rich import print as rprint
from rich.markup import escape as escape

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

# https://rich.readthedocs.io/en/stable/appendix/colors.html
itemKeyColor="cyan"
itemNameColor="bright_white"
hostNameColor="green"
disabledColor="purple"
itemTypeColor="sandy_brown"
taskAlreadySubmittedColor="bright_red"
dryRunColor="bright_yellow"
taskIdColor="cyan"
errColor="red"

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
		rprint(f'[{errColor}]authID not in configuration file .zbx.env[/{errColor}]')
		sys.exit()
	if 'apiURL' not in config.keys():
		rprint(f'[{errColor}]apiURL not in configuration file .zbx.env[/{errColor}]')
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
		for host in foundHosts:
			hostName=escape(host["host"])
			for item in host['items']+host['discoveries']:
				key=escape(item["key_"])
				name=escape(item["name"])
				type=itemTypes[item["type"]]
				itemOrLLDType=itemOrLLD(item)
				if host["status"] == "0":
					hostName=f"[{hostNameColor}]{hostName}[/{hostNameColor}]"
				else:
					hostName=f"[{disabledColor}]{hostName}[/{disabledColor}]"

				if item["status"] == "0":
					key=f"[{itemKeyColor}]{key}[/{itemKeyColor}]"
					name=f"[{itemNameColor}]{name}[/{itemNameColor}]"
				else:
					key=f"[{disabledColor}]{key}[/{disabledColor}]"
					name=f"[{disabledColor}]{name}[/{disabledColor}]"

				# item status
				rprint(f'{hostName} - {itemOrLLDType} - {name} - {key} - [{itemTypeColor}]{type}[/{itemTypeColor}]')
		sys.exit()
	
	# get back a list of item IDs we can submit tasks for
	taskItemIDs=getTaskItems(reqHosts=reqHosts,reqItems=reqItems,foundHosts=foundHosts)

	# no hosts/items matching what was requested
	if len(taskItemIDs) == 0:
		rprint(f"[{errColor}]No matching hosts and/or allowable items found[/{errColor}]")
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
		rprint(f'[{dryRunColor}]!!!! dry run set, not sending request[/{dryRunColor}] !!!!')
		sys.exit()
	apiRes=sendZabbixRequest(req=apiReq,url=apiURL)
	print('Tasks(s) submitted: ',end='')
	rprint(f'[{taskIdColor}]{apiRes["result"]["taskids"][0]}[/{taskIdColor}]',end='')
	if len(apiRes["result"]["taskids"]) > 1:
		for taskID in apiRes["result"]["taskids"][1:]:
			rprint(f',[{taskIdColor}]{taskID}[/{taskIdColor}]',end='')
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
			rprint(f'[{hostNameColor}]{host}[/{hostNameColor}] - [{errColor}]does not exist in Zabbix[/{errColor}]')
		elif foundHostsByHost[host]["status"] != "0": # host is not enabled
			rprint(f'[{hostNameColor}]{host}[/{hostNameColor}] - [{errColor}]not enabled (status "{foundHostsByHost[host]["status"]}")[/{errColor}]')
		else: # host is in Zabbix and enabled, let's iterate through keys
			allHostItems=foundHostsByHost[host]["items"]+foundHostsByHost[host]["discoveries"] # list of all items on the current host
			if len(reqItems) == 0: # requested items is empty, make searchItems the host's whole list of items
				searchItems=list((x["key_"] for x in allHostItems)) # list of all keys on the host
			else:
				searchItems=reqItems

			for item in searchItems:
				itemID,message=validateItem(host=host,item=item,foundItems=allHostItems,taskItems=taskItems)
				rprint(message)
				if itemID:
					taskItems.append(itemID)

	return taskItems

# pass in a hostname, item key, a list of available items, and a list of already found itemids
# return an itemID & message if the item is valid for submission or False if not & message
def validateItem(*,host,item,foundItems,taskItems): # item key to look for, all items we're searching, and list of taskItems we've already found
	hostReturnStr=f'[{hostNameColor}]{host}[/{hostNameColor}] - '
	foundItemsByKey={it["key_"]:it for it in foundItems} # all keys on the host, indexed by key_
	foundItemsById={it["itemid"]:it for it in foundItems}# all keys on the host, indexed by itemid
	printItem=escape(item)
	
	if item not in foundItemsByKey.keys(): # item does not exist in this host, return False
		return False,f'{hostReturnStr}item [{itemKeyColor}]{printItem}[/{itemKeyColor}] [{errColor}]does not exist[/{errColor}]'
	
	# item exists on the host, extract some details about it
	itemOrLLDType=itemOrLLD(foundItemsByKey[item])
	itemId=foundItemsByKey[item]["itemid"]
	masterItemId=foundItemsByKey[item]["master_itemid"]	
	itemStatus=foundItemsByKey[item]["status"]
	itemType=foundItemsByKey[item]["type"]
	itemTypeText=itemTypes[itemType]
	if masterItemId != "0": # item is a dependent item, let's get some master item details
		printMasterItemKey=escape(foundItemsById[masterItemId]["key_"])
		masterItemOrLLDType=itemOrLLD(foundItemsById[masterItemId])
		masterItemType=foundItemsById[masterItemId]["type"]
		masterItemTypeText=itemTypes[masterItemType]
		masterItemStatus=foundItemsById[masterItemId]["status"] # NEED TO ADD A CHECK FOR THIS BELOW!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

	# item exists on this host, but is not enabled, return False
	if itemStatus != "0": # item is not enabled
		return False,f'{hostReturnStr}{itemOrLLDType} [{itemKeyColor}]{printItem}[/{itemKeyColor}] [{errColor}]not submitted (item disabled)[/{errColor}]'
	
	# item is enabled, but item type is not allowed, return False
	if itemType not in allowedItemTypes: # item type not allowed
		return False,f'{hostReturnStr}{itemOrLLDType} [{itemKeyColor}]{printItem}[/{itemKeyColor}] [{errColor}]not submitted (type {itemTypeText})[/{errColor}]'

	# item type allowed
	if masterItemId != "0": # it's a dependent item, need to check it's master item, return failures or success

		if masterItemStatus != "0": # master item is not enabled
			return False,f'{hostReturnStr}{itemOrLLDType} [{itemKeyColor}]{printItem}[/{itemKeyColor}] [{errColor}]not submitted due to master {masterItemOrLLDType} {printMasterItemKey} (master item disabled)[/{errColor}]'

		if masterItemType not in allowedItemTypes: # master item type not allowed, return False
			return False,f'{hostReturnStr}{itemOrLLDType} [{itemKeyColor}]{printItem}[/{itemKeyColor}] [{errColor}]not submitted due to master {masterItemOrLLDType} {printMasterItemKey} (type {masterItemTypeText})[/{errColor}]'

		if masterItemId in taskItems: # master item is already in list
			return False,f'{hostReturnStr}{itemOrLLDType} [{itemKeyColor}]{printItem}[/{itemKeyColor}] master {masterItemOrLLDType} [{itemKeyColor}]{printMasterItemKey}[/{itemKeyColor}] [{taskAlreadySubmittedColor}]already submitted[/{taskAlreadySubmittedColor}]'

		# master item id not in list and allowed, return master item id
		return masterItemId,f'[{hostReturnStr}{itemOrLLDType} [{itemKeyColor}]{printItem}[/{itemKeyColor}] master {masterItemOrLLDType} [{itemKeyColor}]{printMasterItemKey}[/{itemKeyColor}] submitted'
	
	# regular item & submittable, but already in task list, return False
	if itemId in taskItems: # already in task list
		return False,f'{hostReturnStr}{itemOrLLDType} [{itemKeyColor}]{printItem}[/{itemKeyColor}] [{taskAlreadySubmittedColor}]already submitted[/{taskAlreadySubmittedColor}]'

	# regular item & submittable, but already in task list
	return itemId,f'{hostReturnStr}{itemOrLLDType} [{itemKeyColor}]{printItem}[/{itemKeyColor}] submitted'

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
		rprint(f'[{errColor}]ERROR:[/{errColor}]')
		rprint(json.dumps(res,indent=4,sort_keys=True))
		sys.exit()
	except Exception:
		traceback.print_exc()
		sys.exit()

if __name__ == '__main__':
	main()
