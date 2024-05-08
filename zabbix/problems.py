#!/root/scripts/venv/bin/python3
import datetime
import requests
import json
import sys
import dotenv
import tabulate
import argparse

# suppress InsecureRequestWarning warning
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

def main():
	parser = argparse.ArgumentParser(
		description='List, ack, comment on, and close active problems',
		epilog=f"usage: %(prog)s [OPTIONS]")
	parser.add_argument('-e','--eventid',dest='eventid',action='append',default=[],help='Event ID to take action on, multiple -e options allowed')
	parser.add_argument('-m','--message',dest='message',action='store',default='',help='message to add to problem(s), cannot be an empty string')
	parser.add_argument('-c','--close',dest='close',action='store_true',default=False,help='close out problem(s)')
	parser.add_argument('-i','--id',dest='listeventids',action='store_true',default=False,help='show event IDs in listing')
	parser.add_argument('-a','--ack',dest='ack',action='store_true',default=False,help='acknowledge problem')
	parser.add_argument('-l','--long',dest='long_format',action='store_true',default=False,help='print in long format')
	args = parser.parse_args()

	config = dotenv.dotenv_values(sys.path[0]+"/.zbx.env")
	if 'authID' not in config.keys():
		print(f'authID not in configuration file .zbx.env')
		sys.exit()
	if 'apiURL' not in config.keys():
		print(f'apiURL not in configuration file .zbx.env')
		sys.exit()

	authID=config['authID'] 
	apiURL=config['apiURL']

	if (args.eventid and not (args.message or args.close or args.ack)) or (not args.eventid and (args.message or args.close or args.ack)):
		parser.print_help(sys.stdout)
		sys.exit()

	req={
		"jsonrpc": "2.0",
		"method": "problem.get",
		"params": {
			"sortfield":["eventid"],
			"source":0,
			"object":0,
			"sortorder": "DESC",
			"preservekeys": "yes",
			"output":[
				"eventid",
				"objectid",
				"clock",
				"name",
				"severity",
				"acknowledged",
				"suppressed"
			]
		},
		"id": 1
	}

	problems=sendZabbixRequest(req=req,url=apiURL,authID=authID)
	o=[x['objectid'] for x in problems["result"].values()]
	objectids=list(dict.fromkeys(o,None).keys())
	req={	"jsonrpc": "2.0",
		"method": "trigger.get",
		"params": {
			"preservekeys": "yes",
			"output": [
				"manual_close"
			],
			"selectHosts": ["host"],
				"triggerids" : objectids,
				"monitored": 1,
				"skipDependent": 1
		},
		"id": 1
	}
	triggers=sendZabbixRequest(req=req,url=apiURL,authID=authID)
	now=int(datetime.datetime.now().timestamp())
	closestr=['No','Yes']
	table_headers=['Host(s)','Trigger','Severity','Time','Duration','Closeable']
	if args.listeventids or args.message or args.close or args.ack:
		table_headers.insert(0,'Event ID')

	t=[]
	errors=""
	valideventids=[]
	severities=[
		'Not Classified',
		'Information',
		'Warning',
		'Average',
		'High',
		'Disaster'
	]
	for eventid,event in problems["result"].items():
		if event["objectid"] in triggers["result"].keys():
			url=f'https://zabbix.tblake.org/tr_events.php?triggerid={event["objectid"]}&eventid={eventid}'
			valideventids.append(eventid)
			name=event["name"]
			if int(event["acknowledged"]) or int(event["acknowledged"]):
				name=name+"("
				if int(event["acknowledged"]):
					name=name+"a"
				if int(event["suppressed"]):
					name=name+"s"
				name=name+")"
			hostlist=[x["host"] for x in triggers["result"][event["objectid"]]["hosts"]]
			hosts=','.join(hostlist)
			clock=int(event["clock"])
			severity=severities[int(event["severity"])]
			timedifference=now-clock
			closeable=int(triggers["result"][event["objectid"]]["manual_close"])
			if args.close and eventid in args.eventid and closeable==0:
				if len(hostlist) > 1:
					errors=errors+f'ERROR: Can not close trigger "{name}" for hosts "{hosts}", trigger is not closeable\n'
				else:
					errors=errors+f'ERROR: Can not close trigger "{name}" for host "{hosts}", trigger is not closeable\n'
			t.append([hosts,name,severity,datetime.datetime.fromtimestamp(clock).strftime('%x %X'),datetime.timedelta(seconds=timedifference),closestr[closeable]])
			if args.listeventids or args.message or args.close or args.ack:
				t[-1].insert(0,eventid)

	if not args.long_format:
		print(tabulate.tabulate(t,headers=table_headers,numalign="left"))
	else:
		for event in t:
			for x in range(len(table_headers)):
				print(f'{table_headers[x]}: {event[x]}')
			print()

	if args.eventid:
		for eventid in args.eventid:
			if eventid not in valideventids:
				errors=errors+f'ERROR: "{eventid}" not in list of problems\n'

		if errors != "":
			print()
			print(errors,end='')
			sys.exit()

		req={
			"jsonrpc": "2.0",
			"method": "event.acknowledge",
			"params": {
				"eventids": args.eventid,
				"action": 0
			},
			"id": 1
		}
		if args.close:
			req["params"]["action"]=req["params"]["action"]+1
		if args.ack:
			req["params"]["action"]=req["params"]["action"]+2
		if args.message:
			req["params"]["action"]=req["params"]["action"]+4
			req["params"]["message"]=args.message

		res=sendZabbixRequest(req=req,url=apiURL,authID=authID)
		idresults=','.join([str(x) for x in res["result"]["eventids"]])
		print()
		if len(res["result"]["eventids"])>1:
			print(f'succesfully updated event ids {idresults}')
		else:
			print(f'succesfully updated event id {idresults}')

def pp(j):
	import json
	print(json.dumps(j,indent=4,sort_keys=True))

def sendZabbixRequest(*,url,req,authID):
	headers = {
		'Content-type': 'application/json',
		'Authorization': f'Bearer {authID}',
		'User-Agent': 'python-requests/Todd Blake'
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
		pp(res)
		sys.exit()
	except Exception:
		traceback.print_exc()
		sys.exit()

if __name__ == '__main__':
	main()
