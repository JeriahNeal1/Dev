"""Assemble hash-linked execution qualification without changing prior runs."""
import argparse
from collections import Counter
from hashlib import sha256
import io
import json
from pathlib import Path
import unittest
from .core import CORE_PATH,CORE_SHA256
from . import test_model

def pin(path):
    p=Path(path).resolve();return {'path':str(p),'sha256':sha256(p.read_bytes()).hexdigest()}

def package(root,manifest):
    root=Path(root).resolve();manifest=Path(manifest).resolve();m=json.loads(manifest.read_text())
    final=root/'QUALIFICATION.json';aggregate=root/'coverage.json'
    if final.exists() or aggregate.exists():raise FileExistsError('Use a new qualification output root')
    full_path=root/'stock_full_01/FULL_READ.json';fault_path=root/'faults_02/FAULTS.json'
    full=json.loads(full_path.read_text());fault=json.loads(fault_path.read_text())
    assert full['status']==fault['status']=='PASS'
    assert full['identity']['kernel_sha256']==fault['kernel_sha256']==m['kernel_sha256']
    inputs=[]
    for document in (full,fault):
        item=document['coverage'];assert pin(item['path'])['sha256']==item['sha256']
        inputs.append(json.loads(Path(item['path']).read_text()))
    counts=Counter();edges=Counter();writes=Counter();bounds={}
    for d in inputs:
        counts.update({int(a,16):n for a,n in d['instruction_counts'].items()})
        edges.update({(int(e['from'],16),int(e['to'],16)):e['count'] for e in d['edges']})
        writes.update({(int(w['address'],16),w['size'],int(w['pc'],16)):w['count'] for w in d['writes']})
        for pc,(a,b) in d['read_bounds_by_pc'].items():
            a,b=int(a,16),int(b,16);old=bounds.get(pc,(a,b));bounds[pc]=(min(a,old[0]),max(b,old[1]))
    instructions=set(m['instruction_addresses']);assert set(counts)==instructions
    branches=[]
    for i in m['instructions']:
        pc,op=i['address'],i['opcode']
        if op&0xFF00 not in (0x8900,0x8B00):continue
        disp=op&255;disp=disp-256 if disp&128 else disp
        successors=[pc+2,(pc+4+2*disp)&0xFFFFFFFF]
        assert all(edges[(pc,t)]>0 for t in successors),(pc,successors)
        branches.append({'pc':f'{pc:08X}','opcode':f'{op:04X}',
            'successors':[{'pc':f'{t:08X}','count':edges[(pc,t)]} for t in successors]})
    coverage={'schema':1,'status':'PASS','kernel_sha256':m['kernel_sha256'],
      'inputs':[full['coverage'],fault['coverage']],
      'instruction_counts':{f'{a:08X}':n for a,n in sorted(counts.items())},
      'unexecuted_instruction_addresses':[],
      'edges':[{'from':f'{a:08X}','to':f'{b:08X}','count':n} for (a,b),n in sorted(edges.items())],
      'conditional_branches':branches,'conditional_branches_covered':len(branches),
      'conditional_directions_covered':len(branches)*2,
      'writes':[{'address':f'{a:08X}','size':z,'pc':f'{pc:08X}','count':n} for (a,z,pc),n in sorted(writes.items())],
      'read_bounds_by_pc':{pc:[f'{a:08X}',f'{b:08X}'] for pc,(a,b) in sorted(bounds.items())},
      'MMIO_accesses':inputs[1]['MMIO_accesses'],
      'software_stack_bytes':0,'stack_max_bytes':max(d['stack_max_bytes'] for d in inputs),
      'private_stack_capacity_bytes':m['stack_high']-m['stack_low'],
      'hardware_exception_writes':[
          {'address':f"{m['stack_high']-4:08X}",'size':4,'value':'saved SR','origin':'explicit virtual hardware NMI entry'},
          {'address':f"{m['stack_high']-8:08X}",'size':4,'value':'saved PC','origin':'explicit virtual hardware NMI entry'}],
      'instruction_address_definition':'319 executable words only; upload header, literal pools, identity data, vectors and loader checksum word are excluded by compiled manifest',
      'unsupported_instruction_count':0,'unsupported_MMIO_count':0,
      'note':'Expected closed-world negative controls intentionally raise SimulationStop; they are separate from the admitted compiled-path unsupported counts.'}
    assert coverage['software_stack_bytes']==0 and coverage['stack_max_bytes']==8
    aggregate.write_text(json.dumps(coverage,indent=2)+'\n')
    log=io.StringIO();suite=unittest.defaultTestLoader.loadTestsFromModule(test_model)
    result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    assert result.wasSuccessful(),log.getvalue()
    logpath=root/'unit_models.log';logpath.write_text(log.getvalue())
    unit={'schema':1,'status':'PASS','groups':result.testsRun,'local_ISA_value_T_delay_checks':144,
      'log':pin(logpath),'source':pin(Path(test_model.__file__)),
      'covers':['Six project-required instruction forms with signed-bit boundaries/T preservation/delay slots',
        'Unknown opcodes/PC/MMIO, ROM/code writes and uninitialized/private-memory boundaries',
        'SSR read-one/write-zero admission and receive flag lifetime',
        'TDR/TSR two-stage buffering, TDRE-before-TEND and final completion',
        'TE0 abort of both queued and shifting bytes without fabricated output',
        'Forbidden flash controls, unsupported clock/interrupt/mode/width and inadequate declared settling interval']}
    unitpath=root/'unit_models.json';unitpath.write_text(json.dumps(unit,indent=2)+'\n')
    parity=root/'fast_parity_03.json';projection=root/'model_projection_01.json'
    for p in (parity,projection):assert json.loads(p.read_text())['status']=='PASS'
    assert sha256(CORE_PATH.read_bytes()).hexdigest()==CORE_SHA256
    report={'schema':1,'status':'PASS','artifact_class':'TEMP_RAM_ACQUISITION_TOOL',
      'software_scope':'Compiled temporary RAM kernel on strict explicitly scheduled virtual SH7058 peripherals',
      'kernel_sha256':m['kernel_sha256'],'kernel_bytes':m['kernel_bytes'],'manifest':pin(manifest),
      'coverage':pin(aggregate),'instruction_covered':len(counts),'instruction_total':len(instructions),
      'instruction_missing':[],'branches_total':len(branches),'branch_directions_covered':2*len(branches),
      'software_stack_bytes':0,'stack_max_bytes':8,'private_stack_bytes':m['stack_high']-m['stack_low'],
      'fixtures':[{'name':'exact A2WC511R stock','report':pin(full_path),'full_passes':2,
        'blocks':4096,'bytes_per_pass':0x100000,'instructions_executed':full['instructions_executed'],
        'passes':full['passes'],'executed_model_snapshot':pin(root/'model_v1/FILES.json'),
        'applicability_to_final_model':pin(projection)}],
      'faults':pin(fault_path),'compiled_fault_and_fuzz_cases':fault['case_count'],
      'closed_world_negative_controls':fault['negative_control_count'],
      'unit_models':pin(unitpath),'frozen_step_parity':pin(parity),'model_projection':pin(projection),
      'saved_model_snapshots':[pin(root/'model_v1/FILES.json'),pin(root/'model_v2/FILES.json')],
      'final_model_sources':{p.name:pin(p) for p in Path(__file__).parent.glob('*.py')},
      'frozen_core':{'path':str(CORE_PATH),'sha256':CORE_SHA256,'modified':False},
      'unsupported_executed_instruction_count':0,'unsupported_executed_MMIO_count':0,
      'allowed_MMIO':coverage['MMIO_accesses'],'physical_status':'PHYSICAL_REQUIRED','physical_operations':0,
      'limitations':[
        'No physical ECU, provider, electrical waveform, baud tolerance or silicon cycle timing has been exercised.',
        'SCI input bytes arrive under a declared schedule; explicit error flags test the error path. This is not an analog line or autonomous overrun model.',
        'TDR/TSR timing is parameterized in virtual instruction ticks. The full fixtures used the saved collapsed one-tick schedule, not the later model source; projection evidence states the exact admitted equivalence.',
        'The NMI fixture covers one hardware frame at an established non-delay RX boundary. Prefix-before-private-SP/VBR and rapid repeated/nested NMIs remain unproven physical assumptions.',
        'Private stack bound is zero software bytes plus one eight-byte hardware exception frame; no claim admits arbitrarily many pre-handler exceptions.',
        'Clock, RAM enable, prior/in-flight DMA, external watchdog and actual power/reset restoration remain entry/physical contracts.',
        'Partial requests remain pending RX without a fabricated response; host deadlines and close policy are required.',
        'Host native composite/random fixture qualification is reported separately and joined by the root validator.',
        'Full stock evidence retains compact hashes/control counters rather than every individual data-event row. Exact output equality is checked per block; the compiled fixed-range loop defines the ROM byte addresses.'
      ]}
    final.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':'PASS','report':str(final),'sha256':pin(final)['sha256'],
        'instructions':len(counts),'branches':len(branches),'stack':coverage['stack_max_bytes']}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--manifest',required=True)
    a=p.parse_args();package(a.root,a.manifest)
