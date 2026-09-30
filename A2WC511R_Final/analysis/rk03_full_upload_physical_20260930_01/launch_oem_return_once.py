"""Only the unchanged passive observer, after completed full-upload/no-start recovery gates."""
from pathlib import Path
from datetime import datetime
import hashlib,json,subprocess,sys
from launch_full_upload_once import HERE,GATES,SESSION,SESSION_ID,STATE,now,read,digest,require,write_new,wait_for_child

OLD=HERE.parent/'current_rom_20260930_01'
REUSE=OLD/'OEM_RETURN_REUSE.json'
OUT=HERE/'oem_return_after_full_upload_01'
CAPTURE=Path(r'C:\Dev\A2WC511R_Final\passive_som01\integrations\prehardware\capture.py')
def validate_recovery(gates,execution):
    require(gates['session_id']==SESSION_ID and gates['probe_invocation_count']==1)
    require(gates['process_exited'] is True and execution['process_exited'] is True)
    require(execution['session_id']==SESSION_ID)
    require(gates['status']=='RECOVERY_NORMAL_MODE_CONFIRMED' and gates['physical_state']=='NORMAL MODE ON' and gates['engine']=='OFF')
    rows=gates['completed_recovery_gates']
    require([r['reply'] for r in rows]==['IGNITION OFF','NORMAL MODE ON'])
    require(all(r['source']=='user' and r['session_id']==SESSION_ID for r in rows))
    times=[datetime.fromisoformat(execution['exited_utc'])]+[datetime.fromisoformat(r['received_utc']) for r in rows]
    require(all(t.tzinfo is not None for t in times) and times[0]<=times[1]<=times[2], 'Recovery must follow confirmed probe exit')
    require(not gates.get('abort_requested',False))

def validate_reuse(expected_sha=None):
    reuse_bytes=REUSE.read_bytes()
    reuse_sha=hashlib.sha256(reuse_bytes).hexdigest()
    require(expected_sha is None or reuse_sha==expected_sha,'Retained passive qualification changed')
    reuse=json.loads(reuse_bytes.decode('utf-8-sig'))
    require(reuse['status']=='PASS_UNCHANGED_QUALIFIED_PASSIVE_REUSE')
    for row in reuse['files']:
        require(digest(row['path'])==row['sha256'],'Passive reused input changed: '+row['path'])
    require(digest(CAPTURE)=='d8fdab93292130a85e8d3a42b2ce0bd8a1b28d5ce65133a58171a5f0ed3bf3d7')
    return reuse,reuse_sha

def run_once():
    gates=read(GATES)
    execution=read(SESSION/'EXECUTION.json')
    validate_recovery(gates,execution)
    reuse,reuse_sha=validate_reuse()
    OUT.mkdir(exist_ok=False)
    subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(HERE/'check_clients.ps1'),
                    '-OutputPath',str(OUT/'PRELAUNCH_CLIENT_CHECK.json')],check=True)
    require(read(OUT/'PRELAUNCH_CLIENT_CHECK.json')['pass'] is True)
    gates=read(GATES)
    validate_recovery(gates,read(SESSION/'EXECUTION.json'))
    reuse,_=validate_reuse(reuse_sha)
    # Preserve exact state/pins and reserve this passive capture once, never retry.
    write_new(OUT/'GATE_STATE_BEFORE_OEM_RETURN.json',gates)
    write_new(OUT/'PREFLIGHT.json',dict(status='PASS',reused_qualification=reuse_sha,files=reuse['files'],
                                     recovery_policy='SIMPLIFIED_IGNITION_STATES',checked_utc=now()))
    argv=[r'C:\Windows\py.exe','-3.14','-B',str(CAPTURE),'--backend','physical-j2534',
          '--authorize-physical-read-only','--count','120','--interval-ms','250','--output',str(OUT/'capture.jsonl')]
    begun=dict(session_id=SESSION_ID,command_argv=argv,started_utc=now(),retry_allowed=False,scope='PASSIVE_BF_A8_ONLY')
    write_new(OUT/'invocation.once',begun)
    with (OUT/'console.log').open('xb') as console:
        process=subprocess.Popen(argv,stdout=console,stderr=subprocess.STDOUT)
        def record_started():
            gates.update(passive_oem_return_invocations=1,passive_process_id=process.pid,status='OEM_RETURN_RUNNING')
            GATES.write_text(json.dumps(gates,indent=2)+'\n',encoding='utf-8')
        exit_code,error=wait_for_child(process,record_started)
    result=dict(begun,pid=process.pid,exit_code=exit_code,exited_utc=now(),process_exited=True,bookkeeping_error=error)
    write_new(OUT/'EXECUTION.json',result)
    subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(HERE/'check_clients.ps1'),
                    '-OutputPath',str(OUT/'POSTEXIT_CLIENT_CHECK.json')],check=True)
    print(json.dumps(result))

if __name__=='__main__':
    if sys.argv[1:]!=['--run-once-oem-return']:
        raise SystemExit('Only --run-once-oem-return after completed recovery ignition gates')
    run_once()
