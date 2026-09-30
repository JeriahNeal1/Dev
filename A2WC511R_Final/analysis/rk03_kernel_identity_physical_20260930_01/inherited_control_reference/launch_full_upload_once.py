"""Single physical full-upload/no-start launch; no main execution on import. No retry."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = Path(r'C:\Dev\A2WC511R_RK03_FullUploadPhysical')
SESSION_ID = 'RK03_FULL_UPLOAD_NO_START_01'
SESSION = REPO / 'physical_session' / SESSION_ID
EXE = REPO / 'full_upload_physical/build_a/rk03_full_upload_no_start_physical32.exe'
CONTRACT = HERE / 'PHYSICAL_FULL_UPLOAD_REVIEW_CONTRACT.json'
CERT = HERE / 'qualification/QUALIFICATION.json'
GATES = HERE / 'FULL_UPLOAD_GATE_STATE.json'
STATE = Path(r'C:\Dev\A2WC511R_Final\state\CURRENT.json')
TOKEN = 'PROCEED RK03 FULL UPLOAD NO START'
RESERVATIONS = ['launch.reserved', 'invocation.once', 'AUTHORIZATION.txt',
                'native_api.jsonl', 'EXECUTION_BEGIN.json', 'EXECUTION.json',
                'EXECUTION_LAUNCHER_ERROR.json', 'console.log']

def now():
    return datetime.now(timezone.utc).isoformat()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def require(condition, detail='Physical launch precondition failed'):
    if not condition:
        raise RuntimeError(detail)

def write_new(path, obj):
    with Path(path).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, indent=2)
        f.write('\n')

def validate_gate(gates, cert_sha):
    require(gates['session_id'] == SESSION_ID, 'Wrong session')
    require(gates['qualification_sha256'] == cert_sha, 'Qualification gate binding')
    require(gates['probe_invocation_count'] == 0 and gates.get('launch_reserved') is False, 'One-shot reservation/count')
    require(gates['status'] == 'AUTHORIZED_FULL_UPLOAD_NO_START_ONLY', 'Exact authorization state required')
    require(gates['physical_state'] == 'TEST MODE ON', 'Test Mode state required')
    rows = gates['completed_pre_probe_gates']
    require([r['reply'] for r in rows] == ['IGNITION OFF', 'TEST MODE ON'], 'Fresh simplified gate order')
    times = []
    for row in rows:
        require(row['source'] == 'user' and row['session_id'] == SESSION_ID, 'Human gate source/session')
        stamp = datetime.fromisoformat(row['received_utc'])
        require(stamp.tzinfo is not None, 'Gate timestamp timezone')
        times.append(stamp)
    auth = gates['commit_authorization']
    require(auth['reply'] == TOKEN and auth['source'] == 'user', 'Exact new commit token required')
    require(auth['session_id'] == SESSION_ID and auth['qualification_sha256'] == cert_sha, 'Authorization session/certificate binding')
    stamp = datetime.fromisoformat(auth['received_utc'])
    require(stamp.tzinfo is not None and times[0] <= times[1] <= stamp, 'Human gate chronology')
    require(gates['engine'] == 'OFF', 'Engine OFF required')
    require(gates['operator_managed_physical_context'] is True, 'Operator context policy')
    require(gates['full_acquisition_allowed'] is False and gates['retry_allowed'] is False, 'Scope/retry interlock')
    require(gates.get('abort_requested', False) is False, 'Operator abort interlock')

def preflight():
    cert_bytes = CERT.read_bytes()
    cert_sha = hashlib.sha256(cert_bytes).hexdigest()
    cert = json.loads(cert_bytes.decode('utf-8-sig'))
    require(cert['status'] == 'PASS_OFFLINE_QUALIFIED_PHYSICAL_FULL_UPLOAD_NO_START_ONLY', 'Offline qualification required')
    require(cert['session_id'] == SESSION_ID and cert['maximum_physical_invocations'] == 1)
    require(Path(cert['physical_executable']['path']).resolve() == EXE.resolve())
    require(cert['physical_executable']['sha256'] == digest(EXE))
    require(Path(cert['review_contract']['path']).resolve() == CONTRACT.resolve())
    require(cert['review_contract']['sha256'] == digest(CONTRACT))
    required = {Path(__file__).resolve(), (HERE/'check_clients.ps1').resolve(), EXE.resolve(), CONTRACT.resolve()}
    require(required.issubset({Path(r['path']).resolve() for r in cert['files']}), 'Required controls absent from qualification pins')
    for row in cert['files']:
        require(digest(row['path']) == row['sha256'], 'Changed qualified input: '+row['path'])
    gates = read(GATES)
    validate_gate(gates, cert_sha)
    require(not any((SESSION/n).exists() for n in RESERVATIONS), 'Physical session already reserved or executed')
    return cert, gates, cert_sha

def wait_for_child(process, record_started):
    """Always await already-started child even when bookkeeping fails."""
    error = None
    try:
        record_started()
    except BaseException as exc:
        error = repr(exc)
    finally:
        while True:
            try:
                exit_code = process.wait()
                break
            except KeyboardInterrupt as exc:
                # Console interruption is not proof the provider child exited.
                # Keep owning/waiting for it; never relaunch the physical operation.
                error = (error+'; ' if error else '')+'wait interrupted: '+repr(exc)
    return exit_code, error

def run_once():
    cert, gates, cert_sha = preflight()
    SESSION.mkdir(parents=True, exist_ok=True)
    check = SESSION/'PRELAUNCH_CLIENT_CHECK.json'
    subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',
                    str(HERE/'check_clients.ps1'),'-OutputPath',str(check)], check=True)
    require(read(check)['pass'] is True, 'Competing client/module inspection failed')
    # Gates and certificate must remain valid after client inspection.
    require(digest(CERT) == cert_sha, 'Qualification changed during client inspection')
    gates = read(GATES)
    validate_gate(gates, cert_sha)
    exe_sha, contract_sha = digest(EXE), digest(CONTRACT)
    require(exe_sha == cert['physical_executable']['sha256'])
    require(contract_sha == cert['review_contract']['sha256'])
    require(not any((SESSION/n).exists() for n in RESERVATIONS), 'Reservation changed during client inspection')
    authorization = f'{TOKEN}\nSESSION_ID={SESSION_ID}\nEXE_SHA256={exe_sha}\nCONTRACT_SHA256={contract_sha}\n'
    with (SESSION/'AUTHORIZATION.txt').open('x', encoding='ascii', newline='\n') as f:
        f.write(authorization)
    with (SESSION/'launch.reserved').open('x', encoding='ascii', newline='\n') as f:
        f.write(f'{SESSION_ID}\n{exe_sha}\n{contract_sha}\n')
    gates.update(launch_reserved=True, launch_reserved_utc=now(), status='SINGLE_LAUNCH_RESERVED_NO_RETRY')
    GATES.write_text(json.dumps(gates,indent=2)+'\n', encoding='utf-8')
    argv = [str(EXE),'--physical-full-upload-no-start','--session',str(SESSION),
            '--authorization-file',str(SESSION/'AUTHORIZATION.txt')]
    started = dict(session_id=SESSION_ID,command_argv=argv,started_utc=now(),executable_sha256=exe_sha,
                   contract_sha256=contract_sha,qualification_sha256=cert_sha,
                   authorization_source='Exact new user token after IGNITION OFF and TEST MODE ON',retry_allowed=False)
    write_new(SESSION/'EXECUTION_BEGIN.json',started)
    try:
        with (SESSION/'console.log').open('xb') as console:
            process = subprocess.Popen(argv,stdout=console,stderr=subprocess.STDOUT)
            def record_started():
                gates.update(probe_invocation_count=1,process_id=process.pid,status='PROBE_RUNNING_NO_PHYSICAL_STATE_CHANGES')
                GATES.write_text(json.dumps(gates,indent=2)+'\n',encoding='utf-8')
                state = read(STATE)
                state.update(phase='RK03_FULL_UPLOAD_NO_START_RUNNING',full_upload_physical_invocations=1,
                             full_upload_physical_process_id=process.pid,full_upload_physical_session=str(SESSION),updated_utc=now())
                STATE.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
            exit_code, bookkeeping_error = wait_for_child(process,record_started)
        result = dict(started,pid=process.pid,exit_code=exit_code,exited_utc=now(),process_exited=True,
                      bookkeeping_error=bookkeeping_error)
    except Exception as exc:
        write_new(SESSION/'EXECUTION_LAUNCHER_ERROR.json',dict(started,launcher_error=repr(exc),retry_allowed=False))
        raise
    write_new(SESSION/'EXECUTION.json',result)
    gates.update(status='PROBE_EXITED_IGNITION_OFF_REQUIRED',process_exited=True,exit_code=exit_code,next_gate='IGNITION OFF')
    GATES.write_text(json.dumps(gates,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))

if __name__ == '__main__':
    if sys.argv[1:] != ['--run-once']:
        raise SystemExit('Only --run-once: requires qualification, fresh simplified gates and exact user authorization')
    run_once()
