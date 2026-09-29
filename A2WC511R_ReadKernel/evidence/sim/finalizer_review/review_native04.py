"""Independent actual native04 journal replay and semantic metadata negatives."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from host.finalize import replay_native
def pin(p):return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
folder=ROOT/'fake/runs/composite_native04'
report=json.loads((folder/'RESULT.json').read_text());binding=report['binding']
assert report['status']=='PASS_NATIVE_FAKE_COMPILED_KERNEL_TWO_FULL_READS' and report['physical'] is False
for path,expected in [(folder/'owned_read32.exe',binding['client_sha256']),
 (Path(binding['client_path']),binding['client_sha256']),
 (Path(binding['kernel_path']),binding['kernel_sha256']),
 (Path(binding['manifest_path']),binding['manifest_sha256'])]:assert pin(path)['sha256']==expected
kernel=Path(binding['kernel_path']).read_bytes()
events=[json.loads(line) for line in (folder/'native_api.jsonl').read_text().splitlines()]
host,proof=replay_native(events,kernel,binding['kernel_sha256'],False)
fixture=Path(report['fixture']['path']);assert pin(fixture)['sha256']==report['fixture']['sha256']
assert host.images[0]==host.images[1]==fixture.read_bytes()
for n in (0,1):assert (folder/f'pass{n}.partial.bin').read_bytes()==host.images[n]
checks=[]
def reject(name,rows,expected=None,physical=False):
    try:replay_native(rows,kernel,binding['kernel_sha256'],physical)
    except (ValueError,KeyError) as exc:
        if expected:assert expected in str(exc),(name,str(exc))
        checks.append({'case':name,'status':'PASS','observed':'REJECTED','reason':str(exc)})
    else:raise AssertionError('Invalid journal accepted: '+name)
reject('actual_fake_journal_cannot_be_physical',events,physical=True)
reject('actual_complete_read_without_terminal_close',events[:-1],'fixed API step')
for field,value in [('count',9),('protocol',99),('rx_status',4),('tx_flags',1),('timestamp',123),('extra',1)]:
    changed=events.copy();changed[0]={**changed[0],field:value}
    reject('forged_control_'+field,changed,'zero message shape')
changed=events.copy();changed[1]={**changed[1],'function':'PassThruSetProgrammingVoltage'}
reject('forbidden_API',changed,'fixed API step')
tx=next(i for i,e in enumerate(events) if e['function']=='PassThruWriteMsgs' and e['wire_hex'].startswith('beef00080300'))
segments=[];raw=bytearray()
for i in range(tx+1,len(events)):
    e=events[i]
    if e['function']!='PassThruReadMsgs':break
    if e['rx_status']==0:
        data=bytes.fromhex(e['wire_hex']);segments.append((i,len(raw),len(raw)+len(data)));raw.extend(data)
assert len(raw)==523 and raw[:6]==bytes.fromhex('beef02068300')
for name,position in [('wrong_pass_with_correct_checksum',5),('wrong_address_with_correct_checksum',9)]:
    replacement=bytearray(raw);replacement[position]^=1;replacement[-1]=sum(replacement[:-1])&255
    changed=events.copy()
    for i,a,b in segments:changed[i]={**changed[i],'wire_hex':replacement[a:b].hex()}
    reject(name,changed,'Wrong read length/opcode/pass/address')
changed=events.copy();i=segments[0][0];changed[i]={**changed[i],'rx_status':4}
reject('unsupported_RX_status',changed)
# Independently verify the claimed native03 -> native04 change boundary.
transition=json.loads((ROOT/'host/build/native_04/SOURCE_TRANSITION.json').read_text())
old_path=Path(transition['old_source']['path']);new_path=Path(transition['new_source']['path'])
assert pin(old_path)['sha256']==transition['old_source']['sha256']
assert pin(new_path)['sha256']==transition['new_source']['sha256']
def without_logger(text):
    a=text.index('static void log_api(');b=text.index('#define FN(',a)
    return text[:a]+text[b:]
assert without_logger(old_path.read_text())==without_logger(new_path.read_text())
outcome={'schema':1,'status':'PASS','classification':'ACTUAL_NATIVE04_JOURNAL_INDEPENDENT_OFFLINE_REPLAY',
 'input_report':pin(folder/'RESULT.json'),'native_journal':pin(folder/'native_api.jsonl'),
 'finalizer':pin(ROOT/'host/finalize.py'),'preserved_finalizer':pin(HERE/'input_03/finalize.py'),
 'kernel_sha256':binding['kernel_sha256'],'native_client_sha256':binding['client_sha256'],
 'fixture':pin(fixture),'replayed_passes':[{'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()} for b in host.images],
 'positive_replay':proof,'negative_controls':checks,'native_source_transition':'EXACT_OUTSIDE_LOG_API',
 'physical_session_association_proven':False,'current_ROM_identified':False,'provider_loaded':False,
 'physical_operations':0,'transport_calls':0,
 'scope':['Recorded bytes and API names/zero message shape are independently checked',
  'Native source/binary supply fixed non-message arguments; journal does not independently record every IOCTL/filter/connection argument',
  'UTC/QPC metadata retained, not proof of silicon or exact host frame deadline timing',
  'Virtual fixture identity is independently checked here; raw-capture finalizer alone attests integrity only']}
assert outcome['finalizer']['sha256']==outcome['preserved_finalizer']['sha256']
p=HERE/'NATIVE04_REVIEW.json'
if p.exists():raise FileExistsError(p)
p.write_text(json.dumps(outcome,indent=2)+'\n');print(json.dumps({'status':'PASS','controls':len(checks),'report':str(p)}))
