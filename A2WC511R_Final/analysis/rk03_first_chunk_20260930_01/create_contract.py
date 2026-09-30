from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, re, stat

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'current_rom_20260930_01'
MODEL = Path(r'C:\Dev\A2WC511R_RK03_PostTransitionOffline')
REPO = Path(r'C:\Dev\A2WC511R_RK03_FirstChunkPhysical')

def pin(path, expected=None):
    path=Path(path); data=path.read_bytes(); sha=hashlib.sha256(data).hexdigest()
    if expected is not None and sha != expected: raise RuntimeError(str(path))
    return dict(path=str(path), bytes=len(data), sha256=sha)

old=json.loads((OLD/'PROBE_REVIEW_CONTRACT.json').read_text())
artifact=(MODEL/'continuation/src/owned_artifact.h').read_text()
cipher=bytes(int(x,16) for x in re.findall(r'0x([0-9a-fA-F]{2})',artifact.split('KERNEL_CIPHER[]=')[1]))[:128]
def frame(payload):
    b=bytes.fromhex('8010f0')+bytes([len(payload)])+payload
    return (b+bytes([sum(b)&255])).hex()
transfer=frame(bytes.fromhex('36ff3000')+cipher)
pins=[pin(HERE/'SUPERSESSION_STATUS.json','caae68da48de85c532de726fc24c1f6e2fc0e46e5980b3c5cd3b3bbe69a2e702'),
      pin(OLD/'run_completion_20260930_01/CONTINUATION_QUALIFICATION.json','a706de3800d855569403ac93724c55a8b4e7d1b1ea09bb04fb12fc66fa5259ac'),
      pin(OLD/'physical_probe_result/PHYSICAL_RESULT.json','acc41d5d8bbb499ab15805ef0b039a1602307ba8605bfdb90e91c4e73a929544'),
      pin(Path(r'C:\Dev\A2WC511R_RK03_TransitionProbe\physical_session\RK03_TRANSITION_PROBE_01\native_api.jsonl'),'57352963c842fa8cef0f45769a8c0f9613994df9c198fe434ee78e73d262a68b'),
      pin(OLD/'post83_oem_review/FIRST_BLOCK_REPLAY.json','23f1526b7a831d2034ea849c039ea5f2ad3b1fa295c942c410b89fb9aebd6967'),
      pin(MODEL/'continuation/src/fixtures.hpp'),pin(MODEL/'continuation/src/protocol.hpp'),pin(MODEL/'continuation/src/owned_artifact.h'),
      pin(Path(r'C:\Windows\SysWOW64\op20pt32.dll'),'f432084801762d919a3c31974616e097562424470003edc4f4fb843df34103cf')]
