"""Assemble the completed local engineering work, retaining OPEN release gates."""
import argparse, datetime, hashlib, json, shutil
from pathlib import Path
from release_check import check, REQUIRED_REVIEWS

ROOT=Path('C:/Dev/Astra_A2WC511R')
SIM=Path('C:/Dev/A2WC511R_Sim')
BUILD=ROOT/'work/builds/m0_final_05'
REPEAT=ROOT/'work/builds/m0_final_repeat_06'
PATCH=ROOT/'work/patches/m0_final_05'
SOURCE=ROOT/'work/MerpMod_M0/MerpMod/DiagnosticM0'
BASELINE=Path('C:/Dev/SubaruRoms/OEM/A2WC511R.bin')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,obj):p.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')

def package(out):
    assert not out.exists(), 'A review package must use a fresh path'
    build=json.loads((BUILD/'manifest.json').read_text())
    review=json.loads((ROOT/'reports/local/build/final_build_review.json').read_text())
    patch=json.loads((PATCH/'roundtrip_review.json').read_text())
    assert review['result']=='PASS' and patch['production_release_allowed'] is False
    assert sha(BASELINE)==patch['input_baseline_sha256']
    assert sha(BUILD/'manifest.json')==patch['build_manifest_sha256']
    for name,digest in build['sources'].items():assert sha(SOURCE/name)==digest, name
    for name,digest in build['artifacts'].items():assert sha(BUILD/name)==digest, name
    for name,digest in patch['output_hashes'].items():assert sha(PATCH/name)==digest, name
    out.mkdir(parents=True)
    def copy(p,rel):
        dest=out/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    copy(BASELINE,'artifacts/A2WC511R.analysis_baseline.bin')
    names=['A2WC511R.M0.EXPERIMENTAL_UNAPPROVED.raw.bin',
           'A2WC511R.M0.EXPERIMENTAL_UNAPPROVED.checksum_corrected.bin',
           'A2WC511R.M0.EXPERIMENTAL.v1.patch','A2WC511R_M0.EXPERIMENTAL.logger.fragment.xml']
    for name in names:copy(PATCH/name,'artifacts/'+name)
    copy(BUILD/'A2WC511R_DiagnosticM0.EXPERIMENTAL_UNAPPROVED.elf','artifacts/A2WC511R_DiagnosticM0.EXPERIMENTAL_UNAPPROVED.elf')
    for p in SOURCE.iterdir():
        if p.is_file():copy(p,'source/DiagnosticM0/'+p.name)
    copy(Path('C:/Dev/MerpMod/LICENSE.md'),'source/MerpMod_LICENSE.md')
    for name in ('MerpMod_M0_source.patch','SharpTune_offline_source.patch','build_sharptune.py'):
        copy(ROOT/'reports/local/build'/name,'source/'+name)
    for name in ('project_core.py','release_check.py','ida_vendor_client.py','package_experimental_run.py'):
        copy(ROOT/'tools'/name,'tools/'+name)
    shutil.copytree(BUILD,out/'validation/final_build')
    shutil.copytree(REPEAT,out/'validation/repeat_build')
    shutil.copytree(PATCH,out/'validation/patch')
    shutil.copytree(ROOT/'reports/local',out/'validation/local')
    for p in SIM.iterdir():
        if p.is_file():copy(p,'simulator/'+p.name)
    shutil.copytree(SIM/'tests',out/'simulator/tests',ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(SIM/'runs',out/'simulator/runs')
    copy(ROOT/'config/host_paths.json','provenance/host_paths.json')
    copy(ROOT/'state/SYMBOLS.json','provenance/SYMBOLS.json')
    copy(ROOT/'state/RUN_CONTRACT.md','provenance/RUN_CONTRACT.md')
    copy(ROOT/'reports/dev_snapshot/dev_audit.json','provenance/uploaded_dev_audit.json')
    raw=out/'artifacts'/names[0];corrected=out/'artifacts'/names[1]
    x=BASELINE.read_bytes();y=corrected.read_bytes()
    corrected_count=sum(a!=b for a,b in zip(x,y))
    blockers={
      'ROM_OWNERSHIP':{'depends_on':[],'status':'OPEN','required':'Exclusive runtime ownership of exact [E1000,E1364), including indirect readers, vectors/checksum and boot paths.'},
      'RAM_OWNERSHIP':{'depends_on':[],'status':'OPEN','required':'Exclusive lifetime ownership of [FFFF7400,FFFF7420), including indirect/bulk/DMA accesses; reset DMA is known to cross it.'},
      'TASK_STACK_TIMING':{'depends_on':['RAM_OWNERSHIP'],'status':'OPEN','required':'Task9/6580 ->11134 ->1193A stack/ISR nesting and reentrancy/cadence budget; added124-byte frame and instruction counts alone do not prove headroom.'},
      'CURRENT_CALIBRATION':{'depends_on':[],'status':'OPEN','required':'Human-confirmed currently flashed read-back identity and compatibility review for actual VF52/3-port/3-inch MAF hardware. Known local filenames do not establish current installation.'},
      'PHYSICAL_TEST_CANDIDATE':{'depends_on':['ROM_OWNERSHIP','RAM_OWNERSHIP','TASK_STACK_TIMING','CURRENT_CALIBRATION'],'status':'BLOCKED','required':'Review one precisely hashed candidate after all engineering prerequisites close.'},
      'VEHICLE_VALIDATED':{'depends_on':['PHYSICAL_TEST_CANDIDATE'],'status':'NOT_RUN','required':'Human-controlled testing and measured results; none invented here.'}}
    gate={'schema':1,'status':'COMPILED_EXPERIMENTAL_NOT_RELEASED','build_complete':True,
          'offline_reviewed_candidate':False,'production_release_allowed':False,'physical_validation':False,
          'session_id':'01a0da26-addc-7fe1-84df-8c0baa8174f8','blockers':blockers}
    dump(out/'ENGINEERING_GATES.json',gate)
    (out/'HUMAN_REVIEW.md').write_text('''# Human review and eventual test procedure

This package is an experimental engineering result, not a physical-test release. No flash, Test Write, erase, CAN injection or vehicle command was executed. The stock analysis baseline must not replace the car's hardware-specific tune.

The immediate human information needed for a later physical candidate is the exact currently flashed calibration identity, supported by a preserved operator-obtained read-back/hash and its installed-hardware context. Existing local REV3/adjusted files have been found and hashed; their filenames cannot establish current ECU state. No repeated normal-drive gear experiment is requested. There is no short human action that substitutes for the outstanding ROM/RAM/stack engineering proof.

The remaining optional RomRaider interface acceptance is one positively approved disposable batch and one canceled batch, visible table/alias/compare/undo inspection, and reopening an exported disposable copy. The native model, rollback, quantization, stale-state and checksum tests already passed. Retain the bridge's actual local confirmation. This GUI exercise is unrelated to vehicle validation and need not touch a real tune.

After the engineering gates close: review a separately identified candidate built on the confirmed compatible calibration; preserve independent known-good originals, IDB and vehicle read-back; have the human establish the appropriate vendor connection, power and recovery procedure before deciding whether to write. This document does not approve writing the included baseline-derived binary. First measurement should verify OEM behavior and diagnostic publication without enabling any active outputs. Record exact input/output hashes and observed values. Physical operations remain with the human.

Expected diagnostic properties: raw source/snapshot/latch/status are observations; freshness remains0 UNKNOWN; rejection reasons always retain freshness/coherence uncertainty in the hardware binding; samples and sequence count observer work, not received CAN frames. Observer decoded fields reconstruct previous observer samples and may differ from OEM retained values on the first invalid nibble. The individual logger fragment does not itself execute the aggregate sequence-before/after consistency protocol.

Abort any eventual test on unexpected OEM behavior, communication loss, reset/watchdog indications, inconsistent publication or departure from the reviewed calibration; do not infer safe continued operation from a diagnostic counter. Recovery uses the operator's independently verified compatible backup and approved vendor procedure. No timing, physical engagement, combustion, emissions-control or transmission-hydraulic validation is claimed by these software tests.
''',encoding='utf-8')
    texts={
      'baseline_provenance':f'Analysis baseline SHA256 {sha(BASELINE)}. Local ROM, uploaded archive audit and IDB stamp variant were separately reconciled. IDB SHA a34c4ce8238bf28bdc18c191bbe73b2179130aa9846e952a6fa332bae442de96 differs only atFFC4C..FFC4F. See validation/local/ida and provenance/uploaded_dev_audit.json. This is not independent manufacturer provenance or a current-flash attestation.',
      'calibration_compatibility':'OPEN. The actual hardware-specific current ECU calibration is unconfirmed. Local Desktop ROMs and C:/Tuning logs were found and hashed in validation/local/interfaces/local_inventory.json. Stock baseline is for offline analysis; it is not a recommended running-car tune for the VF52/3-port/3-inch MAF setup.',
      'rom_allocation':'OPEN. Final section is [E1000,E1364),868 bytes; ELF/read-only section and exact full-image diff are verified. FF content and absent exact references do not prove ownership. See validation/local/ABI_ALLOCATION_REVIEW.md and independent review; this exact provisional interval is withheld from physical approval.',
      'ram_allocation':'OPEN. State is32 bytes at provisional[FFFF7400,FFFF7420). Actual reset DMA crosses this range. Runtime indirect/DMA lifetime ownership is not established. Task/runtime stacks differ from reset SP; no live RAM write or probing was performed. See validation/local/ABI_ALLOCATION_REVIEW.md.',
      'hook_abi_and_timing':'Partial PASS; timing/stack/reentrancy OPEN. Pool11ADC changes000147AC to000E12DC. Caller1193A/1193C/1193E returns11940. OEM decoder executes first. Differential evidence compares GPR/SR/MAC/PR and OEM writes; compiled closure is integer-only. Added stack124 bytes plus8 surrounding saved-PR bytes is not whole-task headroom. RTOS slot9/6580 ->11134 identified. See simulator runs and validation/local/ABI_ALLOCATION_REVIEW.md.',
      'feature_closure':'PASS for this compiled closure. Only Diagnostic, Bindings, Identifier and DecoderHook are linked. No active MerpMod timing/fueling/MAF/WGDC/rev-limit/torque-intervention module or hook is linked. Raw memory reads and provisional diagnostic-state writes are the new behavior; OEM decoder writes remain. Freshness always UNKNOWN and coherence remains unproven. Initialization publication and exact reader/single-writer limitations are documented in source and patch review.',
      'checksum_verification':f'PASS offline arithmetic/round-trip. Native installed RomRaider and independent Python agree: tableFFB80, active descriptor sums32-bit BE words over[2000,FFAF8), correctionFFB88 equals5AA5A55A minus sum modulo2^32. RawSHA {sha(raw)} intentionally has an invalid changed checksum; correctedSHA {sha(corrected)} is valid. Raw remove returns exact baseline; corrected remove plus checksum normalization returns exact baseline. No edit stamp added/normalized. See validation/patch/roundtrip_review.json and native final checksum audit.',
      'reproducible_build':'PASS. Final05 and repeat06 fresh output trees have bit-identical ELF, objects, assembly, stack-usage and code payload without functional normalization. Only linker-map absolute output directory prefixes differ. Sources/tools/flags/commands are pinned in validation/final_build/manifest.json. Build CLI rejects dirty payload/source associations and fails native command errors. SharpTuneRC2-12 source was built side-by-side; private offline hardening diffs and original RC2-10 provenance are retained.',
      'human_test_plan':'NOT_RUN/NOT_RELEASED. Read HUMAN_REVIEW.md and ENGINEERING_GATES.json. Physical testing depends on ROM/RAM ownership, real task-stack/timing and compatible current-calibration identity. The included binary is experimental. No vehicle operation, live writes or physical validation was performed.'}
    (out/'reviews').mkdir()
    for key,body in texts.items():(out/'reviews'/f'{key}.md').write_text(f'# {key}\n\n{body}\n',encoding='utf-8')
    manifest={'schema':1,'target_calid':'A2WC511R','target_ecuid':'2F12515306','scope':'diagnostic_only',
      'status':'EXPERIMENTAL_NOT_RELEASED','production_release_allowed':False,
      'baseline':{'path':'artifacts/A2WC511R.analysis_baseline.bin','sha256':sha(BASELINE)},
      'candidate':{'path':'artifacts/'+names[1],'sha256':sha(corrected)},
      'expected_output_identity':{'calid':'A2WC511R','ecuid':'2F12515306'},'allowed_changes':[],
      'reviews':{k:{'path':f'reviews/{k}.md','sha256':sha(out/'reviews'/f'{k}.md')} for k in REQUIRED_REVIEWS}}
    for lo,hi,key,purpose in [(0x11adc,0x11ae0,'hook_abi_and_timing','Experimental OEM-first decoder pointer'),
       (0xe1000,0xe1364,'rom_allocation','Experimental diagnostic payload; ownership gate OPEN'),
       (0xffb88,0xffb8c,'checksum_verification','Native-matched checksum correction')]:
        manifest['allowed_changes'].append({'start':hex(lo),'end_exclusive':hex(hi),'review_key':key,
            'purpose':purpose,'baseline_range_sha256':hashlib.sha256(x[lo:hi]).hexdigest()})
    dump(out/'release_envelope_manifest.json',manifest)
    envelope=check(manifest,out)
    dump(out/'ENVELOPE_CHECK.json',envelope)
    assert envelope['envelope_passed'], envelope
    (out/'README.md').write_text(f'''# A2WC511R diagnostic M0 — compiled experimental package

**COMPILED; NOT RELEASED FOR FLASH.** This run completed an actual A2WC511R/2F12515306/AUTO_TRANS1 SH-2E diagnostic integration and reproducible engineering package. Allocation, task-stack/timing and current-calibration gates remain open. `ENGINEERING_GATES.json` is authoritative for release status; a passing evidence-envelope check is not engineering acceptance.

Final source/build: `source/DiagnosticM0`, `validation/final_build` (m0_final_05) and `validation/repeat_build` (m0_final_repeat_06). GNU SH13.01/GCC4.7 uses -m2e -mb -mrenesas -mieee and assembler --isa=sh2e. The module is868 bytes at provisional[E1000,E1364), with32-byte state at provisional[FFFF7400,FFFF7420). It retains the OEM decoder and adds observations/rejection reasons only. No performance-control feature is linked.

| Artifact | SHA256 |
|---|---|
| Analysis baseline | `{sha(BASELINE)}` |
| Raw experimental image | `{sha(raw)}` |
| Checksum-corrected experimental image | `{sha(corrected)}` |
| Strict SharpTune patch | `{sha(out/'artifacts'/names[2])}` |

Both images are1,048,576 bytes. The raw image changes859 bytes within the single hook and diagnostic code span; the corrected image changes{corrected_count} bytes including the checksum word. Raw patch removal returns the exact baseline. Corrected removal followed by the documented checksum normalization returns the exact baseline. The editor stamp remains unchanged. Raw has the expected invalid checksum; the separately named corrected image has a native-matched valid checksum. Neither is physically validated.

Validation includes64 handoff tests,461059 actual host-compiled C checks, native RomRaider acceptance, independent ELF/patch review and actual-ROM SH-2E differential execution. Exact counts, cases, input hashes and coverage limitations are in `validation/local`, `validation/patch` and `simulator/runs`. The initial31-test simulator suite exercises51 supported instruction forms;1,792 stock decoder cases and256 status cases cover both anchors. Compiled differential tests cover1,024 paired cases plus initialization/publication and changed-read scenarios. Unsupported instructions/peripherals fail explicitly. No full engine, TCU, DMA or timing simulation is claimed.

Read `validation/local/ABI_ALLOCATION_REVIEW.md`, `validation/local/interfaces/INDEPENDENT_PORT_REVIEW.md`, the nine `reviews` documents, and `HUMAN_REVIEW.md`. The remaining dependency graph names what is technically unresolved and which human information is needed. The optional native editor confirmation/display workflow remains unperformed; no confirmation was bypassed in RomRaider.

Reproduction on this pinned C:/Dev host uses the exact scripts and recorded argument arrays in `validation/final_build/manifest.json`, `source/DiagnosticM0/build.py` and `experimental_roundtrip.py`. Use fresh output paths. The patch driver deliberately requires the known baseline hash, source/ELF/payload associations and isolated hardened SharpTune tool; do not remove those guards. Source diffs and SharpTune build provenance are included. Compiler/license installations are referenced by hash rather than redistributed. `simulator/README.md` contains its replay commands and scope.

Session:01a0da26-addc-7fe1-84df-8c0baa8174f8. User programs/tunes were preserved; the existing IDB was backed up, analyzed, saved and closed through official Hex-Rays MCP. No ECU/TCU flash, live memory write, CAN injection or vehicle command occurred. All delivered hashes are listed in `SHA256SUMS.json`.
''',encoding='utf-8')
    dump(out/'SHA256SUMS.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
       'files':{str(p.relative_to(out)).replace('\\','/'):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}})
    print(json.dumps({'package':str(out),'status':gate['status'],'envelope_passed':True,
        'corrected_sha256':sha(corrected),'files':sum(p.is_file() for p in out.rglob('*'))}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    package(p.parse_args().output.resolve())
