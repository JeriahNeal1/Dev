"""Create three named SH leaf functions in a disposable acceptance database."""
import ida_bytes,ida_funcs,ida_name,ida_ua,ida_auto,ida_pro
for a in (0,0x10,0x20):
    assert ida_bytes.get_bytes(a,6)==bytes.fromhex('E0'+f'{a//16+1:02X}'+'000B0009')
    for offset in (0,2,4):assert ida_ua.create_insn(a+offset)>0
    assert ida_funcs.get_func(a) or ida_funcs.add_func(a,a+6)
    assert ida_name.set_name(a,'probe_return_'+str(a//16+1),ida_name.SN_CHECK)
ida_auto.auto_wait()
ida_pro.qexit(0)
