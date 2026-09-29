"""Explicit ECU self-echo test against the previously qualified compiled object."""
from hashlib import sha256
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from sim.harness import KernelSession
from sim.self_echo import SelfEchoSCI2
from sim.verify_fast import frame
from sim.sci import Schedule,SSR,RDR,RDRF,ORER,SCR,TDR
manifest=ROOT/'build/attempt_03/manifest.json'
s=KernelSession(manifest,'C:/Dev/SubaruRoms/OEM/A2WC511R.bin','22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218')
s.peripheral.sci=SelfEchoSCI2(Schedule())
ready=s.start();assert ready.status=='PASS' and not ready.tx_bytes
r=s.exchange(frame(b'\1'))
assert r.status=='FAIL' and r.stop_reason=='KERNEL_REJECT',r.as_dict()
assert r.tx_bytes==frame(b'\x81A2WC511R-RK01\0')
assert s.peripheral.sci.reg[SSR]&ORER and s.peripheral.sci.reg[SSR]&RDRF
assert s.peripheral.sci.reg[RDR]==0xBE and s.peripheral.sci.reg[SCR]==0
assert s.peripheral.sci.event_counts['ECU_self_echo_received']==1
assert s.peripheral.sci.event_counts['ECU_self_echo_overrun']==len(r.tx_bytes)-1
# Focused register controls independently establish receive disable and overrun.
controls=[]
for enabled in (False,True):
    u=SelfEchoSCI2();u.reg[SCR]=0x30 if enabled else 0x20
    for value in (0x12,0x34):
        status=u.read(SSR,1);u.write(TDR,1,value);u.write(SSR,1,status&0x7F);u.advance()
    assert bytes(u.tx)==b'\x12\x34'
    if enabled:assert u.reg[RDR]==0x12 and u.reg[SSR]&(RDRF|ORER)==RDRF|ORER
    else:assert not u.reg[SSR]&(RDRF|ORER)
    controls.append({'RE':int(enabled),'status':'PASS','SSR':f'{u.reg[SSR]:02X}','RDR':f'{u.reg[RDR]:02X}',
       'event_counts':dict(u.event_counts)})
out={'schema':1,'status':'FAIL','classification':'OLD_COMPILED_KERNEL_REJECTS_AFTER_VERSION_UNDER_ECU_SELF_ECHO',
 'test_status':'PASS_REPRODUCED','kernel_sha256':s.identity['kernel_sha256'],'manifest':str(manifest),
 'model_source':{'path':str(ROOT/'sim/self_echo.py'),'sha256':sha256((ROOT/'sim/self_echo.py').read_bytes()).hexdigest()},
 'ready':ready.as_dict(),'version_exchange':r.as_dict(),'self_echo_events':dict(s.peripheral.sci.event_counts),
 'controls':controls,'physical_operations':0,'provider_loaded':False,
 'scope':['Declared ECU transceiver loopback topology, not host J2534 TX-echo metadata',
  'Actual compiled bytecode emits the version then sees ORER/RDRF and enters its fail halt',
  'Prior no-self-echo model qualification remains scoped to its recorded profile and does not close this topology',
  'Stock programming helper RE-disable evidence is supplied independently by the contracts agent']}
p=Path(__file__).with_name('CURRENT_KERNEL_ECHO_FAILURE.json');assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'status':out['status'],'test_status':out['test_status'],'report':str(p),'echo_overruns':s.peripheral.sci.event_counts['ECU_self_echo_overrun']}))
