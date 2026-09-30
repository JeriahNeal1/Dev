"""Final offline integrity audit and local checkpoint/tag after physical/OEM PASS."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys
from launch_final_once import HERE,SESSION,REPO,GATES,STATE,read,require,write_new,digest
from validate_final import rows,validate
def pin(p):
 p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=digest(p))
def check_pins(v):
 if isinstance(v,dict):
  if isinstance(v.get('path'),str) and isinstance(v.get('sha256'),str):require(digest(v['path'])==v['sha256'],'Changed evidence '+v['path'])
  for x in v.values():check_pins(x)
 elif isinstance(v,list):
  for x in v:check_pins(x)
def main():
 require(sys.argv[1:]==['--audit-completed-project'],'Explicit final audit command')
 require(not (HERE/'project_completion').exists(),'No overwrite of completed audit')
 g=read(GATES);p=read(HERE/'physical_result/PHYSICAL_RESULT.json');o=read(HERE/'oem_return_after_final_01/OEM_RETURN_RESULT.json');c=read(HERE/'qualification/QUALIFICATION.json')
 require(g['probe_invocation_count']==g['passive_oem_return_invocations']==1,'Exactly one acquisition and one passive return')
 require(p['RK03_FINAL_TWO_PASS_128_PHYSICAL']=='PASS' and o['OEM_RETURN_AFTER_FINAL_TWO_PASS_128']=='PASS','Both physical and recovery PASS')
 require(g['physical_state']=='NORMAL MODE ON' and [x['reply'] for x in g['completed_recovery_gates']]==['IGNITION OFF','NORMAL MODE ON'],'Recovery states')
 require(o['BF_identity']=='2F12515306' and o['samples']==120 and o['capture_status']=='PASS_CAPTURE_ONLY','OEM identity/capture')
 require(all(o[k] for k in ['observer_cleanup_confirmed','broker_cleanup_confirmed','provider_cleanup_confirmed']),'OEM cleanup')
 for evidence in [c,HERE/'physical_result/MANIFEST.json',HERE/'oem_return_after_final_01/MANIFEST.json']:
  check_pins(read(evidence) if isinstance(evidence,Path) else evidence)
 contract=read(HERE/'FINAL_TWO_PASS_REVIEW_CONTRACT.json');contract['_sha256']=digest(HERE/'FINAL_TWO_PASS_REVIEW_CONTRACT.json');reference=Path(contract['current_reference']['path']).read_bytes()
 summary,images=validate(rows(SESSION/'native_api.jsonl'),contract,reference,True,dict(session_id=p['session_id'],exe_sha256=p['execution']['executable_sha256'],contract_sha256=contract['_sha256'],provider_sha256=contract['physical_provider']['sha256']))
 for n,data in enumerate(images):require((SESSION/f'pass{n}.raw').read_bytes()==data,'Final raw byte audit')
 commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip();require(commit==c['commit'],'Release source commit')
 require(not subprocess.check_output(['git','status','--porcelain'],cwd=REPO,text=True).strip(),'Clean source worktree')
 out=HERE/'project_completion';out.mkdir();tag='rk03-final-two-pass-128-project-complete'
 require(subprocess.run(['git','show-ref','--verify','--quiet','refs/tags/'+tag],cwd=REPO).returncode==1,'Completion tag must be new')
 report=dict(status='FINAL_INTEGRITY_AUDIT_PASS',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),commit=commit,tag=tag,ROM_image_designation='CURRENT_PHYSICAL_CAPTURE',factory_stock_claim=False,physical_result=pin(HERE/'physical_result/PHYSICAL_RESULT.json'),OEM_return=pin(HERE/'oem_return_after_final_01/OEM_RETURN_RESULT.json'),qualification=pin(HERE/'qualification/QUALIFICATION.json'),raw_files=[pin(SESSION/f'pass{n}.raw') for n in range(2)],current_reference=pin(contract['current_reference']['path']),comparison=summary['result'],complete_wire_and_file_integrity=True,additional_physical_operation_allowed=False)
 write_new(out/'INTEGRITY_AUDIT.json',report)
 message=out/'TAG_MESSAGE.txt';message.write_text('PROJECT COMPLETE: fixed128 two-pass physical acquisition and passive OEM return.\nAudit SHA256 '+digest(out/'INTEGRITY_AUDIT.json')+'\n',encoding='utf8')
 subprocess.run(['git','tag','-a',tag,commit,'-F',str(message)],cwd=REPO,check=True)
 report=dict(status='PROJECT COMPLETE',commit=commit,tag=tag,tag_object=subprocess.check_output(['git','rev-parse','refs/tags/'+tag],cwd=REPO,text=True).strip(),integrity_audit=pin(out/'INTEGRITY_AUDIT.json'),physical_operations_complete=True,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 write_new(out/'PROJECT_COMPLETE.json',report);write_new(out/'MANIFEST.json',dict(files=[pin(x) for x in sorted(out.iterdir()) if x.is_file()]))
 for x in out.iterdir():x.chmod(0o444)
 g.update(status='PROJECT_COMPLETE',next_gate=None,project_completion=pin(out/'PROJECT_COMPLETE.json'));GATES.write_text(json.dumps(g,indent=2)+'\n',encoding='utf8')
 state=read(STATE);state.update(phase='PROJECT_COMPLETE',human_required=[],next_action=None,project_completion=pin(out/'PROJECT_COMPLETE.json'),further_physical_activity_allowed=False);STATE.write_text(json.dumps(state,indent=2)+'\n',encoding='utf8')
 print(json.dumps(report))
if __name__=='__main__':main()
