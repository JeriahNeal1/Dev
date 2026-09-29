import hashlib, json
from pathlib import Path
import ida_bytes, ida_funcs, ida_ua, idautils, idc

outdir = Path('C:/Dev/Astra_A2WC511R/reports/local/gate_closure/ida')
rom = ida_bytes.get_bytes(0, 0x100000)
out = {'rom_sha256': hashlib.sha256(rom).hexdigest(), 'code': [], 'functions': [], 'xrefs': [], 'names': []}
for ea in idautils.Heads(0, 0x100000):
    flags = ida_bytes.get_flags(ea)
    if ida_bytes.is_code(flags):
        insn = ida_ua.insn_t()
        size = ida_ua.decode_insn(insn, ea)
        f = ida_funcs.get_func(ea)
        out['code'].append({'ea':ea, 'word':int.from_bytes(rom[ea:ea+2],'big'), 'size':size,
            'mnemonic':idc.print_insn_mnem(ea), 'text':idc.generate_disasm_line(ea,0),
            'function':f.start_ea if f else None,
            'ops':[{'type':op.type,'reg':op.reg,'value':op.value,'addr':op.addr,'dtype':op.dtype,
                    'text':idc.print_operand(ea,i)} for i,op in enumerate(insn.ops) if op.type]})
    for ref in idautils.XrefsFrom(ea):
        out['xrefs'].append({'from':ref.frm,'to':ref.to,'type':ref.type,'code':bool(ref.iscode)})
for ea in idautils.Functions(0,0x100000):
    f = ida_funcs.get_func(ea)
    out['functions'].append({'start':ea,'end':f.end_ea,'name':idc.get_func_name(ea),
        'chunks':list(idautils.Chunks(ea)), 'frame_size':idc.get_frame_size(ea)})
for ea, name in idautils.Names():
    out['names'].append({'ea':ea,'name':name})
(outdir/'defined_code_export.json').write_text(json.dumps(out),encoding='utf-8')
print(json.dumps({'code':len(out['code']),'functions':len(out['functions']),'xrefs':len(out['xrefs']),
                 'sha256':out['rom_sha256'],'output':str(outdir/'defined_code_export.json')}))
