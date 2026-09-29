"""Optional one-shot static IDB export; run through IDA File > Script file.
Not an MCP server. No listener, input-byte patch, live ECU access or IDB save.
Prefer the official MCP's discovered export/read tools when available.
"""
from pathlib import Path
import datetime, hashlib, json
import ida_bytes, ida_funcs, ida_name, ida_nalt, ida_segment, ida_ua, idautils, idc
ROOT=Path(__file__).resolve().parents[1]
if ida_bytes.get_bytes(0x2000,9)!=b'A2WC511R\0':
    raise RuntimeError('Unexpected input CALID; no export performed')
rom=ida_bytes.get_bytes(0,0x100000)
if rom is None or len(rom)!=0x100000:raise RuntimeError('Expected mapped 1 MiB ROM')
ledger=json.loads((ROOT/'state/SYMBOLS.json').read_text(encoding='utf-8'))
out={'schema':'a2wc-static-idb-checkpoint-v2','created':datetime.datetime.now(datetime.timezone.utc).isoformat(),
     'input_file':ida_nalt.get_input_file_path(),'static_rom_sha256':hashlib.sha256(rom).hexdigest(),
     'notice':'Static IDB export, not live ECU memory. Existing IDB metadata only; no edits.',
     'segments':[], 'symbols':[], 'functions':[]}
for ea in idautils.Segments():
    s=ida_segment.getseg(ea)
    out['segments'].append({'start':s.start_ea,'end_exclusive':s.end_ea,'name':ida_segment.get_segm_name(s)})
for symbol in ledger['symbols']:
    ea=int(symbol['address'],16);flags=ida_bytes.get_flags(ea)
    out['symbols'].append({'address':symbol['address'],'name':ida_name.get_name(ea),'comment':idc.get_cmt(ea,1),
        'is_head':ida_bytes.is_head(flags),'is_code':ida_bytes.is_code(flags)})
for start,end in [(0x147AC,0x14802),(0x24950,0x24A9C),(0x24A9C,0x24AA4),(0x15A02,0x15A16),(0x15A2C,0x15D46),(0x15D46,0x15D92)]:
    # get_func has worked in the user's beta; deprecation is not a guessed new signature.
    f=ida_funcs.get_func(start);lines=[]
    for ea in range(start,end,2):
        insn=ida_ua.insn_t();size=ida_ua.decode_insn(insn,ea);raw=ida_bytes.get_bytes(ea,2)
        lines.append({'address':ea,'bytes':None if raw is None else raw.hex(),'decoded_length':size,
            'text':idc.generate_disasm_line(ea,idc.GENDSM_FORCE_CODE) if size>0 else None,
            'persistent_code':ida_bytes.is_code(ida_bytes.get_flags(ea))})
    out['functions'].append({'requested_start':start,'expected_end':end,'actual_start':None if not f else f.start_ea,
        'actual_end':None if not f else f.end_ea,'name':ida_name.get_name(start),'window':lines,
        'xref_types':[{'from':x.frm,'type':x.type,'is_code':x.iscode} for x in idautils.XrefsTo(start)]})
p=ROOT/'reports'/('ida-checkpoint-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.json')
with p.open('x',encoding='utf-8') as handle:json.dump(out,handle,indent=2)
print('Static IDB checkpoint:',p)
print('No IDB changes or save were performed; save manually after any separate metadata edits.')
