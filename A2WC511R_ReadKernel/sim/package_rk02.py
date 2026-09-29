"""Join completed RK02 execution evidence; never substitute a historical run."""
import argparse
from collections import Counter
from hashlib import sha256
import io
import json
from pathlib import Path
import unittest
from .core import CORE_PATH, CORE_SHA256
from . import test_model, test_echo

PIN='3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581'
def pin(p):
    p=Path(p).resolve();return {'path':str(p),'sha256':sha256(p.read_bytes()).hexdigest()}
def read_pin(item):
    raw=Path(item['path']).read_bytes();assert sha256(raw).hexdigest()==item['sha256'];return json.loads(raw)

def run(root,manifest):
    root=Path(root).resolve();manifest=Path(manifest).resolve();m=json.loads(manifest.read_bytes())
    assert m['kernel_sha256']==PIN
    assert not (root/'QUALIFICATION.json').exists() and not (root/'coverage.json').exists()
    final_sources=json.loads((root/'final_model/FILES.json').read_bytes())
    for name,digest in final_sources.items():
        assert sha256((Path(__file__).parent/name).read_bytes()).hexdigest()==digest
        assert sha256((root/'final_model'/name).read_bytes()).hexdigest()==digest
    assert sha256(CORE_PATH.read_bytes()).hexdigest()==CORE_SHA256
    paths=[root/'stock_full_01/FULL_READ.json',root/'faults_01/FAULTS.json',root/'SELF_ECHO_QUALIFICATION.json']
    docs=[json.loads(p.read_bytes()) for p in paths];full,fault,echo=docs
    assert all(d['status']=='PASS' for d in docs)
    assert full['identity']['kernel_sha256']==fault['kernel_sha256']==echo['kernel_sha256']==PIN
    assert full['identity']['receiver_self_echo'] is True
    assert full['terminal']=='COMPLETE' and full['SCI2_SCR']==0 and full['blocks']==4096
    assert len(full['passes'])==2
    for n,p in enumerate(full['passes']):
        raw=Path(p['path']).read_bytes()
        assert p['pass']==n and p['bytes']==len(raw)==0x100000
        assert sha256(raw).hexdigest()==p['sha256']==full['identity']['rom']['sha256']
    assert full['identity']['model_sources']==fault['model_sources']==echo['model_sources']==final_sources
    inputs=[read_pin(d['coverage']) for d in docs]
    ec=inputs[0]['SCI_event_counts'];chars=4096*523+20
    assert ec['tx_character_complete']==ec['ECU_self_echo_ignored_RE0']==ec['ECU_self_echo_start_RE0']==chars
    assert not ec.get('ECU_self_echo_start_admitted',0) and not ec.get('ECU_self_echo_overrun',0)
    counts=Counter();edges=Counter();writes=Counter();bounds={};mmio=[]
    for d in inputs:
        counts.update({int(a,16):n for a,n in d['instruction_counts'].items()})
        edges.update({(int(e['from'],16),int(e['to'],16)):e['count'] for e in d['edges']})
        writes.update({(int(w['address'],16),w['size'],int(w['pc'],16)):w['count'] for w in d['writes']})
        for pc,(a,b) in d['read_bounds_by_pc'].items():
            a,b=int(a,16),int(b,16);old=bounds.get(pc,(a,b));bounds[pc]=(min(a,old[0]),max(b,old[1]))
        for row in d.get('MMIO_accesses',[]):
            if row not in mmio:mmio.append(row)
    ins=set(m['instruction_addresses']);assert set(counts)==ins,(len(counts),len(ins),ins-counts.keys())
    branches=[]
    for i in m['instructions']:
        pc,op=i['address'],i['opcode']
        if op&0xFF00 not in (0x8900,0x8B00):continue
        disp=op&255;disp=disp-256 if disp&128 else disp;targets=(pc+2,(pc+4+2*disp)&0xFFFFFFFF)
        assert all(edges[(pc,t)]>0 for t in targets),(f'{pc:08X}',targets)
        branches.append({'pc':f'{pc:08X}','opcode':f'{op:04X}',
          'successors':[{'pc':f'{t:08X}','count':edges[(pc,t)]} for t in targets]})
    cov={'schema':1,'status':'PASS','kernel_sha256':PIN,'receiver_self_echo':True,
      'inputs':[d['coverage'] for d in docs],
      'instruction_counts':{f'{a:08X}':n for a,n in sorted(counts.items())},
      'unexecuted_instruction_addresses':[],
      'edges':[{'from':f'{a:08X}','to':f'{b:08X}','count':n} for (a,b),n in sorted(edges.items())],
      'conditional_branches':branches,'conditional_branches_covered':len(branches),
      'conditional_directions_covered':len(branches)*2,
      'writes':[{'address':f'{a:08X}','size':z,'pc':f'{p:08X}','count':n} for (a,z,p),n in sorted(writes.items())],
      'read_bounds_by_pc':{pc:[f'{a:08X}',f'{b:08X}'] for pc,(a,b) in sorted(bounds.items())},
      'MMIO_accesses':mmio,'software_stack_bytes':0,
      'stack_max_bytes':max(d['stack_max_bytes'] for d in inputs),
      'private_stack_capacity_bytes':m['stack_high']-m['stack_low'],
      'hardware_exception_writes':[
        {'address':f"{m['stack_high']-4:08X}",'size':4,'value':'saved SR','origin':'explicit virtual hardware NMI entry'},
        {'address':f"{m['stack_high']-8:08X}",'size':4,'value':'saved PC','origin':'explicit virtual hardware NMI entry'}],
      'instruction_address_definition':'335 compiled executable words; header, literal pools, identity, vectors and upload checksum excluded',
      'unsupported_instruction_count':0,'unsupported_MMIO_count':0,
      'expected_rejections_are_not_unsupported_execution':True}
    assert cov['stack_max_bytes']==8 and cov['private_stack_capacity_bytes']==16
    cp=root/'coverage.json';cp.write_text(json.dumps(cov,indent=2)+'\n')
    log=io.StringIO();suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(mod) for mod in (test_model,test_echo)])
    result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    assert result.wasSuccessful(),log.getvalue()
    lp=root/'unit_models.log';lp.write_text(log.getvalue())
    unit={'status':'PASS','groups':result.testsRun,'local_ISA_value_T_delay_checks':144,
      'sources':[pin(test_model.__file__),pin(test_echo.__file__)],'log':pin(lp),
      'includes':['TDR/TSR buffering and TEND','TE0 abort pending/buffered bytes',
        'receive admission at start vs completion','all 256 echo values under RE0',
        'RDR retention, ORER and subsequent receive disable','strict opcode/MMIO/private-memory failures']}
    up=root/'unit_models.json';up.write_text(json.dumps(unit,indent=2)+'\n')
    parity=root/'fast_parity_01.json';pr=json.loads(parity.read_bytes());assert pr['status']=='PASS' and pr['kernel_sha256']==PIN
    parity_sources={}
    for name,digest in pr['source_sha256'].items():
        candidates=[Path(__file__).parent/name,root/'final_model'/name,root.parent/'input_snapshot/sim'/name]
        match=next((p for p in candidates if p.exists() and sha256(p.read_bytes()).hexdigest()==digest),None)
        assert match is not None,('orphan parity source',name,digest)
        parity_sources[name]=pin(match)
    report={'schema':1,'status':'PASS','artifact_class':'TEMP_RAM_ACQUISITION_TOOL',
      'kernel_sha256':PIN,'kernel_bytes':m['kernel_bytes'],'manifest':pin(manifest),
      'software_scope':'Actual compiled RK02 with strict explicit SH7058 SCI2 receive-start/half-duplex model',
      'receiver_self_echo':True,'coverage':pin(cp),'instruction_covered':len(counts),'instruction_total':len(ins),
      'instruction_missing':[],'branches_total':len(branches),'branch_directions_covered':len(branches)*2,
      'software_stack_bytes':0,'stack_max_bytes':8,'private_stack_bytes':16,
      'fixtures':[{'name':'exact A2WC511R stock','report':pin(paths[0]),'full_passes':2,'blocks':4096,
        'bytes_per_pass':0x100000,'instructions_executed':full['instructions_executed'],'passes':full['passes'],
        'executed_model_snapshot':pin(root/'final_model/FILES.json'),'self_echo_ignored_bytes':chars}],
      'faults':pin(paths[1]),'compiled_fault_and_fuzz_cases':fault['case_count'],
      'closed_world_negative_controls':fault['negative_control_count'],'self_echo':pin(paths[2]),
      'self_echo_cases':echo['case_count'],'unit_models':pin(up),'frozen_step_parity':pin(parity),
      'compared_instruction_steps':pr['compared_instruction_steps'],'parity_source_resolution':parity_sources,
      'final_model_sources':{name:pin(Path(__file__).parent/name) for name in final_sources},
      'saved_model_snapshots':[pin(root/'final_model/FILES.json')],
      'test_sources':[pin(__file__),pin(Path(__file__).parent/'qualify_echo.py'),pin(Path(__file__).parent/'qualify_faults.py'),pin(Path(__file__).parent/'full_read.py')],
      'frozen_core':{'path':str(CORE_PATH),'sha256':CORE_SHA256,'modified':False},
      'unsupported_executed_instruction_count':0,'unsupported_executed_MMIO_count':0,
      'allowed_MMIO':mmio,'physical_status':'PHYSICAL_REQUIRED','physical_operations':0,
      'limitations':[
        'No physical ECU/provider, electrical waveform, baud tolerance or silicon timing verified.',
        'Self-echo starts during RE0 are ignored, including completion after RX restore. A genuinely new start after RX enable may enter the parser and reject; no arbitrary physical delay bound is asserted.',
        'Controlled host request delivery and ECU self-echo are explicit schedules; host J2534 echo filtering is separate.',
        'One injected hardware NMI frame at established RX boundary consumes eight bytes; prefix before private SP/VBR and rapid nested NMIs remain unproven.',
        'Clock, RAM mode, prior/in-flight DMA, external watchdog and actual power/reset restoration remain entry/physical contracts.',
        'Partial requests yield no response and require host deadlines; compiled reject/exception paths disable SCI and halt.',
        'Host-native composite/random fixture execution is separate and joined by the root validator.',
        'Full execution stores compact event hashes/counts rather than every event row; exact response equality is checked for each 512-byte block.']}
    rp=root/'QUALIFICATION.json';rp.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':'PASS','path':str(rp),'sha256':pin(rp)['sha256'],'instructions':len(ins),'branches':len(branches),'unit_groups':result.testsRun}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--manifest',required=True)
    a=p.parse_args();run(a.root,a.manifest)
