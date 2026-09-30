from pathlib import Path
from datetime import datetime, timezone
import json

here=Path(__file__).resolve().parent
doc=dict(schema=1,session_id='RK03_FIRST_CHUNK_01',created_utc=datetime.now(timezone.utc).isoformat(),
    status='OFFLINE_QUALIFICATION_PENDING',qualification_sha256=None,probe_invocation_count=0,
    launch_reserved=False,commit_authorization=None,completed_pre_probe_gates=[],completed_recovery_gates=[],
    physical_state='UNCONFIRMED_FOR_NEW_SESSION',engine='UNCONFIRMED_FOR_NEW_SESSION',
    operator_managed_physical_context=True,full_acquisition_allowed=False,retry_allowed=False,abort_requested=False,
    first_chunk_physical='NOT_RUN',oem_return_after_first_chunk='NOT_RUN',next_gate=None,
    allowed_physical_states=['IGNITION OFF','TEST MODE ON','NORMAL MODE ON'],
    policy_reference=r'C:\Dev\A2WC511R_Final\analysis\current_rom_20260930_01\gate_policy_migrations\20260930T020401086019Z\OPERATOR_SIMPLIFIED_GATE_POLICY.json',
    historical_transition_pass=True,historical_oem_return_pass=True,
    historical_gates_or_authorizations_reusable=False)
with (here/'FIRST_CHUNK_GATE_STATE.json').open('x',encoding='utf-8',newline='\n') as f:
    json.dump(doc,f,indent=2);f.write('\n')
statepath=Path(r'C:\Dev\A2WC511R_Final\state\CURRENT.json')
state=json.loads(statepath.read_text(encoding='utf-8-sig'))
state.update(first_chunk_gate_state=str(here/'FIRST_CHUNK_GATE_STATE.json'),
    active_physical_gate_policy='OPERATOR_SIMPLIFIED_IGNITION_STATES_ONLY',
    first_chunk_contract=str(here/'FIRST_CHUNK_REVIEW_CONTRACT.json'),
    first_chunk_contract_sha256='a7482b0eba224c9642745b830c71b3fff14f987988a58cdc1376e45dc0aa839c',
    first_chunk_branch='rk03/first-chunk-physical',
    first_chunk_development_directory=r'C:\Dev\A2WC511R_RK03_FirstChunkPhysical',
    first_chunk_session=r'C:\Dev\A2WC511R_RK03_FirstChunkPhysical\physical_session\RK03_FIRST_CHUNK_01',
    updated_utc=datetime.now(timezone.utc).isoformat())
statepath.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
print('New first-chunk gate state initialized without carrying old authorization.')
