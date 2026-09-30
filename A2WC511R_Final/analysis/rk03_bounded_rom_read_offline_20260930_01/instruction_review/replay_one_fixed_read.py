"""One fixed512-byte instruction-model read from a retained postidentity checkpoint.
No native host, provider, hardware, arbitrary input, acquisition loop or flash.
"""
from pathlib import Path
import collections, datetime as dt, gzip, hashlib, json, sys, traceback
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent
ROOT=Path(r'C:\Dev\A2WC511R_ReadKernel')
PRIOR=Path(r'C:\Dev\A2WC511R_Final\analysis\rk03_kernel_identity_offline_20260930_01\instruction_review\replay_20260930T054149444398Z\INSTRUCTION_REPLAY.json')
MANIFEST=ROOT/'build/rk02_01/manifest.json'
CURRENT=Path(r'C:\Dev\SubaruRoms\current.bin')
KERNEL=ROOT/'build/rk02_01/kernel.bin'
CONTRACT=OUT/'FIXED_READ_CONTRACT.json'
def pin(p):
    p=Path(p);b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,obj):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,indent=2);f.write('\n')
def packed(p,obj):
    with Path(p).open('xb') as f:f.write(gzip.compress(json.dumps(obj,sort_keys=True,separators=(',',':')).encode(),mtime=0))
