"""Pure validation and mocked abort-during-scan checks; never runs native code."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import copy,json
import launch_oem_return_once as m

checks=[]
execution=dict(session_id=m.SESSION_ID,process_exited=True,exited_utc='2026-09-30T01:00:00+00:00')
good=dict(session_id=m.SESSION_ID,probe_invocation_count=1,process_exited=True,
          status='RECOVERY_NORMAL_MODE_CONFIRMED',physical_state='NORMAL MODE ON',engine='OFF',abort_requested=False,
          completed_recovery_gates=[dict(reply='IGNITION OFF',source='user',session_id=m.SESSION_ID,received_utc='2026-09-30T01:01:00+00:00'),
                                    dict(reply='NORMAL MODE ON',source='user',session_id=m.SESSION_ID,received_utc='2026-09-30T01:02:00+00:00')])
def rejected(name,change):
    g=copy.deepcopy(good);change(g)
    try:m.validate_recovery(g,execution)
    except (RuntimeError,KeyError,ValueError,TypeError):checks.append(name)
    else:raise RuntimeError('Accepted '+name)
m.validate_recovery(good,execution);checks.append('positive_fresh_recovery')
for k,v in [('session_id','OLD'),('probe_invocation_count',0),('process_exited',False),('status','RUNNING'),
            ('physical_state','TEST MODE ON'),('engine','ON'),('abort_requested',True)]:
    rejected('reject_'+k,lambda g,k=k,v=v:g.__setitem__(k,v))
rejected('reject_reordered_gates',lambda g:g['completed_recovery_gates'].reverse())
rejected('reject_recovery_before_exit',lambda g:g['completed_recovery_gates'][0].update(received_utc='2026-09-30T00:59:00+00:00'))
rejected('reject_timezone_missing',lambda g:g['completed_recovery_gates'][0].update(received_utc='2026-09-30T01:01:00'))
rejected('reject_nonhuman_reply',lambda g:g['completed_recovery_gates'][0].update(source='assistant'))
rejected('reject_old_session_reply',lambda g:g['completed_recovery_gates'][0].update(session_id='OLD'))
with TemporaryDirectory(prefix='rk03_passive_controls_') as folder:
    base=Path(folder);gates=base/'gates.json';session=base/'fake_session';session.mkdir();out=base/'fake_output'
    gates.write_text(json.dumps(good));(session/'EXECUTION.json').write_text(json.dumps(execution))
    calls=[]
    def abort_scan(argv,check):
        calls.append('scan');m.write_new(Path(argv[-1]),{'pass':True})
        altered=copy.deepcopy(good);altered['abort_requested']=True;gates.write_text(json.dumps(altered))
    def no_process(*a,**k): raise RuntimeError('TEST FAILURE: subprocess must not be launched')
    with patch.object(m,'GATES',gates),patch.object(m,'SESSION',session),patch.object(m,'OUT',out),\
         patch.object(m,'validate_reuse',lambda expected_sha=None:({'files':[]},'a'*64)),\
         patch.object(m.subprocess,'run',abort_scan),patch.object(m.subprocess,'Popen',no_process):
        try:m.run_once()
        except RuntimeError as exc:
            if str(exc).startswith('TEST FAILURE'):raise
            if calls!=['scan'] or (out/'invocation.once').exists():raise RuntimeError('Abort check boundary')
            checks.append('reject_abort_arriving_during_client_scan')
        else:raise RuntimeError('Abort ignored')
report=dict(status='PASS',checks_passed=len(checks),checks=checks,physical_operations=0,provider_loads=0,
            subprocess_calls='MOCKED_ONLY',wrapper={'path':m.__file__,'sha256':m.digest(m.__file__)},
            test_source={'path':__file__,'sha256':m.digest(__file__)})
m.write_new(Path(__file__).parent/'OEM_RETURN_CONTROL_TESTS_V2.json',report)
print(json.dumps({'status':'PASS','checks':len(checks)}))
