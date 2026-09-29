from pathlib import Path
from hashlib import sha256
import json
import ida_bytes,ida_funcs,ida_ua,idautils,idc
root=Path('C:/Dev/Astra_A2WC511R');out=root/'reports/local/m07_residency/ida'
raw=ida_bytes.get_bytes(0,0x100000);stock=Path('C:/Dev/SubaruRoms/OEM/A2WC511R.bin').read_bytes()
spans=[(0x4260,0x430A),(0x1473C,0x147AC),(0x484B0,0x484BC)]
assert all(raw[a:b]==stock[a:b] for a,b in spans)
sites=[]
for a in (0x4260,0x42A4,0x430A,0x1466E,0x1473A,0x1473C,0x14770,0x147AC,0x4828C,0x484B0):
 f=ida_funcs.get_func(a);insn=ida_ua.insn_t();decoded=ida_ua.decode_insn(insn,a)
 sites.append({'address':a,'name':idc.get_name(a),'decoded_size':decoded,'bytes':raw[a:a+8].hex(),
  'function':None if f is None else {'entry':f.start_ea,'end_exclusive':f.end_ea,'chunks':list(idautils.Chunks(f.start_ea))},
  'xrefs':[{'from':x.frm,'to':x.to,'type':x.type,'code':bool(x.iscode)} for x in idautils.XrefsTo(a)]})
result={'status':'PASS_LOCAL_IDB_BYTES_AND_METADATA_READ','rom_sha256':sha256(raw).hexdigest(),
 'stock_sha256':sha256(stock).hexdigest(),'equal_spans':spans,'sites':sites,'metadata_changed':False,
 'scope':'Existing IDB function boundaries/xrefs are evidence, not a complete computed-entry theorem.'}
(out/'current_candidate_idb.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'sites':len(sites),'rom_sha256':result['rom_sha256']}))
