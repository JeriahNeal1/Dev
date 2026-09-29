"""Runs inside official IDA MCP after backed-up, hash-pinned read-only proofs."""
import json,hashlib
from pathlib import Path
import ida_bytes,ida_name,ida_ua,idc
OUT=Path('C:/Dev/Astra_A2WC511R/reports/local/gate_closure/ida')
assert hashlib.sha256(ida_bytes.get_bytes(0,0x100000)).hexdigest()=='a34c4ce8238bf28bdc18c191bbe73b2179130aa9846e952a6fa332bae442de96'
assert hashlib.sha256(Path('C:/Dev/Astra_A2WC511R/backups/gate_closure_20260925/idb/A2WC511R_STOCK_ROMRAIDER.bin.i64').read_bytes()).hexdigest()=='2ec93dadb56be292a91ce6ee7060dcc4ab63d0ca457fb1138ab4b96afc766547'
assert json.loads((OUT.parent/'rom/routine_regression.json').read_text())['pass']
changes=[]
for ea,expected,comment in [
 (0x7A79C,'d220','Verified PC-relative load of exclusive calibration-scan bound CE754 from7A820. Routine7A77C reads halfwords[C0034,CE754); controlled simulator first/middle/last128-word scenarios and wrong-bound negative control PASS. This excludes the FF hole for this reader only; not ROM ownership.'),
 (0xF75E,'62e6','Verified additive checksum inner loop: uint32 BE load@r14++, sum r12 in BF/S delay slot. Descriptor0 [2000,FFAF7] results in reads[2000,FFAF8), INCLUDING proposed M0 ROM region. Tests stock/payload/boundary chunks PASS; checksum correction required. No full peripheral/reset simulation claimed.'),
 (0xFA84,'e703','Verified checksum range validator: start aligned4; start<=end; end mod4==3 OR start==end. Seven boundary cases executed on original opcodes PASS. See gate_closure/rom/routine_regression.json.')]:
    actual=ida_bytes.get_bytes(ea,2).hex()
    # First pass exports expected bytes explicitly and fails before any metadata if mismatched.
    if actual!=expected:raise AssertionError((hex(ea),actual,expected))
for ea,comment in [
 (0x7A79C,'Verified exclusive calibration-scan bound CE754 (pool7A820), used by7A77C halfword rolling sum. First/middle/last128-word cases and wrong-bound negative control PASS. Excludes hole for this reader only; not ROM ownership.'),
 (0xF75E,'Verified BE uint32 additive checksum loop @r14++; descriptor0 reads[2000,FFAF8), INCLUDING M0 hole. Stock/payload/boundary chunk regression PASS. Corrected checksum required; no full reset/peripheral timing proof.'),
 (0xFA84,'Verified checksum range validator: aligned4 start<=end, with end%4==3 OR start==end. Seven actual-opcode boundary cases PASS; gate_closure/rom/routine_regression.json.')]:
    old=idc.get_cmt(ea,0)
    if not ida_bytes.is_code(ida_bytes.get_flags(ea)):
        assert ida_ua.create_insn(ea)==2
    assert ida_bytes.set_cmt(ea,comment,False)
    changes.append({'ea':ea,'old_comment':old,'new_comment':comment})
ea=0xFA84;old=ida_name.get_name(ea)
if old.startswith('sub_'):
    assert ida_name.set_name(ea,'oem_validate_rom_checksum_range',ida_name.SN_CHECK)
    changes.append({'ea':ea,'old_name':old,'new_name':'oem_validate_rom_checksum_range'})
assert hashlib.sha256(ida_bytes.get_bytes(0,0x100000)).hexdigest()=='a34c4ce8238bf28bdc18c191bbe73b2179130aa9846e952a6fa332bae442de96'
(OUT/'metadata_changes.json').write_text(json.dumps({'changes':changes,'rom_bytes_unchanged':True},indent=2))
print(json.dumps({'changes':len(changes),'rom_bytes_unchanged':True}))
