#!/root/scripts/venv/bin/python3
import argparse
import requests
import json
import sys
import dotenv
import tabulate

# suppress InsecureRequestWarning warning
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

def main():
	parser = argparse.ArgumentParser(description='run a zabbix script')
	parser.add_argument('-s',dest='script',action='store',help='script to run',required=True)
	parser.add_argument('-z',dest='host',action='store',help='host to run the script against',required=True)
	args = parser.parse_args()

	script_name="Reload Configuration Cache"
	script_host="zabbix.tblake.org"

	script_name=args.script
	script_host=args.host

	config = dotenv.dotenv_values(sys.path[0]+"/.zbx.env")
	if 'authID' not in config.keys():
		print(f'authID not in configuration file .zbx.env')
		sys.exit()
	if 'apiURL' not in config.keys():
		print(f'apiURL not in configuration file .zbx.env')
		sys.exit()

	authID=config['authID'] 
	apiURL=config['apiURL']


	req={
		"jsonrpc": "2.0",
		"method": "script.get",
		"params": {
			"search": {
				"name": script_name
			},
			"output": "extend"
		},
		"id": 1
	}
	res=sendZabbixRequest(req=req,url=apiURL,authID=authID)
	if len(res["result"]) == 0:
		print(f"No script named {script_name} found")
		sys.exit()
	elif len(res["result"]) > 1:
		print(f"More than one script named {script_name} found")
		sys.exit()

	scriptid=res["result"][0]["scriptid"]
	req={
		"jsonrpc": "2.0",
		"method": "host.get",
		"params": {
			"search": {
				"host": script_host
			},
			"output": "refer",
		},
		"id": 1
	}
	res=sendZabbixRequest(req=req,url=apiURL,authID=authID)
	if len(res["result"]) == 0:
		print(f"No host named {script_host} found")
		sys.exit()
	elif len(res["result"]) > 1:
		print(f"More than one host named {script_host} found")
		sys.exit()

	hostid=res["result"][0]["hostid"]
	req={
		"jsonrpc": "2.0",
		"method": "script.execute",
		"params": {
			"scriptid": scriptid,
			"hostid": hostid
		},
		"id": 1
	}

	res=sendZabbixRequest(req=req,url=apiURL,authID=authID)
	response=res["result"]["response"]
	value=res["result"]["value"]
	debug=json.dumps(res["result"]["debug"])

	#headers=['Response','Value','Debug']
	#table=[[response,value,debug]]

	headers=['Response','Value']
	table=[[response,value]]

	print(tabulate.tabulate(table,headers=headers))

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
