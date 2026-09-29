"""Codex metadata preflight: no thread/start, turn/start, prompt or model completion.
Requires a native Codex executable; stores only model/version/usage metadata.
"""
from __future__ import annotations
import argparse, hashlib, json, queue, re, subprocess, threading, time
from datetime import datetime, timezone
from pathlib import Path

ALLOWED={'initialize','model/list','account/rateLimits/read','config/read'}
MIN_VERSION=(0,153,0)

class RpcError(RuntimeError): pass

class MetadataClient:
 def __init__(self, command:list[str], cwd:Path, timeout:float=45):
  self.timeout=timeout;self.next_id=0;self.q=queue.Queue();self.methods=[]
  self.proc=subprocess.Popen(command,cwd=str(cwd),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                             text=True,encoding='utf-8',errors='replace',bufsize=1)
  def consume():
   try:
    for line in self.proc.stdout:
     try:self.q.put(json.loads(line))
     except (ValueError,TypeError):pass
   finally:self.q.put(None)
  def drain():
   # Do not persist arbitrary stderr (it can contain account-specific details).
   for _ in self.proc.stderr: pass
  self.reader=threading.Thread(target=consume,daemon=True);self.reader.start()
  threading.Thread(target=drain,daemon=True).start()
 def send(self, obj):
  self.proc.stdin.write(json.dumps(obj)+'\n');self.proc.stdin.flush()
 def request(self, method, params=None):
  if method not in ALLOWED:raise ValueError('Non-metadata operation prohibited in this probe: '+method)
  self.next_id+=1;rid=self.next_id;self.methods.append(method)
  msg={'method':method,'id':rid}
  if params is not None:msg['params']=params
  self.send(msg);deadline=time.monotonic()+self.timeout
  while time.monotonic()<deadline:
   try:r=self.q.get(timeout=max(.01,deadline-time.monotonic()))
   except queue.Empty:raise RpcError('Timeout waiting for '+method)
   if r is None:raise RpcError('Codex app-server exited before answering '+method)
   if not isinstance(r,dict) or r.get('id')!=rid:continue
   if 'error' in r:raise RpcError(method+' returned error code '+str(r['error'].get('code')))
   if 'result' not in r:raise RpcError('Unexpected response to '+method)
   return r['result']
  raise RpcError('Timeout waiting for '+method)
 def initialize(self):
  r=self.request('initialize',{'clientInfo':{'name':'a2wc511r_preflight','title':'A2WC511R metadata preflight','version':'3.0.0'}})
  self.send({'method':'initialized','params':{}})
  return r
 def close(self):
  try:self.proc.stdin.close()
  except (BrokenPipeError,OSError):pass
  try:self.proc.wait(timeout=3)
  except subprocess.TimeoutExpired:
   self.proc.terminate()
   try:self.proc.wait(timeout=3)
   except subprocess.TimeoutExpired:self.proc.kill();self.proc.wait(timeout=3)
  for s in (self.proc.stdout,self.proc.stderr):
   try:s.close()
   except OSError:pass

def selected_model(models, preferred='gpt-6-astra', effort='ultra'):
 visible=[m for m in models if not m.get('hidden',False)]
 exact=[m for m in visible if m.get('model')==preferred or m.get('id')==preferred]
 if not exact:
  raise ValueError('Requested model not returned: '+preferred+'. Select an exact returned Astra model ID explicitly; no automatic substitution.')
 if len(exact)!=1:raise ValueError('Model identity is ambiguous in catalog')
 m=exact[0]
 supported=[e.get('reasoningEffort') if isinstance(e,dict) else e for e in m.get('supportedReasoningEfforts',[])]
 if effort not in supported:raise ValueError('Requested effort '+effort+' not advertised. Advertised: '+repr(supported))
 if 'astra' not in (str(m.get('model',''))+' '+str(m.get('displayName',''))).lower():
  raise ValueError('Returned model is not identified as Astra; verify the requested deployment explicitly.')
 return {'model':m.get('model') or m.get('id'),'effort':effort,'display_name':m.get('displayName'),
         'supported_efforts':supported,'evidence':'current authenticated model/list'}

def slim_usage(result):
 def bucket(b):
  if not isinstance(b,dict):return None
  out={k:b.get(k) for k in ('limitId','limitName','rateLimitReachedType')}
  for which in ('primary','secondary'):
   x=b.get(which)
   out[which]={k:x.get(k) for k in ('usedPercent','windowDurationMins','resetsAt')} if isinstance(x,dict) else None
  return out
 return {'rateLimits':bucket(result.get('rateLimits')),
         'rateLimitsByLimitId':{k:bucket(v) for k,v in (result.get('rateLimitsByLimitId') or {}).items()}}

