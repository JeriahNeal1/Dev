"""RK02 actual compiled half-duplex tests; no physical delay-bound claim."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from .harness import KernelSession
from .qualify_faults import Suite, read_body
from .verify_fast import frame
from .sci import Schedule, SCR, SSR, RDR, TEND
from .self_echo import EchoProfile

PIN='3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581'
VERSION=frame(b'\x81A2WC511R-RK02\0')

def run(manifest,rom,rom_hash,out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    assert json.loads(Path(manifest).read_text())['kernel_sha256']==PIN
    suite=Suite(manifest,rom,rom_hash,out/'echo_cases_01')
    details=[]
    def audit(s):
        rows=[];original=s.peripheral.sci.write
        def write(a,z,v):
            if a==SCR:
                row={'tick':s.peripheral.sci.tick,'value':v,'SSR_before':s.peripheral.sci.reg[SSR],
                  'pending_before':s.peripheral.sci.tx_pending,'buffer_before':s.peripheral.sci.tx_buffer}
                if v==0x10 and rows:
                    assert row['SSR_before']&TEND and row['pending_before'] is None and row['buffer_before'] is None,row
                rows.append(row)
            original(a,z,v)
        s.peripheral.sci.write=write
        return rows
    def record(name,s,r,expected,rows,**notes):
        suite.record(name,s,r,expected,allow_tx=True,kind='COMPILED_ECHO_SCHEDULE',injection=notes or None)
        details.append({'case':name,'identity':s.identity,'expected_outcome':expected,
          'response_hex':r.tx_bytes.hex(),'SCI_event_counts':dict(s.peripheral.sci.event_counts),
          'SCR_writes':rows,'notes':notes})
    profiles=[('no_echo',{'receiver_self_echo':False}),('every_byte_echo',{}),
      ('delayed_completion_after_RX_restore',{'schedule':Schedule(tx_complete_ticks=25),'echo_profile':EchoProfile(12)}),
      ('only_final_bytes_echo',{'schedule':Schedule(tx_complete_ticks=25),'echo_profile':EchoProfile(12,(20,543))})]
    for name,kw in profiles:
        s=suite.session(**kw);rows=audit(s);assert s.start().status=='PASS'
        r=s.exchange(frame(b'\1'));assert r.status=='PASS' and r.tx_bytes==VERSION
        r=s.exchange(frame(read_body()));assert r.status=='PASS' and r.tx_bytes==frame(b'\x83\0'+bytes(4)+s.rom.data[:512])
        ec=s.peripheral.sci.event_counts
        assert not ec['ECU_self_echo_start_admitted'] and not ec['ECU_self_echo_overrun']
        if name=='every_byte_echo':assert ec['ECU_self_echo_ignored_RE0']==543
        if name.startswith('delayed') or name=='only_final_bytes_echo':
            assert ec['ECU_self_echo_RE0_start_completed_after_RX_restore']>=1
        record(name,s,r,'RX_WAIT',rows)
    s=suite.session();rows=audit(s);assert s.start().status=='PASS'
    for packet,expected in [(frame(b'\1'),VERSION),(frame(read_body()),frame(b'\x83\0'+bytes(4)+s.rom.data[:512]))]:
        for n,b in enumerate(packet):
            r=s.exchange(bytes([b]));assert r.status=='PASS'
            assert r.tx_bytes==(expected if n==len(packet)-1 else b'')
    record('fragmented_requests_every_byte_echo',s,r,'RX_WAIT',rows)
    s=suite.session(peripheral_initial={'sci2':{SSR:0xFC,RDR:0xA5}});rows=audit(s)
    assert s.start().status=='PASS';r=s.exchange(frame(b'\1'));assert r.tx_bytes==VERSION
    record('entry_stale_RDRF_and_error_flags_cleared',s,r,'RX_WAIT',rows)
    for bit in (0x40,0x20,0x10,0x08,0x78):
        s=suite.session();rows=audit(s);assert s.start().status=='PASS';original=s.cpu.step;done=False
        def inject(s=s,original=original,bit=bit):
            nonlocal done
            if not done and s.cpu.pc==s.symbols['tx_frame']:
                s.peripheral.sci.reg[SSR]|=bit;done=True
            original()
        s.cpu.step=inject;r=s.exchange(frame(b'\1'))
        assert done and not r.tx_bytes
        record(f'pre_TX_residual_SSR_{bit:02X}',s,r,'KERNEL_REJECT',rows,explicit_peripheral_fault_bits=bit)
    s=suite.session();rows=audit(s);assert s.start().status=='PASS'
    assert s.exchange(frame(b'\1')).tx_bytes==VERSION
    r=s.exchange(b'\xA5');assert not r.tx_bytes
    record('new_post_RX_noise_start_rejected',s,r,'KERNEL_REJECT',rows,
      scope='A genuine new character after RX enable; not an ignored RE0 start')
    s=suite.session(echo_profile=EchoProfile(1000,(20,)));rows=audit(s)
    assert s.start().status=='PASS';r=s.exchange(frame(b'\1'))
    assert r.tx_bytes==VERSION and s.peripheral.sci.event_counts['ECU_self_echo_received']==1
    record('genuinely_late_echo_start_rejected',s,r,'KERNEL_REJECT',rows,
      scope='A declared new start after RX enable; expected fail-closed outcome, not successful protocol')
    suite.report([],0)
    # Superseded kernel is a negative control only, never included in RK02 coverage.
    old=Path(manifest).resolve().parents[1]/'attempt_03/manifest.json'
    s=KernelSession(old,rom,rom_hash,receiver_self_echo=True);assert s.start().status=='PASS'
    r=s.exchange(frame(b'\1'));assert r.stop_reason=='KERNEL_REJECT'
    assert s.peripheral.sci.event_counts['ECU_self_echo_received']==1
    assert s.peripheral.sci.event_counts['ECU_self_echo_overrun']==1
    negative={'kernel_sha256':s.identity['kernel_sha256'],'expected_outcome':'KERNEL_REJECT',
      'observed_outcome':r.stop_reason,'response_hex':r.tx_bytes.hex(),
      'SCI_event_counts':dict(s.peripheral.sci.event_counts),'included_in_RK02_coverage':False}
    cp=suite.out/'coverage.json'
    report={'schema':1,'status':'PASS','kernel_sha256':PIN,'physical':False,
      'classification':'ACTUAL_COMPILED_RK02_HALF_DUPLEX_UNDER_EXPLICIT_RECEIVE_START_SCHEDULES',
      'receiver_self_echo_default':True,'cases':details,'case_count':len(details),
      'coverage':{'path':str(cp),'sha256':sha256(cp.read_bytes()).hexdigest()},
      'RK01_negative_control':negative,'model_sources':suite.session().identity['model_sources'],
      'limits':['Receive admission is captured at start, not re-evaluated merely because RE is enabled at completion.',
        'No arbitrary maximum physical self-echo delay is asserted; a genuine new start after RX enable may enter the parser and must fail closed.',
        'ECU-side line loopback is separate from host J2534 transmit-echo filtering.',
        'Virtual instruction ticks are not silicon timing, baud tolerance or electrical waveform proof.',
        'These bounded communication cases do not substitute for full two-pass fixture execution.']}
    p=out/'SELF_ECHO_QUALIFICATION.json';p.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':'PASS','path':str(p),'sha256':sha256(p.read_bytes()).hexdigest(),'cases':len(details)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--rom',required=True)
    p.add_argument('--rom-sha256',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    run(a.manifest,a.rom,a.rom_sha256,a.out)
