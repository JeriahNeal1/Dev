"""Hash-link completed dynamic qualification; never edits frozen deliveries."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import collections,copy,datetime,hashlib,json
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/local/ecuflash_dynamic'

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def ref(relative):
    p=OUT/relative
    return {'path':str(p),'sha256':sha(p)}

def dump(path,value):path.write_text(json.dumps(value,indent=2)+'\n')

def main():
    prior_path=ROOT/'reports/local/prehardware/ENGINEERING_GATES.json'
    prior=json.loads(prior_path.read_text());gates=copy.deepcopy(prior)
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    gates.update(schema=5,updated_utc=now,phase='ECUFLASH_DYNAMIC_READ_CHARACTERIZED_EXACTNESS_REJECTED',
        previous_frozen_gates={'path':str(prior_path),'sha256':sha(prior_path)},
        next_rational_action='A_OFFLINE_LOSSLESS_ACQUISITION_AND_KERNEL_ENTRY_QUALIFICATION',
        B_connection_qualified=False,release_allowed=False,new_ECU_image_built=False,
        physical_actions_performed=False,real_provider_loaded=False)
    for gate in gates['gates']:
        gate['carried_from_frozen_prehardware']=True
        if gate['status']=='PHYSICAL/BENCH REQUIRED':gate['status']='PHYSICAL_REQUIRED'
    lookup={g['id']:g for g in gates['gates']}
    def put(identifier,status,scope,reason,evidence,remaining=None,depends=(),**extra):
        g={'id':identifier,'status':status,'scope':scope,'reason':reason,
           'evidence':[ref(e) for e in evidence],'remaining':remaining,'depends_on':list(depends),
           'carried_from_frozen_prehardware':False,**extra}
        if identifier in lookup:gates['gates'][gates['gates'].index(lookup[identifier])]=g
        else:gates['gates'].append(g)
        lookup[identifier]=g
    put('ECUFLASH_INSTALLED_KERNEL_IDENTITY','PASS','Exact captured installed Read object',
        '37 ordered RAM transfers reconstruct4660 bytes; independent decryptions, named installed resource and stock5AA5 checksum agree. Conditional stock entryFFFF3004/SPFFFFBFA0.',
        ['read_audit/BASELINE_CAPTURE_SUMMARY.json','read_audit/ENTRY_CHECKSUM_ADDENDUM.json','kernel_candidate/qualified_read_007/NATIVE_EXPORT.json'],
        'This proves selected bytes and bounded stock handoff only; actual ECU acceptance and startup context remain separate gates.')
    put('ECUFLASH_EXACT_READ_COVERAGE','FAIL','Unmodified installed Read for arbitrary1MiB flash',
        'Actual native Save replaces nonblank[86000,87000) withFF after a genuine CRC32 collision;37bytes differ despite SUCCESS. Historical gaps are conditionally read, not hard-masked.',
        ['read_audit/COVERAGE_COMPARISON.json','coverage_contract/HOST_COVERAGE_CONTRACT.json'],
        'Use a separately qualified lossless raw03 acquisition supplement or supported force-raw path. More ordinary fixtures cannot disprove the captured counterexample.',
        demonstrated_counterexample=True,expected_sha256='c777be6d9e0e3de2a1abc263a26c91ec2e1f421d09acb6fbe09c3ca81021180b',
        actual_sha256='4019b72614f525025acbc3cb34d2aa731711373b90f329ec006f60cc5800dc0d')
    put('ECUFLASH_READ_HOST_COMMAND_EXCLUSION','PASS','Captured successful and twelve fault host protocol traces only',
        'Every attempted ECU command classified; no erase/program/unlock/commit kernel20..25 command. Temporary RAM34/36/31 and session10 are explicit. Unsupported vendor service4 fails and is not disguised as ECU traffic.',
        ['read_audit/QUALIFICATION_COMPARISON.json','read_audit/FAULT_RETRY_CLEANUP.json'],
        'Does not establish kernel-internal controller effects, electrical behavior or every possible unobserved host failure path.')
    put('ECUFLASH_READ_FLASH_WRITE_EXCLUSION','CONDITIONAL','Combined host-command and kernel-execution contract',
        'Captured forbidden-command exclusion passes. Bounded read handlers exclude erase/program handlers; initial controller cleanup depends on incoming state and touches prohibitedE803 when selector zero. Physical/kernel-wide exclusion is not promoted from wire absence.',
        ['read_audit/QUALIFICATION_COMPARISON.json','kernel_candidate/qualified_read_007/READ_PATH_CONTRACT.json','kernel_candidate/handoff_scope/HANDOFF_SCOPE.json'],
        'Close the SH7058 startup context separately; retain actual hardware behavior as PHYSICAL_REQUIRED.',
        ('ECUFLASH_READ_HOST_COMMAND_EXCLUSION','ECUFLASH_KERNEL_STARTUP_CONTEXT'),software_wire_result='PASS',kernel_startup_result='UNQUALIFIED',physical_result='PHYSICAL_REQUIRED')
    put('ECUFLASH_KERNEL_STARTUP_CONTEXT','FAIL','SH7058 compatibility and inherited RAM before first kernel read',
        'Captured object does not initializeFFFF5444. Zero-selector startup performs zero stores toE800..E803;E803 is prohibited onSH7058. Actual selector lifetime and acceptable controller behavior are unproved.',
        ['kernel_candidate/handoff_scope/HANDOFF_SCOPE.json','kernel_candidate/qualified_read_007/READ_PATH_CONTRACT.json'],
        'Establish a supported complete entry contract or a qualified replacement acquisition kernel. Do not guess selector value or suppress the prohibited access.',
        physical_result='PHYSICAL_REQUIRED')
    put('ECUFLASH_HOST_FAILURE_CLEANUP','PASS','Observable installed host state machine under declared virtual faults',
        'Twelve one-shot faults and success paths captured; three-journal association complete. Six recover with exact images, six abort. All windows close normally; no re-upload or CPU-reset command.',
        ['read_audit/FAULT_RETRY_CLEANUP.json'],
        'Finite deliberately scoped transport failures characterize the captured cases, not all electrical faults or every possible application failure.')
    put('ECUFLASH_EXIT_RESET_CLEANUP','PHYSICAL_REQUIRED','Return to OEM ECU execution after temporary kernel',
        'Software behavior is now known: Disconnect/Close does not issue reset/exit, kernel04is constant0258, and success GUI asks for ignition off. OEM restart is not established.',
        ['read_audit/FAULT_RETRY_CLEANUP.json','kernel_candidate/qualified_read_007/READ_PATH_CONTRACT.json'],
        'Qualify physical power-off/reset, watchdog and OEM identity re-establishment after the startup/acquisition gates close.',
        software_observation_result='PASS',automatic_CPU_reset_sent=False)
    put('ECUFLASH_DETERMINISTIC_END_TO_END','PASS','Two clean installed-host processes with identical model inputs',
        'qualification_01/02 match normalizedTX, extractedkernel, full returned-byte ranges and native savedROM.14 baseline/fault journal joins complete; clock/pollcount differences remain explicit.',
        ['read_audit/QUALIFICATION_COMPARISON.json','read_audit/FAULT_RETRY_CLEANUP.json'],
        'These two baseline captures are byte-exact; this does not override CRC collision failure.')
    put('ECUFLASH_FAKE_PROVIDER_AND_ISOLATION','PASS','Process-local guarded fake boundary and scoped registry/AppData',
        'All14 native APIs implemented or explicitly refused;10,015-call stress and provider negative controls pass. Real DLL/executable/registrations unchanged. Built-in host requires reviewed in-memory redirect; normalgeneric enumeration unsupported.',
        ['provider_persistent_review/TEST_RESULTS.json','FINAL_PRESERVATION.json'],
        'Not a hostile-process sandbox or proof of actual OpenPort behavior. Earlier log-rotation incident is a separate preservation failure.')
    put('VIRTUAL_LOSSLESS_RAW_SUPPLEMENT','PASS','Fixed full-range command03 model readback, not a physical backend',
        '2048 ascending512-byte replies reconstruct exact1MiB and recover all37 hidden bytes; strict response/terminal checks and independent journal reconstruction pass.',
        ['raw_read_supplement/coverage_v2_04/RESULT.json','read_audit/RAW_SUPPLEMENT_REVIEW.json'],
        'Does not modify the installed Read result or establish hardware/kernel startup safety.')
    native_relative='native_raw_supplement/qualification_collision_native/RESULT.json'
    native=OUT/native_relative
    if native.exists():
        n=json.loads(native.read_text())
        put('NATIVE_FAKE_LOSSLESS_SUPPLEMENT','PASS' if n.get('status','').startswith('PASS') else 'FAIL',
            'Fixed readback through isolated native fake J2534 only',
            'Separate guarded fixed client exercises the same fake DLL boundary; original native Read image retained.',
            [native_relative,'native_raw_supplement/timeout_hardening_01/RESULT.json','final_review/NATIVE_SUPPLEMENT_INDEPENDENT_REVIEW.json'],
            'No real-provider binding, electrical acceptance or physical kernel execution claim.')
    put('ECUFLASH_PHYSICAL_ACCEPTANCE','PHYSICAL_REQUIRED','Electrical, OpenPort and actual ECU behavior',
        'No real provider or vehicle operation was performed; fake protocol and instruction tests are separated from silicon.',
        ['FINAL_PRESERVATION.json','kernel_candidate/handoff_scope/HANDOFF_SCOPE.json'],
        'Actual transport, current-ROM identity, ECU security/session acceptance, peripheral behavior, reset and OEM restart need the later qualified human session.')
    put('SINGLE_ACQUISITION_CONNECTION','FAIL','Connection not released',
        'Installed Read exactness has a concrete counterexample and SH7058 kernel startup remains unqualified. A virtual lossless supplement narrows the required change but does not close these gates.',
        ['read_audit/COVERAGE_COMPARISON.json','kernel_candidate/handoff_scope/HANDOFF_SCOPE.json','raw_read_supplement/coverage_v2_04/RESULT.json'],
        'Next task is the minimum lossless acquisition/entry contract, not additional residency searches or finite ordinary page tests.',
        ('LIVE_HOST_TRANSPORT_IMPLEMENTATION','ECUFLASH_INSTALLED_KERNEL_IDENTITY','ECUFLASH_EXACT_READ_COVERAGE','ECUFLASH_READ_FLASH_WRITE_EXCLUSION','ECUFLASH_KERNEL_STARTUP_CONTEXT','ECUFLASH_EXIT_RESET_CLEANUP'))
    put('FROZEN_ARTIFACT_PRESERVATION','PASS','Protected artifacts and real installation; not universal log preservation',
        '3090 sealed files verified including frozenM0/M06/M07, Diaphora, boot/read-only backend and canonical/damagedIDBs. RealDLL/executable/registry/settings unchanged.',
        ['FINAL_PRESERVATION.json'],None)
    put('HISTORICAL_ECUFLASH_LOG_PRESERVATION','FAIL','Early discovery AppData isolation incident',
        'ECUFlash rotated7original logs before Qt folder interception was complete;3exact originals recovered/restored and4remain unrecovered. Both historical Read logs restored. All subsequentRead runs isolated.',
        ['FINAL_PRESERVATION.json','SETUP_REPAIR_LOG.md'],
        'Retain incident and recovery evidence; do not claim universal preservation. Bounded recovery search exhausted.')
    gates['summary']={s:[g['id'] for g in gates['gates'] if g['status']==s]
                      for s in sorted({g['status'] for g in gates['gates']})}
    dump(OUT/'ENGINEERING_GATES.json',gates)
    summary={'schema':1,'updated_utc':now,'decision':'NO_SINGLE_ACQUISITION_CONNECTION',
        'next_rational_action':gates['next_rational_action'],
        'supported_observational_path':'EXISTING_HOST_NATIVE_FIXED_BF_A8',
        'installed_Read_experiment_complete':True,'installed_Read_unconditionally_exact':False,
        'native_provider_enumeration':'UNSUPPORTED_IN_INSTALLED_BUILD; HASH_PINNED_PROCESS_LOCAL_REDIRECT_USED',
        'kernel':{'sha256':'b0989858ec59c7c281c1368d956a7187b353454683b248be5f1739c86835b082','bytes':4660,
            'upload_range':['FFFF3000','FFFF4234'],'conditional_entry':'FFFF3004','conditional_SP':'FFFFBFA0','BE32_sum_low16':'5AA5'},
        'decisive_counterexample':{'range':['00086000','00087000'],'CRC32':'F154670A','lost_bytes':37,
            'host_reported_success':True,'raw_virtual_supplement_recovers':True},
        'minimum_remaining_acquisition_change':'Qualify fixed raw03 full-byte readback with a supported SH7058 kernel-entry/cleanup contract; the unchanged installed CRC-fill algorithm cannot satisfy universal exactness.',
        'single_smallest_remaining_offline_blocker':'Close DUAL1.07 SH7058 startup compatibility: actual incomingFFFF5444 value/lifetime at handoff and its zero-branch write to prohibitedFFFFE803. Native-fake fixed raw03 readback is already demonstrated.',
        'smallest_unclosed_startup_obligation':'IncomingFFFF5444 value/lifetime and the zero-branch prohibitedFFFFE803 write.',
        'physical_operations':False,'real_provider_loaded':False,'new_ECU_image_built':False,
        'ECU_resident_branch_frozen':True,'gate_counts':dict(collections.Counter(g['status'] for g in gates['gates'])),
        'evidence':{name:ref(path) for name,path in {
            'gates':'ENGINEERING_GATES.json','decision_report':'READ_QUALIFICATION.md',
            'repeatability':'read_audit/QUALIFICATION_COMPARISON.json','coverage':'read_audit/COVERAGE_COMPARISON.json',
            'faults':'read_audit/FAULT_RETRY_CLEANUP.json','kernel':'kernel_candidate/qualified_read_007/READ_PATH_CONTRACT.json',
            'entry':'kernel_candidate/handoff_scope/HANDOFF_SCOPE.json','preservation':'FINAL_PRESERVATION.json',
            'supplement':'raw_read_supplement/coverage_v2_04/RESULT.json'}.items()}}
    if native.exists():
        summary['evidence']['native_supplement']=ref(native_relative)
        summary['evidence']['native_runner_timeout']=ref('native_raw_supplement/timeout_hardening_01/RESULT.json')
    dump(OUT/'QUALIFICATION_SUMMARY.json',summary)
    print(json.dumps({'decision':summary['decision'],'gate_counts':summary['gate_counts'],'gates':str(OUT/'ENGINEERING_GATES.json')}))
if __name__=='__main__':main()
