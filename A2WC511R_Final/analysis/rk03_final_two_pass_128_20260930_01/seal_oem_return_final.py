"""Validate and preserve passive OEM return after the bounded ROM-read probe."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re

A=Path(__file__).resolve().parent
O=A/'oem_return_after_final_01'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def pin(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def require(ok,why):
    if not ok:raise RuntimeError(why)
def new_json(p,obj):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,indent=2);f.write('\n')
rows=[json.loads(x) for x in (O/'capture.jsonl').read_text().splitlines()]
ids=[r for r in rows if r.get('type')=='identity'];samples=[r for r in rows if r.get('type')=='sample'];end=rows[-1]
require(len(ids)==1 and ids[0]['ecu_id']=='2F12515306','BF identity')
require(len(samples)==end['samples_written']==120,'Full120sample count')
require(end['status']=='PASS_CAPTURE_ONLY' and end['error'] is None and end['cleanup_error'] is None,'Passive status and cleanup')
execution=read(O/'EXECUTION.json')
require(execution['process_exited'] and execution['exit_code']==0 and execution['bookkeeping_error'] is None,'Observer exited cleanly')
require(read(O/'POSTEXIT_CLIENT_CHECK.json')['pass'] is True,'No competing client/provider user after exit')
addresses={'FFFF4C75','FFFF4C8D','FFFF4CA1','FFFF4C50','FFFF4BC1','FFFF4BC2'}
for r in samples:
    require(set(r['raw_by_address'])==addresses,'Exact six-variable capture')
    require(r['provenance']['identity_ecu_id']=='2F12515306' and r['provenance']['physical_backend'] is True,'Physical sample provenance')
tx=re.findall(r'^TX .* raw=([0-9a-fA-F]+)$',(O/'capture.jsonl.provider.stderr.log').read_text(),re.M)
require(tx==['8010f001bf40']+['8010f014a800ff4c75ff4c8dff4ca1ff4c50ff4bc1ff4bc272']*120,'Only BF plus120fixedA8 transmitted')
g=read(A/'FINAL_GATE_STATE.json')
require(g['probe_invocation_count']==1 and g['passive_oem_return_invocations']==1 and g['physical_state']=='NORMAL MODE ON','Invocation/state bounds')
require([r['reply'] for r in g['completed_recovery_gates']]==['IGNITION OFF','NORMAL MODE ON'],'Simplified recovery gates')
require(g['final_physical'] in ('PASS','FAIL'),'Recorded physical identity outcome')
new_json(O/'GATE_STATE_AT_OEM_RETURN.json',g)
now=datetime.now(timezone.utc).isoformat()
result=dict(schema=1,created_utc=now,OEM_RETURN_AFTER_FINAL_TWO_PASS_128='PASS',session_id=g['session_id'],
    BF_identity='2F12515306',capture_status='PASS_CAPTURE_ONLY',samples=120,variables_per_sample=6,
    observer_exit_code=0,observer_cleanup_confirmed=True,broker_cleanup_confirmed=True,provider_cleanup_confirmed=True,
    cleanup_basis='Pinned capture/transport completed without cleanup errors, requiring broker CLOSE and worker exit0; post-exit process/module scan PASS.',
    wire_requests={'BF':1,'A8':120,'other':0},programming_session_requests=0,
    physical_probe_invocations=1,passive_return_invocations=1,further_physical_operations_allowed=False,
    battery_or_vehicle_power_loss_measured=False,physical_context='Operator-managed simplified ignition states; no numerical power-loss measurement claimed.',
    current_rom_attested_by_passive_check=False,current_rom_source='Preserved prior direct ECUFlash current.bin remains authoritative.',
    evidence=[pin(p) for p in sorted(O.iterdir()) if p.is_file()],validator=pin(Path(__file__)),
    final_physical_result=g['final_physical'], next_scope=('OFFLINE ONLY: run final raw-image comparison and integrity audit, then project completion checkpoint/tag.' if g['final_physical']=='PASS' else 'OFFLINE ONLY: exact first-divergence analysis; no retry or further physical attempt.'))
new_json(O/'OEM_RETURN_RESULT.json',result)
with (O/'OEM_RETURN_RESULT.md').open('x',encoding='utf-8',newline='\n') as f:
    f.write('# OEM return after bounded ROM-read probe\n\nOEM_RETURN_AFTER_FINAL_TWO_PASS_128 = PASS\n\n')
    f.write('After operator-confirmed IGNITION OFF then NORMAL MODE ON, the unchanged passive observer received BF identity2F12515306 and captured120 samples of the exact six reviewed variables. PASS_CAPTURE_ONLY, observer exit0 and clean broker/provider cleanup were confirmed. The wire log contains oneBF plus120A8 requests only.\n\n')
    f.write('The bounded ROM-read probe remains one invocation. No additional physical operation is allowed in this run. If final acquisition passed, work continues offline to the final raw comparison and integrity audit; after a failed bounded-read stage, only offline first-divergence analysis follows. Passive return does not attest every current-ROM byte or prove measured vehicle-side power loss.\n')
new_json(O/'MANIFEST.json',dict(status='SEALED_OEM_RETURN_AFTER_FINAL_TWO_PASS_128_PASS',files=[pin(p) for p in sorted(O.iterdir()) if p.is_file()]))
for p in O.iterdir():
    if p.is_file():p.chmod(0o444)
g.update(status='OEM_RETURN_PASS_OFFLINE_ONLY',OEM_RETURN_AFTER_FINAL_TWO_PASS_128='PASS',oem_return_after_final='PASS',
         oem_return_result=pin(O/'OEM_RETURN_RESULT.json'),next_gate=None,further_physical_activity_allowed=False,updated_utc=now)
(A/'FINAL_GATE_STATE.json').write_text(json.dumps(g,indent=2)+'\n',encoding='utf-8')
sp=Path(r'C:\Dev\A2WC511R_Final\state\CURRENT.json');s=read(sp)
s.update(phase='RK03_FINAL_TWO_PASS_128_OEM_RETURN_PASS',OEM_RETURN_AFTER_FINAL_TWO_PASS_128='PASS',
         final_oem_return_result=str(O/'OEM_RETURN_RESULT.json'),human_required=[],further_physical_activity_allowed=False,
         next_action=('Final raw comparison and integrity audit, then checkpoint/tag PROJECT COMPLETE' if g['final_physical']=='PASS' else 'Offline first-divergence analysis only; no retry'),updated_utc=now)
sp.write_text(json.dumps(s,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status='OEM_RETURN_AFTER_FINAL_TWO_PASS_128_PASS',samples=120,result=pin(O/'OEM_RETURN_RESULT.json'),next_scope='OFFLINE_ONLY')))
