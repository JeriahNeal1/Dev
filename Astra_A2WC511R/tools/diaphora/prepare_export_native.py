"""Fresh native SH firmware database preparation plus strict Diaphora export."""
from pathlib import Path
from hashlib import sha256
import sys,os,json,traceback
import ida_auto,ida_bytes,ida_funcs,ida_segment,ida_ida,ida_idaapi,ida_pro,idautils,idc
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import export_native

def run(job):
    raw=Path(job['rom']).read_bytes();assert sha256(raw).hexdigest()==job['rom_sha256']
    assert ida_ida.inf_get_procname().lower()=='sh4b',ida_ida.inf_get_procname()
    ida_ida.inf_set_be(True)
    assert ida_ida.inf_is_be()
    rom=ida_segment.getseg(0);assert rom and rom.start_ea==0 and rom.end_ea==0x100000
    ida_segment.set_segm_addressing(rom,1)
    assert ida_bytes.get_bytes(0,0x100000)==raw
    low,high=job['ram_segment'];assert ida_segment.add_segm(0,low,high,'RAM','DATA')
    ida_segment.set_segm_addressing(ida_segment.getseg(low),1)
    before={'af':ida_ida.inf_get_af(),'af2':ida_ida.inf_get_af2()}
    # Do not assign copied function ends: IDA discovers each target's own flow.
    for item in job['function_seeds']:ida_auto.auto_make_proc(item['address'])
    assert ida_auto.auto_wait()
    seed_status=[{'address':x['address'],'exact_function_start':bool((f:=ida_funcs.get_func(x['address'])) and f.start_ea==x['address']),
                  'containing_function':f.start_ea if f else None} for x in job['function_seeds']]
    functions=[]
    for ea in idautils.Functions(0,0x100000):
        f=ida_funcs.get_func(ea)
        chunks=list(idautils.Chunks(ea))
        inbound=[{'from':x.frm,'to':x.to,'type':x.type,'iscode':bool(x.iscode)} for x in idautils.XrefsTo(ea,0)]
        refs=[]
        for head in idautils.FuncItems(ea):
            for x in idautils.XrefsFrom(head,0):
                if x.type!=21:refs.append({'from':x.frm,'to':x.to,'type':x.type,'iscode':bool(x.iscode)})
        functions.append({'start':ea,'end':f.end_ea,'name':idc.get_func_name(ea),'chunks':chunks,
                          'frame_size':f.frsize,'frame_regs':f.frregs,'args_size':f.argsize,
                          'chunk_sha256':[sha256(raw[a:b]).hexdigest() for a,b in chunks],
                          'inbound':inbound,'references':refs})
    analysis={**job,'status':'PASS','analysis_options':before,'functions':functions,'seed_status':seed_status,
              'segments':[{'start':s,'end':ida_segment.getseg(s).end_ea,'name':idc.get_segm_name(s),'bitness':ida_segment.getseg(s).bitness} for s in idautils.Segments()]}
    Path(job['export']).with_suffix('.analysis.json').write_text(json.dumps(analysis,indent=2)+'\n',encoding='utf-8')
    export_native.export(Path(job['export']))

if __name__=='__main__':
    job=json.loads(Path(os.environ['A2WC_DIAPHORA_JOB']).read_text());code=0
    try:run(job)
    except BaseException:
        failure={'status':'FAIL','traceback':traceback.format_exc(),'sys_path':sys.path,'python':sys.version,'job':job}
        Path(job['export']).with_suffix('.failure.json').write_text(json.dumps(failure,indent=2)+'\n',encoding='utf-8')
        traceback.print_exc();code=1
    finally:ida_pro.qexit(code)
