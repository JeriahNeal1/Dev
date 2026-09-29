"""Clean-process acceptance of the pinned read-only validator; no new ROMs."""
import sys
sys.dont_write_bytecode=True
import argparse,json,subprocess
from pathlib import Path
import validator as v
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    out=a.output_dir.resolve();out.mkdir(parents=True,exist_ok=False);cwd=out/'unrelated cwd with spaces';cwd.mkdir()
    registry=v.load_registry();rows=[]
    for label,key,expected,code in [('stock','stock','CONDITIONAL',2),('one_page','one_page','FAIL',3),('two_pages','two_pages','FAIL',3),('stock_repeat','stock','CONDITIONAL',2)]:
        image=registry['artifacts'][key]['image']['path'];job=out/label
        argv=[sys.executable,'-B',str(Path(v.__file__).resolve()),image,'--output-dir',str(job)]
        run=subprocess.run(argv,cwd=cwd,capture_output=True,text=True,timeout=60)
        (out/(label+'.process.log')).write_text(json.dumps(argv)+'\n'+run.stdout+'\n'+run.stderr)
        assert run.returncode==code,(label,run.returncode,run.stdout,run.stderr)
        d=json.loads((job/'VALIDATION.json').read_text());assert d['status']==expected and d['input_unchanged'] is True and not d['flash_authorized']
        failed=[x['id'] for x in d['checks'] if x['status']=='FAIL']
        assert failed==([] if key=='stock' else ['RESIDENCY_OWNERSHIP']),(label,failed)
        assert next(c for c in d['checks'] if c['id']=='STOCK_VS_CANDIDATE_BOOT_PREFIX')['status']=='PASS'
        assert next(c for c in d['checks'] if c['id']=='BOOT_PATH')['status']=='CONDITIONAL'
        assert next(c for c in d['checks'] if c['id']=='SSM_STARTUP_READINESS')['status']=='CONDITIONAL'
        rows.append({'label':label,'status':d['status'],'exit_code':run.returncode,'report':str(job/'VALIDATION.json'),
                     'sha256':v.digest((job/'VALIDATION.json').read_bytes()),'deterministic_verdict_sha256':d['deterministic_verdict_sha256'],'failed_checks':failed,
                     'boot_stop':d['boot_summary']['candidate']['stop']})
        print(label,d['status'],flush=True)
    assert rows[0]['deterministic_verdict_sha256']==rows[3]['deterministic_verdict_sha256']
    result={'schema':1,'status':'PASS','runs':rows,'stock_clean_process_repeat_equal':True,'cwd_contains_spaces':True,
            'registry_sha256':v.REGISTRY_SHA256,'validator_sha256':v.digest(Path(v.__file__).read_bytes()),'new_ROM_images_created':False,'physical_or_provider_access':False}
    (out/'ACCEPTANCE.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':'PASS','report':str(out/'ACCEPTANCE.json')}))
if __name__=='__main__':main()