def probe(codex:Path, cwd:Path, model:str, effort:str):
 codex=codex.resolve()
 if not codex.is_file():raise ValueError('Native Codex executable not found')
 if codex.suffix.lower() in ('.ps1','.cmd','.bat'):raise ValueError('Supply the native codex.exe, not an npm/PowerShell shim. See docs/CLI_SETUP.md.')
 p=subprocess.run([str(codex),'--version'],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=20)
 version_text=(p.stdout or p.stderr).strip()
 found=re.search(r'\b(\d+)\.(\d+)\.(\d+)\b',version_text)
 if p.returncode or not found or tuple(map(int,found.groups()))<MIN_VERSION:
  raise ValueError('Codex >=0.153.0 required; actual: '+version_text)
 login=subprocess.run([str(codex),'login','status'],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=20)
 if login.returncode:raise ValueError('Codex is not authenticated. Run this native executable with login, then repeat preflight; no model task was sent.')
 api_key_auth='api key' in (login.stdout+' '+login.stderr).lower()
 h=hashlib.sha256(codex.read_bytes()).hexdigest()
 report={'schema':1,'generated_at':datetime.now(timezone.utc).isoformat(),'codex_exe':str(codex),
         'codex_sha256':h,'codex_version':version_text,'cwd':str(cwd.resolve()),
         'requested_model':model,'requested_effort':effort,'ready_for_model_run':False,
         'prompt_started':False,'login_status_returncode':login.returncode,'api_key_auth_indicated':api_key_auth,'warnings':[]}
 if api_key_auth:report['warnings'].append('API-key login detected: API billing is separate from a ChatGPT plan. No budget/purchase authorization is inferred.')
 client=MetadataClient([str(codex),'app-server'],cwd)
 try:
  client.initialize();models=[];cursor=None;seen=set()
  for _ in range(20):
   params={'limit':100,'includeHidden':False}
   if cursor:params['cursor']=cursor
   r=client.request('model/list',params);models.extend(r.get('data',[]));cursor=r.get('nextCursor')
   if not cursor:break
   if cursor in seen:raise RpcError('Repeated model/list cursor')
   seen.add(cursor)
  else:raise RpcError('Model catalog pagination limit reached')
  report['models']=[{k:m.get(k) for k in ('id','model','displayName','hidden','defaultReasoningEffort','supportedReasoningEfforts')} for m in models]
  try:report['selected']=selected_model(models,model,effort);report['ready_for_model_run']=True
  except ValueError as e:report['error']=str(e)
  try:
   report['usage']=slim_usage(client.request('account/rateLimits/read'))
   primary=report['usage'].get('rateLimits') or {}
   exhausted=primary.get('rateLimitReachedType') is not None
   for key in ('primary','secondary'):
    bucket=primary.get(key) or {}
    if isinstance(bucket.get('usedPercent'),(int,float)) and bucket['usedPercent']>=100:exhausted=True
   if exhausted:
    report['ready_for_model_run']=False
    report['error']='The returned primary Codex allowance reports a reached limit. Wait/review the account; no automatic credit purchase or reset consumption.'
  except RpcError:report['warnings'].append('Usage buckets unavailable; no assumption of unlimited allowance.')
  try:
   cfg=client.request('config/read',{'includeLayers':False}).get('config',{})
   provider=cfg.get('model_provider')
   report['configured_model_provider']=provider
   if provider not in (None,'openai'):
    report['ready_for_model_run']=False
    report['error']='Non-OpenAI model provider configured. Confirm intended provider/routing before this Astra run.'
   tier=cfg.get('service_tier')
   if tier is None:tier=((cfg.get('models') or {}).get('new_thread') or {}).get('service_tier')
   report['configured_service_tier']=tier
   if tier in ('fast','priority'):
    report['ready_for_model_run']=False
    report['error']='Fast/priority tier configured. Disable Fast for this efficiency-first run, then re-probe.'
  except RpcError:report['warnings'].append('Could not inspect service tier; confirm Fast is off in local configuration.')
 except (RpcError,BrokenPipeError,OSError) as e:
  report['ready_for_model_run']=False;report['error']=str(e)
 finally:report['methods_sent']=client.methods;client.close()
 return report

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--codex',type=Path,required=True);p.add_argument('--cwd',type=Path,default=Path(r'C:\Dev'))
 p.add_argument('--model',default='gpt-6-astra');p.add_argument('--effort',default='ultra');p.add_argument('--out',type=Path,required=True)
 a=p.parse_args();a.out.parent.mkdir(parents=True,exist_ok=True)
 try:r=probe(a.codex,a.cwd,a.model,a.effort)
 except Exception as e:r={'schema':1,'generated_at':datetime.now(timezone.utc).isoformat(),'ready_for_model_run':False,'prompt_started':False,'error':str(e)}
 a.out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:r[k] for k in ('ready_for_model_run','prompt_started','selected','error','warnings') if k in r},indent=2))
 print('Metadata report:',a.out)
 raise SystemExit(0 if r['ready_for_model_run'] else 2)
if __name__=='__main__':main()
