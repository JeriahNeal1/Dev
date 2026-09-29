"""Local transport only for official IDA MCP. No retry of mutations."""
import http.client, json
from datetime import datetime,timezone
from pathlib import Path
OUT=Path(__file__).parent
connection=http.client.HTTPConnection('127.0.0.1',8737,timeout=380)
def request(method,params=None):
    payload={'jsonrpc':'2.0','id':1,'method':method}
    if params is not None:payload['params']=params
    record={'request':payload}
    path=OUT/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json')
    try:
        connection.request('POST','/mcp',body=json.dumps(payload),headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream'})
        response=connection.getresponse();raw=response.read().decode()
        record['http_status']=response.status
        if raw.startswith('event:') or raw.startswith('data:'):raw='\n'.join(s[5:].strip() for s in raw.splitlines() if s.startswith('data:'))
        result=json.loads(raw);record['response']=result
        if 'error' in result or result.get('result',{}).get('isError'):raise RuntimeError('Official MCP error')
        return result
    except Exception as e:
        record['error']=repr(e);raise
    finally:path.write_text(json.dumps(record,indent=2),encoding='utf-8')
if __name__=='__main__':
    a=request('tools/list');print('official_tools',len(a['result']['tools']))
    b=request('tools/call',{'name':'reference','arguments':{'query':'names comments instructions'}})
    print('reference_ok',not b['result'].get('isError'))
    c=request('tools/call',{'name':'list_databases','arguments':{}})
    print(json.dumps(c.get('result',{}).get('structuredContent',c.get('result',{}))))
