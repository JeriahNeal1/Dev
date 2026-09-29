"""Execute the real portable C observer as a private no-CRT Windows DLL."""
from pathlib import Path
import ctypes as C, hashlib, json, subprocess, argparse
ROOT=Path(__file__).resolve().parent
MSVC=Path(r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64')
class Input(C.Structure):
    _fields_=[(x,C.c_uint8) for x in ('source','snapshot','latch','flags','freshness','capture_changed','reserved0','reserved1')]
class State(C.Structure):
    _fields_=[(x,C.c_uint32) for x in ('sequence','magic','samples','reasons','transitions')]+[(x,C.c_uint8) for x in ('source','snapshot','latch','flags','target_nibble','current_nibble','decoded_target','decoded_current','freshness','previous_snapshot','initialized','capture_changed')]
def main(out):
    out.mkdir(parents=True,exist_ok=False)
    commands=[[str(MSVC/'cl.exe'),'/nologo','/c','/O2','/GS-','/DM0_HOST_TEST','/Fo'+str(out/'Diagnostic.obj'),str(ROOT/'Diagnostic.c')],
              [str(MSVC/'link.exe'),'/NOLOGO','/DLL','/NOENTRY','/NODEFAULTLIB','/OUT:'+str(out/'Diagnostic.dll'),str(out/'Diagnostic.obj')]]
    for i,cmd in enumerate(commands):
        p=subprocess.run(cmd,cwd=out,capture_output=True,text=True,timeout=60)
        (out/f'build_{i}.log').write_text(json.dumps(cmd)+'\n'+p.stdout+p.stderr)
        if p.returncode: raise RuntimeError(p.stdout+p.stderr)
    lib=C.CDLL(str(out/'Diagnostic.dll'))
    lib.m0_decode.argtypes=[C.c_uint8,C.c_uint8];lib.m0_decode.restype=C.c_uint8
    lib.m0_reasons.argtypes=[C.POINTER(Input)];lib.m0_reasons.restype=C.c_uint32
    lib.m0_init.argtypes=[C.POINTER(State)];lib.m0_observe.argtypes=[C.POINTER(State),C.POINTER(Input)]
    assert C.sizeof(State)==32
    checks=0
    for raw in range(256):
        for previous in range(256):
            assert lib.m0_decode(raw,previous)==(raw if raw<8 else 0 if raw==8 else previous)
            checks+=1
    for snapshot in range(256):
        for source in range(256):
            for fresh in (0,1,2,3,255):
                inp=Input(source,snapshot,1,2,fresh,0,0,0)
                expected=512 | (1 if snapshot!=17 else 0) | (32 if source!=snapshot else 0)
                expected|=(8 if fresh==0 else 0 if fresh==1 else 16 if fresh==2 else 64)
                expected|=128 if snapshot>>4>8 or snapshot&15>8 else 0
                assert lib.m0_reasons(C.byref(inp))==expected
                checks+=1
    for latch in range(256):
        for flags in range(256):
            inp=Input(17,17,latch,flags,0,0,0,0)
            assert lib.m0_reasons(C.byref(inp))==520|(2 if latch!=1 else 0)|(4 if not flags&2 else 0)
            checks+=1
    for fill in range(256):
        arena=(C.c_uint8*64)(*[fill]*64)
        st=C.cast(C.byref(arena,16),C.POINTER(State))
        lib.m0_init(st)
        assert st.contents.magic==0x4d304431 and st.contents.initialized==1
        assert st.contents.samples==0 and st.contents.reasons==520
        prev_target=prev_current=0
        for ix,snapshot in enumerate((0x88,0x11,0x22,0xe8,0xe9,0xff,0x00,0x77,0x55)):
            inp=Input(snapshot,snapshot,1,2,0,ix&1,0,0)
            lib.m0_observe(st,C.byref(inp))
            t,c=snapshot>>4,snapshot&15
            prev_target=t if t<8 else 0 if t==8 else prev_target
            prev_current=c if c<8 else 0 if c==8 else prev_current
            assert st.contents.decoded_target==prev_target and st.contents.decoded_current==prev_current
            assert st.contents.samples==ix+1 and st.contents.transitions==ix and st.contents.sequence==(ix+2)*2
            assert bool(st.contents.reasons&256)==bool(ix&1)
            assert bytes(arena[:16])==bytes([fill]*16) and bytes(arena[48:])==bytes([fill]*16)
            checks+=1
    state=State();lib.m0_init(C.byref(state));state.samples=0xffffffff;state.sequence=0xfffffffe;state.transitions=0xffffffff;state.previous_snapshot=0
    inp=Input(17,17,1,2,0,0,0,0);lib.m0_observe(C.byref(state),C.byref(inp))
    assert state.samples==state.sequence==state.transitions==0
    state.magic=0;lib.m0_observe(C.byref(state),C.byref(inp));assert state.samples==1 and state.magic==0x4d304431 and state.sequence==4
    prior=state.sequence;lib.m0_init(C.byref(state));assert state.sequence==prior+2 and state.samples==0
    report={'result':'PASS','checks':checks+3,'state_bytes':C.sizeof(State),'coverage':['all 256 raw decode inputs x all 256 previous values','all 256 packed snapshot x all 256 source values x 5 freshness states','all latch/status bytes','initialization from 256 fill patterns','transitions/hold/reverse/neutral','publication sequence and counter wrap','explicit reinitialization advances sequence','32-byte write boundary canaries'],
            'source_sha256':hashlib.sha256((ROOT/'Diagnostic.c').read_bytes()).hexdigest(),'dll_sha256':hashlib.sha256((out/'Diagnostic.dll').read_bytes()).hexdigest(),
            'limitation':'Host C semantics only; no CPU/ABI/vehicle/timing/freshness proof'}
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);main(p.parse_args().out.resolve())
