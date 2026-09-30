"""Preserve/validate one completed final run; never launch a process or provider."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
from launch_final_once import HERE,SESSION,SESSION_ID,GATES,STATE,TOKEN,read,require,write_new,digest
from validate_final import rows,validate
def pin(p):
 p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=digest(p))
def main():
 require(sys.argv[1:]==['--seal-completed-session'],'Explicit completed-session sealing command')
 execution=read(SESSION/'EXECUTION.json');gates=read(GATES)
 require(execution['process_exited'] is True and gates['probe_invocation_count']==1 and gates['session_id']==SESSION_ID,'Exactly one exited physical process')
 require(gates['commit_authorization']['reply']==TOKEN and gates['commit_authorization']['source']=='user','Human authorization')
 output=HERE/'physical_result';output.mkdir(exist_ok=False);copies=output/'evidence';copies.mkdir();evidence=[]
 for source in sorted(SESSION.iterdir()):
  if source.is_file():
   target=copies/source.name
   with source.open('rb') as src,target.open('xb') as dst:
    while data:=src.read(1048576):dst.write(data)
   require(digest(source)==digest(target),'Evidence copy integrity');evidence.append(pin(source))
 validation=None;failure=None
 try:
  require(execution['exit_code']==0 and execution['bookkeeping_error'] is None,'Child exit/bookkeeping')
  require(read(SESSION/'POSTEXIT_CLIENT_CHECK.json')['pass'] is True,'Provider/client cleanup check')
  certificate=read(HERE/'qualification/QUALIFICATION.json');contract=read(HERE/'FINAL_TWO_PASS_REVIEW_CONTRACT.json');contract['_sha256']=digest(HERE/'FINAL_TWO_PASS_REVIEW_CONTRACT.json')
  require(digest(HERE/'qualification/QUALIFICATION.json')==execution['qualification_sha256'],'Certificate binding')
  require(execution['session_id']==certificate['session_id']==SESSION_ID,'Session binding')
  require(certificate['physical_executable']['sha256']==execution['executable_sha256']==digest(certificate['physical_executable']['path']),'Executable binding')
  require(certificate['review_contract']['sha256']==execution['contract_sha256']==contract['_sha256'],'Contract binding')
  reference=Path(contract['current_reference']['path']).read_bytes()
  summary,images=validate(rows(SESSION/'native_api.jsonl'),contract,reference,True,dict(session_id=SESSION_ID,exe_sha256=execution['executable_sha256'],contract_sha256=contract['_sha256'],provider_sha256=contract['physical_provider']['sha256']))
  for n,raw in enumerate(images):require((SESSION/f'pass{n}.raw').read_bytes()==raw,'Every saved byte equals independently reconstructed physical responses')
  summary['raw_files']=[pin(SESSION/f'pass{n}.raw') for n in range(2)];validation=summary
 except Exception as exc:failure=str(exc)
 status='PASS' if validation else 'FAIL'
 result=dict(schema=1,RK03_FINAL_TWO_PASS_128_PHYSICAL=status,session_id=SESSION_ID,utc=datetime.now(timezone.utc).isoformat(),physical_invocations=1,execution=execution,validation=validation,validation_failure=failure,source_evidence=evidence,validator=pin(Path(__file__)),stream_validator=pin(HERE/'validate_final.py'),retry_allowed=False,additional_kernel_start_allowed=False,ROM_image_designation='CURRENT_PHYSICAL_CAPTURE',factory_stock_claim=False,next_required_state='IGNITION OFF')
 write_new(output/'PHYSICAL_RESULT.json',result);write_new(output/'MANIFEST.json',dict(status='SEALED_FINAL_TWO_PASS_128_'+status,files=[pin(p) for p in sorted(output.rglob('*')) if p.is_file()]))
 for p in list(SESSION.iterdir())+list(output.rglob('*')):
  if p.is_file():p.chmod(0o444)
 gates.update(final_physical=status,status='PROBE_EXITED_IGNITION_OFF_REQUIRED',next_gate='IGNITION OFF',physical_result=pin(output/'PHYSICAL_RESULT.json'));GATES.write_text(json.dumps(gates,indent=2)+'\n',encoding='utf8')
 state=read(STATE);state.update(RK03_FINAL_TWO_PASS_128_PHYSICAL=status,final_physical_result=str(output/'PHYSICAL_RESULT.json'),final_physical_invocations=1,next_action='IGNITION OFF then NORMAL MODE ON and passive OEM return',human_required=['IGNITION OFF']);STATE.write_text(json.dumps(state,indent=2)+'\n',encoding='utf8')
 print(json.dumps(dict(status=status,validation_failure=failure,result=pin(output/'PHYSICAL_RESULT.json'))))
if __name__=='__main__':main()