doc=dict(schema=1,created_utc=datetime.now(timezone.utc).isoformat(),status='REVIEW_CONTRACT_NOT_PHYSICAL_AUTHORIZATION',
  session_class='RK03_FIRST_CHUNK_ONLY', session_id='RK03_FIRST_CHUNK_01', session_path=str(REPO/'physical_session/RK03_FIRST_CHUNK_01'),
  maximum_physical_invocations=1,requires_exact_human_authorization='PROCEED RK03 FIRST CHUNK PROBE',
  physical_authorization_received=False,full_acquisition_allowed=False,automatic_retry_allowed=False,
  base_branch='rk03/post-transition-offline',base_commit='2a8eeee2a7ff251346314c54d6dd028f6df93766',
  build_branch='rk03/first-chunk-physical',
  expected_ecu_id='2f12515306',expected_81_response='80f01003c1ef8fc2',expected_83_response='80f01007c30000ff00ff0048',
  connect=old['connect'],set_config_order=old['set_config_order'],get_config=old['get_config'],filter=old['filter'],
  ordered_requests=[{'stage':i,'name':n,'wire_hex':w} for i,(n,w) in enumerate([
    ('BF','8010f001bf40'),('81','8010f0018102'),('8300','8010f002830005'),('2701','8010f0022701aa'),
    ('2702','DERIVED_FROM_EXACT_FOUR_BYTE_SEED_BY_PINNED_ALGORITHM'),('108502','8010f0031085021a'),
    ('34','8010f00834ff30000400071006'),('36',transfer)])],
  expected_ack_payloads={'2701':'6701 + exactly four seed bytes','2702':'670234','108502':'5085','34':'7484','36':'76'},
  fixed_transfer={'ram_address':'FFFF3000','address_wire_hex':'ff3000','length':128,'end_exclusive':'FFFF3080',
    'cipher_hex':cipher.hex(),'cipher_sha256':hashlib.sha256(cipher).hexdigest(),'frame_hex':transfer,
    'frame_sha256':hashlib.sha256(bytes.fromhex(transfer)).hexdigest(),
    'plaintext_sha256':'4f467e4371e66ff93b991f29c3081d9d78fdfafc58299acd3e3e0240b93da309',
    'source_kernel_sha256':'3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581',
    'download_declaration_size':1808,'embedded_payload_bytes':128,
    'declaration_note':'Retain reviewed 1808-byte declaration; send only first128 bytes. Never start or complete upload in this executable.'},
  ordered_post_key_actions=[{'wait_ms':200,'after':'validated key ACK'}, {'send':'108502'},
    {'wait_ms':100,'after':'validated session ACK'}, {'set_config':{'parameter':1,'value':15625}},
    {'ioctl':7,'name':'CLEAR_TX_BUFFER'}, {'ioctl':8,'name':'CLEAR_RX_BUFFER'},
    {'wait_ms':200,'before':'single34 declaration'}, {'send':'34','count':1}, {'send':'36','count':1}, {'require_ack':'76'}, {'action':'STOP_AND_CLEANUP'}],
  timing_contract='Exact requested durations200/100/200ms, minimum elapsed enforced with QPC on real clock; scheduler overshoot recorded. Virtual tests do not prove physical elapsed timing.',
  baud_evidence_limit='Reviewed SET_CONFIG return and object integrity checked. No GET_CONFIG baud claim or electrical waveform claim.',
  hard_exclusions=['second36','full kernel upload','kernel start','custom kernel execution','ROM read','flash erase','flash program','flash commit','arbitrary RAM address','external payload selection','automatic retry'],
  human_physical_states=['IGNITION OFF','TEST MODE ON','NORMAL MODE ON'],
  physical_gate_policy='Operator manages all battery/charger/voltage/adapter/Test Mode connector details. Exact new ignition confirmations and exact new software authorization required; earlier probe authorization is not reusable.',
  recovery='After one invocation, require IGNITION OFF then NORMAL MODE ON; only qualified passive BF/A8 OEM return, with BF2F12515306 PASS_CAPTURE_ONLY clean observer/broker/provider exit.',
  transport_constraints=[
    'Fixed eight-stage dispatch and no arbitrary send entrypoint; seed-derived key is the sole variable request content',
    'Exactly128 embedded cipher bytes; no full kernel bytes or payload file input',
    'Fixed provider path/hash; physical EXE/auth/reservation bound to session and review contract',
    'Native exclusive invocation marker before provider load; no retry after reservation or failure',
    'Offline CLI selects static fake provider and cannot load actual provider',
    'Validate all complete frames, metadata, checksums, request order, counts; any fault stops progression',
    'Log all received records before interpretation, including unexpected frames/statuses',
    'Attempt StopMsgFilter, Disconnect, Close in order after allocation even after journal failure; cleanup fault prevents PASS',
    'A failed36 may already have changed RAM: stock writes before trailing checksum validation; recovery is mandatory',
    'No test is permission to execute a full acquisition'],
  journal=old['journal'],
  qualification_requirements=['reuse127modelcases','exactsuccessfulphysicalBF81/83transcript','all16reviewedseedvectors','200/100/200virtualandrealclockfakechecks','baud15625thenTX7RX8','one34one36strict76','hardexclusionsreview','two byte-identical clean builds','independent review','hash-pinned qualification manifest'],
  reused_evidence=pins)
path=HERE/'FIRST_CHUNK_REVIEW_CONTRACT.json'
with path.open('x',encoding='utf-8',newline='\n') as f: json.dump(doc,f,indent=2); f.write('\n')
path.chmod(stat.S_IREAD)
print(json.dumps(pin(path)))
