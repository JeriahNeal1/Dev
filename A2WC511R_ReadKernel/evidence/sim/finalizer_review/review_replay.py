"""Independent parser negatives using real native03 wire bytes plus TEST metadata.

The added metadata is synthetic and is NEVER qualified as a native04 capture,
kernel execution, provider event, physical session or release fixture.
"""
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from host.finalize import replay_native as current
from host.protocol import sha256
def pin(p):return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
oldpath=HERE/'input_01/finalize.py'
spec=importlib.util.spec_from_file_location('review_prior_finalizer',oldpath)
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old);old.ROOT=ROOT
source=ROOT/'fake/runs/random_01/native_api.jsonl'
records=[json.loads(line) for line in source.read_text().splitlines()]
kernel=(ROOT/'build/attempt_03/kernel.bin').read_bytes();kh=sha256(kernel)
events=[]
for i,row in enumerate(records):
    message=row['function'] in ('PassThruWriteMsgs','PassThruReadMsgs')
    raw=bytes.fromhex(row['wire_hex'])
    events.append({**row,'protocol':3 if message else 0,'rx_status':0,'tx_flags':0,
      'timestamp':i if message else 0,'data_size':len(raw),'extra':0,
      'utc_filetime':134350000000000000+i*1000,'counter':i*1000,'frequency':10_000_000})
baseline,proof=current(events,kernel,kh,False)
run_report=json.loads((ROOT/'fake/runs/random_01/RESULT.json').read_text())
fixture=Path(run_report['fixture']['path']);assert sha256(fixture.read_bytes())==run_report['fixture']['sha256']
assert baseline.images[0]==baseline.images[1]==fixture.read_bytes()
cases=[]
for field,value in [('count',9),('protocol',99),('rx_status',4),('tx_flags',1),('timestamp',123),('extra',1)]:
    altered=events.copy();altered[0]={**altered[0],field:value}
    before,_=old.replay_native(altered,kernel,kh,False);assert before.status=='PASS'
    try:current(altered,kernel,kh,False)
    except ValueError as exc:cases.append({'case':'control_'+field,'prior':'INCORRECTLY_ACCEPTED','current':'REJECTED','reason':str(exc)})
    else:raise AssertionError('Control metadata still accepted: '+field)
def reject(name,rows,physical=False):
    try:current(rows,kernel,kh,physical)
    except (ValueError,KeyError) as exc:cases.append({'case':name,'current':'REJECTED','reason':str(exc)})
    else:raise AssertionError('Invalid replay accepted: '+name)
reject('partial_journal_missing_close',events[:-1])
reject('fake_flags_cannot_replay_as_physical',events,True)
changed=events.copy();changed[1]={**changed[1],'function':'PassThruSetProgrammingVoltage'}
reject('unexpected_API',changed)
rx=next(i for i,e in enumerate(events) if e['function']=='PassThruReadMsgs' and e['wire_hex'].startswith('beef020683'))
for name,offset in [('wrong_pass_valid_checksum',5),('wrong_address_valid_checksum',9)]:
    changed=events.copy();raw=bytearray.fromhex(changed[rx]['wire_hex']);raw[offset]^=1;raw[-1]=sum(raw[:-1])&255
    changed[rx]={**changed[rx],'wire_hex':raw.hex()};reject(name,changed)
changed=events.copy();changed[rx]={**changed[rx],'protocol':4};reject('unsupported_protocol',changed)
changed=events.copy();changed[rx]={**changed[rx],'rx_status':4};reject('unsupported_status',changed)
changed=events.copy();changed[rx]={**changed[rx],'extra':1};reject('unexpected_extra_data',changed)
# Current-ROM association is intentionally not derived from a virtual journal.
# The same bytes could be another consistent ROM fixture; root qualification
# checks its independently pinned fixture identity, not this integrity parser.
report={'schema':1,'status':'PASS','classification':'OFFLINE_SYNTHETIC_METADATA_PARSER_NEGATIVES_ONLY',
 'wire_bytes_source':pin(source),'test_metadata':'Locally generated canonical numeric fields; not native04 evidence',
 'prior_finalizer':pin(oldpath),'current_finalizer':pin(ROOT/'host/finalize.py'),
 'baseline_reconstructed_image_sha256':sha256(baseline.images[0]),'cases':cases,
 'physical_operations':0,'provider_loaded':False,
 'limitations':['No native04 or physical acquisition claim from this test fixture',
  'Full native04 journal positive review remains pending run completion',
  'Integrity-only finalization does not independently qualify which virtual fixture or physically associate an ECU']}
out=HERE/'REPLAY_REVIEW.json'
if out.exists():raise FileExistsError(out)
out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':'PASS','cases':len(cases),'report':str(out)}))
