"""Launcher qualification uses disposable fake paths and mocked subprocess only."""
from pathlib import Path
from datetime import datetime, timezone
from tempfile import TemporaryDirectory
from unittest.mock import patch
import copy, hashlib, importlib.util, json, sys

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('launcher',HERE/'launch_bounded_once.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=[]
def require(ok,name):
    if not ok: raise RuntimeError(name)
    checks.append(name)
def gate(sha):
    return dict(session_id=m.SESSION_ID,qualification_sha256=sha,probe_invocation_count=0,launch_reserved=False,
      status='AUTHORIZED_BOUNDED_ROM_READ_ONLY',physical_state='TEST MODE ON',engine='OFF',
      operator_managed_physical_context=True,full_acquisition_allowed=False,retry_allowed=False,abort_requested=False,
      completed_pre_probe_gates=[dict(reply='IGNITION OFF',source='user',session_id=m.SESSION_ID,received_utc='2026-09-30T00:00:00+00:00'),
        dict(reply='TEST MODE ON',source='user',session_id=m.SESSION_ID,received_utc='2026-09-30T00:01:00+00:00')],
      commit_authorization=dict(reply=m.TOKEN,source='user',session_id=m.SESSION_ID,qualification_sha256=sha,received_utc='2026-09-30T00:02:00+00:00'))
def reject(name,change):
    g=gate('a'*64); change(g)
    try: m.validate_gate(g,'a'*64)
    except (RuntimeError,KeyError,ValueError,TypeError): checks.append(name)
    else: raise RuntimeError('Accepted negative '+name)

m.validate_gate(gate('a'*64),'a'*64); checks.append('positive_simplified_gate')
for key,value in [('session_id','OLD'),('qualification_sha256','b'*64),('probe_invocation_count',1),
                  ('launch_reserved',True),('status','NOT_AUTHORIZED'),('physical_state','NORMAL MODE ON'),
                  ('engine','ON'),('operator_managed_physical_context',False),('full_acquisition_allowed',True),
                  ('retry_allowed',True),('abort_requested',True)]:
    reject('reject_'+key,lambda g,k=key,v=value:g.__setitem__(k,v))
reject('reject_missing_gate',lambda g:g['completed_pre_probe_gates'].pop())
reject('reject_reordered_gates',lambda g:g['completed_pre_probe_gates'].reverse())
reject('reject_historical_component_gates',lambda g:g['completed_pre_probe_gates'][0].update(reply='DONE G06'))
reject('reject_nonhuman_gate',lambda g:g['completed_pre_probe_gates'][0].update(source='assistant'))
reject('reject_old_gate_session',lambda g:g['completed_pre_probe_gates'][0].update(session_id='OLD'))
reject('reject_gate_without_timezone',lambda g:g['completed_pre_probe_gates'][0].update(received_utc='2026-09-30T00:00:00'))
reject('reject_old_transition_token',lambda g:g['commit_authorization'].update(reply='PROCEED RK03 TRANSITION PROBE'))
reject('reject_nonexact_token',lambda g:g['commit_authorization'].update(reply=m.TOKEN+' '))
reject('reject_nonhuman_authorization',lambda g:g['commit_authorization'].update(source='assistant'))
reject('reject_wrong_auth_certificate',lambda g:g['commit_authorization'].update(qualification_sha256='b'*64))
reject('reject_old_auth_session',lambda g:g['commit_authorization'].update(session_id='OLD'))
reject('reject_auth_before_test_mode',lambda g:g['commit_authorization'].update(received_utc='2026-09-30T00:00:30+00:00'))

class Child:
    pid=123456
    waited=False
    def wait(self): self.waited=True; return 0
child=Child()
def bookkeeping_error(): raise OSError('injected offline bookkeeping failure')
code,error=m.wait_for_child(child,bookkeeping_error)
require(code==0 and child.waited and 'injected' in error,'wait_child_after_bookkeeping_failure')
class InterruptedChild(Child):
    waits=0
    def wait(self):
        self.waits+=1
        if self.waits==1: raise KeyboardInterrupt('offline injected console interruption')
        self.waited=True
        return 0
interrupted=InterruptedChild()
code,error=m.wait_for_child(interrupted,lambda:None)
require(code==0 and interrupted.waited and interrupted.waits==2 and 'wait interrupted' in error,'wait_child_after_console_interrupt')

original=dict(HERE=m.HERE,SESSION=m.SESSION,EXE=m.EXE,CONTRACT=m.CONTRACT,CERT=m.CERT,GATES=m.GATES,STATE=m.STATE)
with TemporaryDirectory(prefix='rk03_launcher_offline_') as temp:
    base=Path(temp);m.HERE=base;m.SESSION=base/'fake_session';m.EXE=base/'fake.exe'
    m.CONTRACT=base/'contract.json';m.CERT=base/'qualification.json';m.GATES=base/'gates.json';m.STATE=base/'state.json'
    m.EXE.write_bytes(b'NOT_AN_EXECUTABLE_OFFLINE_TEST');m.CONTRACT.write_text('{}');(base/'check_clients.ps1').write_text('NEVER_EXECUTED')
    def pin(p): return dict(path=str(p),sha256=m.digest(p),bytes=p.stat().st_size)
    cert=dict(status='PASS_OFFLINE_QUALIFIED_PHYSICAL_BOUNDED_ROM_READ_ONLY',session_id=m.SESSION_ID,maximum_physical_invocations=1,
              physical_executable=pin(m.EXE),review_contract=pin(m.CONTRACT),
              files=[pin(Path(m.__file__)),pin(base/'check_clients.ps1'),pin(m.EXE),pin(m.CONTRACT)])
    m.CERT.write_text(json.dumps(cert));m.GATES.write_text(json.dumps(gate(m.digest(m.CERT))));m.STATE.write_text('{}')
    m.preflight();checks.append('positive_fake_preflight')
    goodexe=m.EXE.read_bytes();m.EXE.write_bytes(b'TAMPERED')
    try: m.preflight()
    except RuntimeError: checks.append('reject_executable_tamper')
    else: raise RuntimeError('tampered executable accepted')
    m.EXE.write_bytes(goodexe)
    oldcert=m.CERT.read_bytes();bad=copy.deepcopy(cert);bad['files']=bad['files'][1:]
    m.CERT.write_text(json.dumps(bad));m.GATES.write_text(json.dumps(gate(m.digest(m.CERT))))
    try: m.preflight()
    except RuntimeError: checks.append('reject_unpinned_launcher')
    else: raise RuntimeError('unpinned launcher accepted')
    m.CERT.write_bytes(oldcert);m.GATES.write_text(json.dumps(gate(m.digest(m.CERT))))
    calls=[]
    def fake_check(argv,check):
        calls.append(('client_check',argv));m.write_new(Path(argv[-1]),{'pass':True})
    def fake_popen(argv,stdout,stderr):
        calls.append(('popen',argv));return Child()
    with patch.object(m.subprocess,'run',fake_check),patch.object(m.subprocess,'Popen',fake_popen): m.run_once()
    require([c[0] for c in calls]==['client_check','popen'],'exactly_one_mocked_child_after_check')
    require(calls[1][1]==[str(m.EXE),'--physical-bounded-rom-read','--session',str(m.SESSION),'--authorization-file',str(m.SESSION/'AUTHORIZATION.txt')],'fixed_child_argv')
    require(m.read(m.SESSION/'EXECUTION.json')['process_exited'] is True,'recorded_child_exit')
    require(m.read(m.GATES)['next_gate']=='IGNITION OFF','recovery_only_ignition_off')
    require((m.SESSION/'AUTHORIZATION.txt').read_bytes().startswith((m.TOKEN+'\n').encode()),'exact_auth_prefix_LF')
    try: m.preflight()
    except RuntimeError: checks.append('reject_second_invocation')
    else: raise RuntimeError('second invocation accepted')
    # Reset only disposable gates, proving native/root markers independently block replay.
    m.GATES.write_text(json.dumps(gate(m.digest(m.CERT))))
    try: m.preflight()
    except RuntimeError: checks.append('reject_existing_session_evidence')
    else: raise RuntimeError('session marker accepted')
for k,v in original.items(): setattr(m,k,v)
report=dict(schema=1,created_utc=datetime.now(timezone.utc).isoformat(),status='PASS',
            physical_operations=0,provider_loads=0,subprocess_calls='MOCKED_ONLY',python_optimized=not __debug__,
            checks_passed=len(checks),checks=checks,
            launcher=dict(path=str(Path(m.__file__)),sha256=m.digest(m.__file__)),
            test_source=dict(path=str(Path(__file__)),sha256=m.digest(__file__)))
output=HERE/('LAUNCHER_TESTS_V2_OPTIMIZED.json' if not __debug__ else 'LAUNCHER_TESTS_V2.json')
m.write_new(output,report)
print(json.dumps({'status':'PASS','checks':len(checks),'report':str(output)}))
