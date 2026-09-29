"""Build new RK02 evidence only; retain every RK01 report and source unchanged."""
import sys
sys.dont_write_bytecode=True
import argparse,json,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent.parent
EXPECTED='3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581'
def pin(p):
    b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def check_input(item):
    path=Path(item['path']);actual=pin(path) if path.is_file() else None
    if actual and actual['sha256']==item['sha256']:
        return {'original':item,'resolution':'CURRENT_PATH_EXACT','resolved':actual}
    try:relative=path.relative_to(ROOT)
    except ValueError:raise AssertionError('Unresolved external historical input: '+str(path))
    snap=ROOT/'evidence/rk02/input_snapshot'/relative
    resolved=pin(snap);assert resolved['sha256']==item['sha256'],str(path)
    return {'original':item,'resolution':'HISTORICAL_BYTES_EXACT_IN_SNAPSHOT','resolved':resolved,'current_path_sha256':actual['sha256'] if actual else None}
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--echo-report',type=Path,required=True);args=parser.parse_args()
    base=json.loads((HERE/'OEM_ACQUISITION_CONTRACT.json').read_text())
    assert base['status']=='PASS'
    stock=Path(base['stock_rom']['path']).read_bytes()
    assert hashlib.sha256(stock).hexdigest()==base['stock_rom']['sha256']
    for block in base['reviewed_code_blocks']:
        assert hashlib.sha256(stock[int(block['start'],16):int(block['end_exclusive'],16)]).hexdigest()==block['sha256']
    build=ROOT/'build/rk02_01';binary=pin(build/'kernel.bin');assert binary['sha256']==EXPECTED
    old_names=['OEM_LOADER_REGRESSION.json','KWP_PRODUCER_REGRESSIONS.json','KWP_WIRE_CONTRACT.json','BOOT_ENTRY_REGRESSIONS.json','BOOT_SETUP_CONTRACT.json']
    new_names=['BINARY_REVIEW_rk02_01.json','UPLOAD_WIRE_CONTRACT_RK02.json','UPLOAD_NEGATIVE_CONTROLS_RK02.json']
    resolutions=[]
    for name in old_names+new_names:
        report=json.loads((HERE/name).read_text());assert report['status'].startswith('PASS'),name
        if name in new_names:
            assert report.get('kernel_sha256',EXPECTED)==EXPECTED,name
            assert any(Path(x['path'])==build/'kernel.bin' and x['sha256']==EXPECTED for x in report['inputs']),name
        if name=='UPLOAD_WIRE_CONTRACT_RK02.json':assert report['actual_upload_sha256']==EXPECTED
        resolutions.append({'report':pin(HERE/name),'inputs':[check_input(x) for x in report.get('inputs',[])]})
    # The old upload report is retained as historical evidence only. Resolve its
    # previous protocol.py bytes explicitly rather than silently checking RK02.
    historical=json.loads((HERE/'UPLOAD_WIRE_CONTRACT.json').read_text())
    historical_resolution={'report':pin(HERE/'UPLOAD_WIRE_CONTRACT.json'),'used_for_RK02_upload':False,
      'inputs':[check_input(x) for x in historical['inputs']]}
    echo=json.loads(args.echo_report.read_text())
    assert echo['kernel_sha256']==EXPECTED,'Echo evidence must bind exact RK02 binary'
    assert echo['status']=='PASS' and echo['physical'] is False
    assert echo['case_count']==len(echo['cases'])==13
    model_names={'__init__.py','core.py','cpu.py','fast_step.py','harness.py','memory.py','sci.py','self_echo.py'}
    assert set(echo['model_sources'])==model_names
    for name,digest in echo['model_sources'].items():
        assert pin(ROOT/'sim'/name)['sha256']==digest,name
    assert pin(Path(echo['coverage']['path']))['sha256']==echo['coverage']['sha256']
    for case in echo['cases']:
        identity=case['identity']
        assert identity['kernel_sha256']==EXPECTED and identity['kernel_bytes']==1808
        assert identity['model_sources']==echo['model_sources']
        assert pin(Path(identity['core_path']))['sha256']==identity['core_sha256']
        assert pin(build/'manifest.json')['sha256']==identity['manifest_sha256']
    out={k:v for k,v in base.items() if k not in ('kernel_sha256','protocol','regression_refs','loader_store_domains')}
    out['kernel_sha256']=EXPECTED;out['generation']='RK02';out['kernel']=binary
    out['protocol']={**base['protocol'],'upload_declaration':'34FF300004 + BE24(1808); fixed positive aligned length <=8192','upload_blocks':15,'kernel_identity':'A2WC511R-RK02\\0'}
    out['loader_store_domains']={**base['loader_store_domains'],'fixed_upload':'[FFFF3000,FFFF3710),452 ordered longword stores at1646'}
    out['regression_refs']=[pin(HERE/n) for n in old_names+new_names]
    out['legacy_scope']='Reuses only unchanged actual-stock dispatch/security, IRQ-mask, quiescence and boot semantics. RK01 binary/upload is not approval evidence for RK02.'
    out['reused_source_provenance']=resolutions
    out['historical_upload_provenance']=historical_resolution
    out['independent_binary_review']={'report':pin(HERE/'BINARY_REVIEW_rk02_01.json'),'instructions':335,'store_sites':22,'RAM_store_sites':4,'MMIO_store_sites':18,'flash_stores':0,'private_RAM':['FFFF3710','FFFF3730']}
    out['actual_stock_upload']={'report':pin(HERE/'UPLOAD_WIRE_CONTRACT_RK02.json'),'frames':17,'instructions':479183,'ordered_longword_stores':452,'entry':'FFFF3004','SP':'FFFFBFA0','SR_I':15}
    out['SCI_half_duplex']={'status':'PASS_SCOPED_SOFTWARE_CONTRACT','static':'SCR20 at3202 disables RE before reply. SSR78 residual/error guard precedes firstTDR. Every reply drains actualTEND at3284 before SCR10 at3278. TX/drain timeout is terminal SCR0.',
      'independent_static_report':pin(HERE/'BINARY_REVIEW_rk02_01.json'),'simulator_report':pin(args.echo_report.resolve()),
      'prior_defect_retained':pin(HERE/'SCI_SELF_ECHO_CONTRACT.json'),
      'limits':'Physical line propagation/turnaround, incomplete incoming byte at RE0, real adapter and silicon timing remain explicit physical conditions. Host J2534 echo is a separate layer.'}
    out['generator']=pin(Path(__file__))
    (HERE/'OEM_ACQUISITION_CONTRACT_RK02.json').write_text(json.dumps(out,indent=2)+'\n')
    paths=[HERE/n for n in ('review_binary_rk02.py','BINARY_REVIEW_rk02_01.json','BINARY_REVIEW_RK02.md','verify_upload_wire_rk02.py','UPLOAD_WIRE_CONTRACT_RK02.json','UPLOAD_WIRE_RK02_TRACE.json.gz','verify_upload_negative_rk02.py','UPLOAD_NEGATIVE_CONTROLS_RK02.json','finalize_contracts_rk02.py','OEM_ACQUISITION_CONTRACT_RK02.json')]
    manifest={'schema':1,'scope':'New independent RK02 evidence only; no RK01 mutation','kernel_sha256':EXPECTED,'files':[pin(p) for p in paths]}
    (HERE/'RK02_FILES.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'new_files':len(paths),'kernel_sha256':EXPECTED,'reused_reports':len(old_names)}))
if __name__=='__main__':main()
