#!/root/scripts/venv/bin/python3
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
	parser = argparse.ArgumentParser(description='Show all unsupported items')
	parser.add_argument('-e',dest='show_errors',action='store_true',default=False,help='show errors field')
	parser.add_argument('-c',dest='show_count',action='store_true',default=False,help='just show total count')

	args = parser.parse_args()
	show_errors=args.show_errors
	show_count=args.show_count

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
		"method": "item.get",
		"params": {
			"output": [
				"key_",
				"status",
				"name"
			],
			"selectHosts":["host"],
			"monitored": "true",
			"countOutput": show_count,
			"tags": [
					{
						"tag":"notsupportedok",
						"operator":"5"
					}
				],
			"filter":{
				"state":"1",
				"status":"0"
			}
		},
		"id": 1
	}

	if show_errors:
		req["params"]["output"].append("error")

	res=sendZabbixRequest(req=req,url=apiURL,authID=authID)

	if show_count:
		print(res["result"])
	elif show_errors:
		t=[[x["hosts"][0]["host"],x["key_"],x["name"],x["error"]] for x in res["result"]]
		print(tabulate.tabulate(t,headers=['Host','Key','Name','Error']))
	else:
		t=[[x["hosts"][0]["host"],x["key_"],x["name"]] for x in res["result"]]
		print(tabulate.tabulate(t,headers=['Host','Key','Name']))

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
