"""Independent finalizer file/race negatives, confined to synthetic review dirs."""
import contextlib,io,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from host import finalize as current
scope={'__file__':str(HERE/'review_read_race.py')}
prefix=(HERE/'review_read_race.py').read_text().split('\nspec=')[0]
exec(compile(prefix,str(HERE/'review_read_race.py'),'exec'),scope)
build,pin=scope['build_fixture'],scope['pin'];cases=[]
def reject(label,folder,expected):
    try:
        with contextlib.redirect_stdout(io.StringIO()):current.finalize('native_04',folder,False)
    except ValueError as exc:
        assert expected in str(exc),(label,str(exc))
        assert not (folder/'finalized').exists()
        cases.append({'case':label,'status':'PASS','outcome':'REJECTED_BEFORE_PUBLICATION','reason':str(exc)})
    else:raise AssertionError('Invalid file set accepted: '+label)
folder=build(HERE/'SYNTHETIC_PARTIAL_02');p=folder/'pass1.partial.bin';p.write_bytes(p.read_bytes()[:-1])
reject('partial_raw_pass',folder,'Raw file not exactly')
folder=build(HERE/'SYNTHETIC_WRONG_RAW_02');p=folder/'pass1.partial.bin';raw=bytearray(p.read_bytes());raw[0]^=1;p.write_bytes(raw)
reject('wrong_raw_pass',folder,'Raw file not exactly')
folder=build(HERE/'SYNTHETIC_WRONG_EXE_02');p=folder/'owned_read32.exe';raw=bytearray(p.read_bytes());raw[0]^=1;p.write_bytes(raw)
reject('wrong_capture_executable',folder,'Capture executable differs')
folder=build(HERE/'SYNTHETIC_EARLY_RACE_02');original_check=current.require_sources_unchanged
def early_change(sources):
    (folder/'native_api.jsonl').write_text('{"corrupted_before_publication":true}\n')
    return original_check(sources)
current.require_sources_unchanged=early_change
reject('journal_changed_before_publication',folder,'changed')
current.require_sources_unchanged=original_check
folder=build(HERE/'SYNTHETIC_LATE_RACE_02');journal=folder/'native_api.jsonl';before=pin(journal)
original_record=current.record;triggered=False
def late_change(path,data=None):
    global triggered
    if not triggered and Path(path).name=='raw_pass0.bin':
        journal.write_text('{"corrupted_after_validation":true}\n');triggered=True
    return original_record(path,data)
current.record=late_change
with contextlib.redirect_stdout(io.StringIO()):result=current.finalize('native_04',folder,False)
current.record=original_record
assert triggered and result['status']=='PASS_RAW_CAPTURE_INTEGRITY'
assert result['native_journal']==before and result['native_journal']['sha256']!=pin(journal)['sha256']
assert result['physical_session_association_proven'] is False and result['current_ROM_identified'] is False
cases.append({'case':'mutation_after_prepublication_check','status':'PASS',
  'outcome':'REPORT_RETAINS_EXACT_PREVIOUSLY_VALIDATED_HASH_NOT_REPLACEMENT_HASH',
  'reported_journal':result['native_journal'],'later_source':pin(journal),
  'scope':'Later alteration is detected by downstream hash verification; no claim files cannot change after checking.'})
report={'schema':1,'status':'PASS','classification':'SYNTHETIC_FINALIZER_FILE_AND_READ_RACE_TESTS_ONLY',
  'current_finalizer':pin(ROOT/'host/finalize.py'),'source':pin(Path(__file__)),
  'cases':cases,'physical_operations':0,'provider_loaded':False,
  'not_evidence_of':['native04 execution','physical acquisition','current ECU ROM']}
out=HERE/'FILE_RETEST.json'
if out.exists():raise FileExistsError(out)
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'PASS','cases':len(cases),'report':str(out)}))