def main():
    run=OUT/('replay_'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));run.mkdir(exist_ok=False)
    report={'schema':1,'status':'FAIL','scope':'OFFLINE_ONE_FIXED_FIRST512_BYTE_READ','physical_operations':0,'provider_loads':0,
            'upload_start_identity_instructions_reexecuted':0,'new_read_requests':0,'full_acquisition':False}
    try:
        assert pin(PRIOR)['sha256']=='300de29c90b7f79b7bc845859232bcc75f08ce3a311f749f0851e01f7bca0ffa'
        assert pin(CONTRACT)['sha256']=='48df08343615f960263d9940b648c44568a9c0dbb8f2ae588267cfce53dd2b6a'
        prior=read(PRIOR);contract=read(CONTRACT);manifest=read(MANIFEST)
        variant=prior['kernel_identity_variants']['actual_OEM_registers'];model=variant['model_identity']
        inputs=[PRIOR,CONTRACT,MANIFEST,CURRENT,KERNEL,Path(__file__),Path(model['core_path'])]
        assert pin(MANIFEST)['sha256']==model['manifest_sha256']
        assert pin(CURRENT)['sha256']==model['rom']['sha256']=='bf10be6d7c75b4f2ae663b0d57a912e6e9ef7654ccfc985195954596e50427b2'
        assert pin(KERNEL)['sha256']==model['kernel_sha256']=='3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581'
        assert pin(model['core_path'])['sha256']==model['core_sha256']
        for name,h in model['model_sources'].items():
            p=ROOT/'sim'/name;assert pin(p)['sha256']==h;inputs.append(p)
        for relative,h in manifest['sources'].items():
            p=ROOT/relative;assert pin(p)['sha256']==h;inputs.append(p)
        for k in ['trace','coverage']:
            p=Path(variant[k]['path']);assert pin(p)==variant[k];inputs.append(p)
        coverage=read(variant['coverage']['path'])
        old=json.loads(gzip.decompress(Path(variant['trace']['path']).read_bytes()))
        assert variant['response_from_executed_SCI']=='beef000f8141325743353131522d524b3032005f'
        assert variant['ROM_data_read_events']==0 and variant['stop_reason']=='RX_WAIT_AFTER_ONE_IDENTITY_EXCHANGE'
        assert coverage['registers']['r8']==coverage['registers']['r9']=='00000000' and coverage['registers']['r10']=='00000001'
        assert len(old['instructions'])==4778 and len(coverage['exchanges'])==2 and coverage['terminal'] is None
        sys.path.insert(0,str(ROOT))
        from sim.harness import KernelSession
        from sim.sci import Schedule
        from sim.self_echo import EchoProfile
        initial=model['peripheral_initial'].copy();initial['sci2']={int(k,16):v for k,v in initial['sci2'].items()}
        session=KernelSession(MANIFEST,CURRENT,model['rom']['sha256'],kernel_bytes=KERNEL.read_bytes(),
            trace_dir=run/'exchange',detailed=True,optimized=False,schedule=Schedule(**model['schedule']),
            peripheral_initial=initial,receiver_self_echo=True,echo_profile=EchoProfile(**model['echo_profile']))
        # Reconstruct finite peripheral state by replaying retained register accesses
        # and their instruction ticks; no prior CPU instructions are executed.
        sci=session.peripheral.sci
        for e in old['SCI_events']:
            while sci.tick<e['tick']:sci.advance()
            if e['kind']=='register_read':assert sci.read(int(e['address'],16),1)==e['value']
            elif e['kind']=='register_write':sci.write(int(e['address'],16),1,e['value'])
            elif e['kind']=='host_rx_enqueued':
                identity=bytes.fromhex(variant['request']);assert e['bytes']==len(identity);sci.feed(identity)
        while sci.tick<len(old['instructions']):sci.advance()
        assert sci.events==old['SCI_events']
        for mode,address,size,value in old['other_peripheral_events']:
            if mode=='r':assert session.peripheral.read(address,size)==value
            else:session.peripheral.write(address,size,value)
        assert session.peripheral.events==[tuple(x) for x in old['other_peripheral_events']]
        private_writes=0
        for e in old['memory']:
            address=int(e['address'],16)
            if e['mode']=='w' and address<0xffffc000:
                assert any(a<=address<address+e['size']<=b for a,b in session.ram_spans)
                session.memory.initialize(address,int(e['value'],16).to_bytes(e['size'],'big'));private_writes+=1
        for n in range(16):session.cpu._reg(n,int(coverage['registers'][f'r{n}'],16),())
        system=coverage['system'];session.cpu._set_system('sr',int(system['SR'],16),())
        for attr in ['pr','vbr','mach','macl']:setattr(session.cpu,attr,int(system[attr.upper()],16))
        session.cpu.pc=int(variant['end_pc'],16);session.cpu.pending=None;session.cpu.returned=False
        session.cpu.call_context=list(old['instructions'][-1]['call_context'])
        session.cpu.min_sp=manifest['stack_high']-coverage['stack_max_bytes']
        assert session.cpu.pc==manifest['symbols']['rx_poll'] and session.cpu.call_context==['FFFF3004','FFFF31BC']
        assert sci.rx_empty and sci.tx_idle and sci.line_idle and not sci.current_echo
        assert bytes(sci.tx).hex()==variant['response_from_executed_SCI']
        assert session.cpu.trace.count==0 and not session.memory.events
        session.started=True
        checkpoint={'origin':'RESTORED_RETAINED_POST_IDENTITY_EMPTY_RX_CHECKPOINT','pc':f'{session.cpu.pc:08X}',
            'registers':coverage['registers'],'system':system,'call_context':session.cpu.call_context.copy(),
            'restored_private_write_events':private_writes,'SCI_events_exactly_reproduced':len(sci.events),
            'other_peripheral_events_exactly_reproduced':len(session.peripheral.events),
            'SCI_registers':{f'{k:08X}':v for k,v in sci.reg.items()},'SCI_tick':sci.tick,
            'queues_empty':True,'new_CPU_instructions_before_read':0}
        save(run/'RESTORED_CHECKPOINT.json',checkpoint)
        base_sci_counts=collections.Counter(sci.event_counts);base_sci_len=len(sci.events);base_other_len=len(session.peripheral.events)
        request=bytes.fromhex(contract['request_hex']);expected=bytes.fromhex(contract['reply_hex'])
        assert request==bytes.fromhex('beef00080300000000000200ba') and len(request)==13
        response=session.exchange(request,instruction_budget=100000)
        report['new_read_requests']=1
        assert response.status=='PASS' and response.stop_reason=='RX_WAIT' and response.tx_bytes==expected
        assert len(response.tx_bytes)==523 and response.tx_bytes[10:-1]==CURRENT.read_bytes()[:512]
        assert response.tx_bytes[-1]==sum(response.tx_bytes[:-1])%256
        cov=session.coverage();symbols=manifest['symbols']
        assert session.cpu.r[8]==512 and session.cpu.r[9]==0 and session.cpu.r[10]==1 and session.cpu.r[11]==1
        assert session.cpu.pc==symbols['rx_poll'] and session.terminal is None and len(session.results)==1
        assert set(session.cpu.pc_counts)<=set(manifest['instruction_addresses'])
        for name in ['raw_read','decode_address','tx_raw','tx_address','tx_data']:assert symbols[name] in session.cpu.pc_counts
        forbidden=['kernel_entry','identity','pass_done','complete','fatal','halt_fail','exception_handler','halt_exception']
        assert all(symbols[name] not in session.cpu.pc_counts for name in forbidden)
        rom_reads=[e for e in session.memory.events if e['mode']=='r' and int(e['address'],16)<0x100000]
        assert len(rom_reads)==512 and [int(e['address'],16) for e in rom_reads]==list(range(512))
        assert all(e['size']==1 and int(e['pc'],16)==symbols['tx_data'] for e in rom_reads)
        assert bytes(int(e['value'],16)&255 for e in rom_reads)==CURRENT.read_bytes()[:512]
        writes=[e for e in session.memory.events if e['mode']=='w']
        assert all(int(e['address'],16)>=0xffff3710 for e in writes)
        assert all(not 0xffffe800<=int(e['address'],16)<0xffffe810 for e in writes)
        assert all(any(a<=int(e['address'],16)<int(e['address'],16)+e['size']<=b for a,b in session.ram_spans)
                   or 0xfffff010<=int(e['address'],16)<=0xfffff016 for e in writes)
        assert session.memory.kernel==KERNEL.read_bytes()
        delta=dict(collections.Counter(sci.event_counts)-base_sci_counts)
        assert delta['host_rx_enqueued']==1 and delta['tx_character_complete']==523
        assert sci.rx_empty and sci.tx_idle and sci.line_idle and not sci.current_echo
        save(run/'KERNEL_READ_COVERAGE.json',cov)
        packed(run/'KERNEL_READ_TRACE.json.gz',{'instructions':session.cpu.trace.rows,'memory':session.memory.events,
            'SCI_events':sci.events[base_sci_len:],'other_peripheral_events':session.peripheral.events[base_other_len:]})
        with (run/'ROM_BLOCK_00000000_00000200.bin').open('xb') as f:f.write(response.tx_bytes[10:-1])
        with (run/'READ_RESPONSE.bin').open('xb') as f:f.write(response.tx_bytes)
        assert session.identity['model_sources']==model['model_sources']
        inputs=[pin(p) for p in sorted(set(inputs))]
        assert all(pin(p['path'])==p for p in inputs)
        report.update(status='PASS_ONE_FIXED_READ_FROM_RETAINED_IDENTITY_CHECKPOINT',inputs=inputs,
            contract=pin(CONTRACT),prior_instruction_replay=pin(PRIOR),checkpoint=pin(run/'RESTORED_CHECKPOINT.json'),
            request_hex=request.hex(),response_hex=response.tx_bytes.hex(),response_sha256=hashlib.sha256(response.tx_bytes).hexdigest(),
            response_bytes=523,data_bytes=512,data_sha256=hashlib.sha256(response.tx_bytes[10:-1]).hexdigest(),
            range_start='00000000',range_end_exclusive='00000200',pass_number=0,cursor_after='00000200',
            instruction_count=response.instruction_count,read_exchange=response.as_dict(),ROM_data_read_events=512,
            ROM_data_read_PC=f'{symbols["tx_data"]:08X}',flash_write_events=0,kernel_mutation=False,
            forbidden_symbols_unexecuted=forbidden,SCI_event_counts_this_read=delta,
            kernel_coverage=pin(run/'KERNEL_READ_COVERAGE.json'),trace=pin(run/'KERNEL_READ_TRACE.json.gz'),
            model_identity=session.identity,
            limits=['This is actual unchanged SH-2E instruction execution in the pinned simulator, not a provider transcript or hardware operation.',
              'The prior completed upload/start/identity is reused. CPU registers/private RAM and finite peripheral state are reconstructed from its retained actual-OEM-register variant; no prior CPU instruction is rerun.',
              'Recorded peripheral register calls/ticks are replayed to reconstruct the exact idle checkpoint and compared with retained events. Prior identity bytes are replayed only into the peripheral-state reconstruction; the only new CPU exchange is the fixed read.',
              'Instruction ticks, UART completion/self-echo and peripheral models remain declared simulation assumptions, not physical baud or silicon timing.',
              'Exactly one read request is executed. The cursor advances to0x200, pass remains0, and the kernel waits for another request; no full acquisition, pass completion or later read is attempted.',
              'The fixed512-byte block matches stock as well as current.bin and cannot identify the complete current calibration. No ROM classification, Diaphora or historical analysis is repeated.'])
    except Exception:report['error']=traceback.format_exc()
    report['artifacts']=[pin(p) for p in sorted(run.rglob('*')) if p.is_file()]
    save(run/'INSTRUCTION_REPLAY.json',report)
    if report['status'].startswith('PASS'):save(OUT/'INSTRUCTION_REVIEW.json',{'status':report['status'],'replay':pin(run/'INSTRUCTION_REPLAY.json'),'physical_operations':0,'provider_loads':0,'new_read_requests':1})
    print(json.dumps({'status':report['status'],'report':pin(run/'INSTRUCTION_REPLAY.json'),'error':report.get('error')}))
    return 0 if report['status'].startswith('PASS') else 1
if __name__=='__main__':raise SystemExit(main())
