"""Dependency-free, read-only MCP stdio server for this project. No ECU access.
MCP JSON-RPC over newline-delimited UTF-8, protocol 2025-06-18.
"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT_CODE=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT_CODE/'tools'))
from project_core import resolve_inside,rom_audit,binary_diff,csv_summary,gear_log_analysis,logger_validate


def schema(props,required):
    return {'type':'object','properties':props,'required':required,'additionalProperties':False}
STR={'type':'string'}
TOOLS=[
 {'name':'rom_audit','description':'Read a 1 MiB ROM; report identity, hashes, known pointer checks and candidate FF runs. No flash-safety conclusion.','inputSchema':schema({'path':STR},['path'])},
 {'name':'rom_diff','description':'Read-only binary diff. Does not apply patches.','inputSchema':schema({'a':STR,'b':STR},['a','b'])},
 {'name':'csv_summary','description':'Summarize an existing CSV including missing values and polling intervals.','inputSchema':schema({'path':STR},['path'])},
 {'name':'gear_log_analysis','description':'Compare packed gear nibbles with decoded bytes and list transitions; not a validity certification.','inputSchema':schema({'path':STR},['path'])},
 {'name':'logger_validate','description':'Validate project logger XML structure and exact ECU-scoped raw-byte channels.','inputSchema':schema({'path':STR},['path'])},
]
for t in TOOLS:t['annotations']={'readOnlyHint':True,'destructiveHint':False,'idempotentHint':True,'openWorldHint':False}

def call_tool(root,name,args):
    if not isinstance(args,dict):raise ValueError('Arguments must be object')
    entry=next((t for t in TOOLS if t['name']==name),None)
    if not entry:raise ValueError('Unknown tool')
    sc=entry['inputSchema']
    if set(args)!=set(sc['required']):raise ValueError('Unexpected or missing arguments')
    if not all(isinstance(v,str) for v in args.values()):raise ValueError('Paths must be strings')
    paths={k:resolve_inside(root,v) for k,v in args.items()}
    if name=='rom_diff':return binary_diff(paths['a'],paths['b'])
    return {'rom_audit':rom_audit,'csv_summary':csv_summary,'gear_log_analysis':gear_log_analysis,'logger_validate':logger_validate}[name](paths['path'])

def serve(root,instream=None,outstream=None):
    inp=instream or sys.stdin
    out=outstream or sys.stdout
    initialized=False
    for line in inp:
        if len(line)>1048576:continue
        try:
            q=json.loads(line)
            if not isinstance(q,dict):raise ValueError('Expected JSON-RPC object')
            if 'id' not in q:continue
            rid=q['id']; method=q.get('method'); p=q.get('params') or {}
            if method=='initialize':
                requested=p.get('protocolVersion','2025-06-18')
                ver=requested if requested in {'2024-11-05','2025-03-26','2025-06-18'} else '2025-06-18'
                result={'protocolVersion':ver,'capabilities':{'tools':{}},'serverInfo':{'name':'a2wc511r-project','version':'1.0.0'}};initialized=True
            elif method=='ping':result={}
            elif not initialized:raise ValueError('initialize required')
            elif method=='tools/list':result={'tools':TOOLS}
            elif method=='tools/call':
                try:
                    value=call_tool(root,p.get('name'),p.get('arguments',{}))
                    result={'content':[{'type':'text','text':json.dumps(value,ensure_ascii=False)}],'isError':False}
                except Exception as e:result={'content':[{'type':'text','text':f'{type(e).__name__}: {e}'}],'isError':True}
            else:
                out.write(json.dumps({'jsonrpc':'2.0','id':rid,'error':{'code':-32601,'message':'Method not supported'}})+'\n');out.flush();continue
            response={'jsonrpc':'2.0','id':rid,'result':result}
        except Exception as e:
            response={'jsonrpc':'2.0','id':None,'error':{'code':-32700,'message':str(e)}}
        out.write(json.dumps(response,ensure_ascii=False)+'\n');out.flush()

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args()
    if not a.root.is_dir():raise SystemExit('Project root does not exist')
    if hasattr(sys.stdin,'reconfigure'):sys.stdin.reconfigure(encoding='utf-8');sys.stdout.reconfigure(encoding='utf-8')
    serve(a.root.resolve())
if __name__=='__main__':main()
