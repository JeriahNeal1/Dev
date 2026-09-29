"""Counterexample using synthetic review inputs only, never a live capture."""
import contextlib,hashlib,importlib.util,io,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
def pin(p):return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def build_fixture(folder):
    folder.mkdir(exist_ok=False)
    source=ROOT/'fake/runs/random_01'
    events=[]
    for i,line in enumerate((source/'native_api.jsonl').read_text().splitlines()):
        row=json.loads(line);message=row['function'] in ('PassThruWriteMsgs','PassThruReadMsgs')
        raw=bytes.fromhex(row['wire_hex'])
        events.append({**row,'protocol':3 if message else 0,'rx_status':0,'tx_flags':0,
          'timestamp':i if message else 0,'data_size':len(raw),'extra':0,
          'utc_filetime':134350000000000000+i*1000,'counter':i*1000,'frequency':10_000_000})
    (folder/'native_api.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
    (folder/'native.log').write_text('SYNTHETIC REVIEW FIXTURE ONLY\nPASS_NATIVE_FAKE_TWO_FULL_READS\n')
    (folder/'owned_read32.exe').write_bytes((ROOT/'host/build/native_04/owned_read32.exe').read_bytes())
    for n in (0,1):(folder/f'pass{n}.partial.bin').write_bytes((source/f'pass{n}.partial.bin').read_bytes())
    (folder/'SYNTHETIC_REVIEW_ONLY.txt').write_text('Never native04 execution evidence, a provider capture, or current ECU ROM. Native03 bytes and fabricated test metadata exercise only local file validation.\n')
    return folder

spec=importlib.util.spec_from_file_location('review_prior_finalizer_race',HERE/'input_01/finalize.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old);old.ROOT=ROOT
folder=build_fixture(HERE/'SYNTHETIC_RACE_01');journal=folder/'native_api.jsonl'
before=pin(journal);original_record=old.record;triggered=False
def mutate_before_reporting(path):
    global triggered
    if not triggered and Path(path).name=='raw_pass0.bin':
        journal.write_text('{"corrupted_after_replay":true}\n');triggered=True
    return original_record(path)
old.record=mutate_before_reporting
with contextlib.redirect_stdout(io.StringIO()):result=old.finalize('native_04',folder,False)
assert triggered and result['status']=='PASS_RAW_CAPTURE_INTEGRITY'
assert result['native_journal']['sha256']!=before['sha256']
report={'schema':1,'status':'FINDING_REPRODUCED','classification':'SYNTHETIC_INPUT_READ_RACE_ONLY',
 'reviewed_finalizer':pin(HERE/'input_01/finalize.py'),'validated_journal_before':before,
 'reported_journal_after':result['native_journal'],'wrongly_accepted_result':result['status'],
 'reason':'Proof uses earlier journal bytes; report hashes later replaced invalid bytes, with no revalidation.',
 'fixture':str(folder),'physical_operations':0,'provider_loaded':False,
 'not_evidence_of':['native04 execution','physical acquisition','current ECU ROM']}
out=HERE/'READ_RACE_REVIEW.json'
if out.exists():raise FileExistsError(out)
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
