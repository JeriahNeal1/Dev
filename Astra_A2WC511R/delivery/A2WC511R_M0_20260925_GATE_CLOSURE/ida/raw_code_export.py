import json
from pathlib import Path
import ida_bytes, ida_ua, idc
OUT=Path('C:/Dev/Astra_A2WC511R/reports/local/gate_closure/ida')
rows=[]
for ea in range(0,0x859BC,2):
    insn=ida_ua.insn_t()
    if not ida_ua.decode_insn(insn,ea):continue
    rows.append({'ea':ea,'word':ida_bytes.get_word(ea),
       'defined':ida_bytes.is_code(ida_bytes.get_flags(ea)),
       'ops':[{'type':op.type,'reg':op.reg,'value':op.value,'addr':op.addr,'dtype':op.dtype} for op in insn.ops if op.type]})
(OUT/'raw_decodable_code.json').write_text(json.dumps(rows),encoding='utf-8')
print(json.dumps({'raw_decodable_even_words':len(rows),'note':'Decode only; contains data. No code items created.'}))
