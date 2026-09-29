"""Local stdio MCP: native RomRaider editor model + immutable table/log history.
No hardware connection. No arbitrary execution. Commit requires a local editor dialog.
"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from core import Store,Bridge

def obj(properties,required=None):return {'type':'object','properties':properties,'required':required if required is not None else list(properties),'additionalProperties':False}
S={'type':'string'};N={'type':'number'};I={'type':'integer'};A={'type':'array','items':S}
CELL=obj({'row':I,'column':I})
BIND=obj({'column':S,'unit':S,'factor':N,'offset':N})
TOOLS=[]
def tool(name,description,props,required=None,read=True):
    TOOLS.append({'name':name,'description':description,'inputSchema':obj(props,required),'annotations':{'readOnlyHint':read,'destructiveHint':False,'idempotentHint':read,'openWorldHint':False}})
tool('rr_status','List ROMs open in the actual RomRaider editor and probe the bridge session. Does not create an editor.',{})
tool('rr_capture_snapshot','Capture all loaded tables, axes, native scales, presets and values into immutable content-addressed project history.',{'rom_id':S,'label':S},read=False)
tool('rr_live_table','Read one table or axis (Table Name::x / ::y / ::axis) directly from the running editor model.',{'rom_id':S,'table':S})
tool('rr_history','List immutable snapshot/log/overlay/proposal/comparison/event records.',{'kind':S,'limit':I},required=[])
tool('rr_snapshot_table','Read a table from a historical snapshot, including axes as separate explicit keys.',{'snapshot_id':S,'table':S})
tool('rr_compare_snapshots','Compare raw and real values and flag changed axes/scales. Write a complete comparison report.',{'old_snapshot':S,'new_snapshot':S,'table':S},required=['old_snapshot','new_snapshot'],read=False)
tool('rr_ingest_log','Capture a CSV from inside this workspace. Association must explicitly be user_attested_applied_rom or unverified_candidate_association; timestamps alone do not establish flashed ROM.',{'path':S,'snapshot_id':S,'association':S,'note':S},read=False)
tool('rr_table_timeline','Join explicit logger channels/units to the associated snapshot table axes, with filters and declared sensor delay. Produces a full timeline CSV, weighted cell evidence and local HTML report. Analysis interpolation is not proof of actual ECU table selection.',{'log_id':S,'table':S,'bindings':{'type':'object','properties':{'x':BIND,'y':BIND},'additionalProperties':False},'metric_column':S,'time_column':S,'time_unit':S,'filters':{'type':'array','items':{'type':'object'}},'active_table_evidence':S,'metric_delay_ms':N,'max_alignment_gap_ms':N},required=['log_id','table','bindings','metric_column','time_column','time_unit','filters','active_table_evidence'],read=False)
tool('rr_calculate_proposal','Evaluate a restricted numeric formula with supplied variables and optionally actual weighted cell evidence. Preserves unselected/unsupported cells. Produces an unapproved proposal, NOT guaranteed optimum.',{'snapshot_id':S,'table':S,'expression':S,'cells':{'type':'array','items':CELL},'constants':{'type':'object','additionalProperties':N},'constraints':obj({'minimum':N,'maximum':N,'max_abs_delta':N,'min_samples':I,'tolerance':N}),'reason':S,'evidence':A,'overlay_id':S},required=['snapshot_id','table','expression','cells','constants','constraints','reason','evidence'],read=False)
tool('rr_preset_proposal','Build a proposal from a named native switch/preset state. No invented numeric optimization of enum/switch states.',{'snapshot_id':S,'table':S,'preset':S,'reason':S,'evidence':A},read=False)
tool('rr_preview_proposal','Run a reversible native-editor transaction and return achieved quantized values plus byte diff. Restores the complete editor ROM buffer before returning. Not a read-only operation internally.',{'proposal_id':S},read=False)
tool('rr_commit_preview','Apply an exact unexpired preview to the editor after a local YES/NO dialog. Does not save to disk, fix checksums, or flash. Never retry automatically after timeout.',{'preview_id':S},read=False)
tool('rr_export_model','Export the current editor byte buffer under a SHA256 NOT_FLASH_READY filename in the dedicated work directory. Does not overwrite a source ROM or call Rom.saveFile/checksum side effects.',{'rom_id':S,'expected_rom_sha256':S},read=False)

def invoke(store,name,args):
    entry=next((x for x in TOOLS if x['name']==name),None)
    if entry is None or not isinstance(args,dict):raise ValueError('Unknown tool / invalid arguments')
    s=entry['inputSchema']
    if not set(s['required'])<=args.keys() or not args.keys()<=s['properties'].keys():raise ValueError('Missing or unexpected arguments')
    for k,v in args.items():
        ty=s['properties'][k].get('type');checks={'string':lambda:isinstance(v,str),'number':lambda:type(v)in(int,float),'integer':lambda:type(v)is int,'array':lambda:isinstance(v,list),'object':lambda:isinstance(v,dict)}
        if ty in checks and not checks[ty]():raise ValueError('Wrong type for '+k)
    if name=='rr_status':return store.bridge.request('status',{})
    if name=='rr_capture_snapshot':return store.capture(args['rom_id'],args['label'])
    if name=='rr_live_table':return store.bridge.request('table',args)
    if name=='rr_history':return {'records':store.history(args.get('kind','snapshots'),args.get('limit',30))}
    if name=='rr_snapshot_table':s,t=store.table(args['snapshot_id'],args['table']);return {'rom':s['rom'],'table':t}
    if name=='rr_compare_snapshots':return store.compare(args['old_snapshot'],args['new_snapshot'],args.get('table'))
    if name=='rr_ingest_log':return store.ingest_log(**args)
    if name=='rr_table_timeline':q=dict(args);q['table_key']=q.pop('table');return store.overlay(**q)
    if name=='rr_calculate_proposal':q=dict(args);q['table_key']=q.pop('table');return store.calculate(**q)
    if name=='rr_preset_proposal':q=dict(args);q['table_key']=q.pop('table');q['preset_name']=q.pop('preset');return store.preset_proposal(**q)
    if name=='rr_preview_proposal':return store.preview(args['proposal_id'])
    if name in {'rr_commit_preview','rr_export_model'}:
        op='commit' if name=='rr_commit_preview' else 'export_model';result=store.bridge.request(op,args)
        from core import utc
        event=store.put('events',{'captured_utc':utc(),'kind':op,'result':result});return {'event_id':event,**result}
    raise ValueError('Unsupported tool')

def serve(store,inp=None,out=None):
    inp=inp or sys.stdin;out=out or sys.stdout;ready=False
    for line in inp:
        rid=None
        try:
            if len(line)>4*1024*1024:raise ValueError('Request too large')
            q=json.loads(line)
            if not isinstance(q,dict) or q.get('jsonrpc')!='2.0':raise ValueError('JSON-RPC 2.0 required')
            if 'id'not in q:continue
            rid=q['id'];method=q.get('method');p=q.get('params')or{}
            if method=='initialize':
                v=p.get('protocolVersion');v=v if v in {'2024-11-05','2025-03-26','2025-06-18'} else '2025-06-18';ready=True
                result={'protocolVersion':v,'capabilities':{'tools':{}},'serverInfo':{'name':'romraider-model-history','version':'2.0.0'}}
            elif method=='ping':result={}
            elif not ready:raise ValueError('initialize first')
            elif method=='tools/list':result={'tools':TOOLS}
            elif method=='tools/call':
                try:
                    data=invoke(store,p.get('name'),p.get('arguments',{}));result={'content':[{'type':'text','text':json.dumps(data,ensure_ascii=False,allow_nan=False)}],'isError':False}
                except Exception as e:result={'content':[{'type':'text','text':type(e).__name__+': '+str(e)}],'isError':True}
            else:
                out.write(json.dumps({'jsonrpc':'2.0','id':rid,'error':{'code':-32601,'message':'Method unsupported'}})+'\n');out.flush();continue
            response={'jsonrpc':'2.0','id':rid,'result':result}
        except Exception as e:response={'jsonrpc':'2.0','id':rid,'error':{'code':-32600,'message':str(e)}}
        out.write(json.dumps(response,ensure_ascii=False,allow_nan=False)+'\n');out.flush()

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--connection',type=Path,required=True);a=p.parse_args()
    if not a.root.is_dir():raise SystemExit('Workspace root missing')
    if hasattr(sys.stdin,'reconfigure'):sys.stdin.reconfigure(encoding='utf-8');sys.stdout.reconfigure(encoding='utf-8')
    serve(Store(a.root,Bridge(a.connection)))
if __name__=='__main__':main()
