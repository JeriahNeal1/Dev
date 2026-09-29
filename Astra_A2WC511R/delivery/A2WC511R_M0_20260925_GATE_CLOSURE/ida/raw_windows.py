import json, hashlib
from pathlib import Path
import ida_bytes, ida_ua, idautils, idc
OUT=Path('C:/Dev/Astra_A2WC511R/reports/local/gate_closure/ida')
windows=[(0xA80,0xB10),(0xF600,0xF680),(0x7A740,0x7A900),(0x853F0,0x85610),
 (0xCE6A0,0xCE754),(0xFFAF8,0xFFC50),(0x85900,0x859BC),
 (0x545F0,0x54C00),(0x7B8F0,0x7BA00)]
r={'windows':{},'boundary_xrefs':{}}
for a,b in windows:
    rr=[]
    for ea in range(a,b,2):
        insn=ida_ua.insn_t();size=ida_ua.decode_insn(insn,ea)
        rr.append({'ea':ea,'word':ida_bytes.get_word(ea),'defined':ida_bytes.is_code(ida_bytes.get_flags(ea)),
            'text':idc.generate_disasm_line(ea,idc.GENDSM_FORCE_CODE) if size else None})
    r['windows'][hex(a)]=rr
for a in [0x7A820,0x7A79C,0x7A7B4,0xCE754,0xFFAF8,0xFFB80,0xFFB84,0xE1000,0xFFFF8]:
    r['boundary_xrefs'][hex(a)]=[{'from':x.frm,'to':x.to,'type':x.type,'code':bool(x.iscode)} for x in idautils.XrefsTo(a)]
(OUT/'raw_windows.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
print(json.dumps({'ranges':list(r['windows']),'xrefs':r['boundary_xrefs']}))
