"""Qualify offline validator against retained new-PE journals and targeted mutations."""
from pathlib import Path
import json,hashlib,subprocess,datetime
from validate_final import validate,rows
A=Path(__file__).resolve().parent;R=Path(r'C:\Dev\A2WC511R_RK03_FinalTwoPass128\final_two_pass_128')
def pin(p):
 p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
cp=A/'FINAL_TWO_PASS_REVIEW_CONTRACT.json';c=read(cp);c['_sha256']=pin(cp)['sha256'];reference=Path(c['current_reference']['path']).read_bytes()
reportpath=Path(read(R/'reports/LATEST_QUALIFICATION.json')['report']['path']);report=read(reportpath);checks=[]
for case in report['cases']:
 path=case['journal']['path']
 try:
  result,images=validate(rows(path),c,reference,False)
 except ValueError as e:
  assert not case['positive'],(case['case'],str(e));checks.append(dict(case='retained_'+case['case'],status='PASS',expect='REJECT',reason=str(e)))
 else:
  assert case['positive'];assert all(Path(p['path']).read_bytes()==b for p,b in zip(case['images'],images))
  assert result['result']['pass0_vs_current']['identical'] is (case['case']!='success_changed_current')
  checks.append(dict(case='retained_'+case['case'],status='PASS',expect='ACCEPT',result=result['result']))
base=next(x for x in report['cases'] if x['mode']=='real_clock')['journal']['path']
def modified(kind):
 done=False
 for r in rows(base):
  typ=r.get('type')
  if not done:
   if kind=='startup_hash' and typ=='full_read_start':r['contract_sha256']='0'*64;done=True
   elif kind=='wrong_backend' and typ=='full_read_start':r['physical']=True;done=True
   elif kind=='missing_startup' and typ=='full_read_start':done=True;continue
   elif kind in ('API_sequence','API_status','API_clock') and typ=='api_return':
    if kind=='API_sequence':r['sequence']+=1
    elif kind=='API_status':r['status']=16
    else:r['api_elapsed_ticks']+=1
    done=True
   elif kind in ('block_address','block_length','block_payload','block_checksum','block_duplicate','block_missing','block_reordered','pass_mismatch') and typ=='rom_block':
    if kind=='block_address':r['address']=128
    elif kind=='block_length':r['length']=129
    elif kind in ('block_payload','block_checksum'):
     b=bytearray.fromhex(r['response_hex']);b[10 if kind=='block_payload' else -1]^=1;r['response_hex']=b.hex()
    elif kind=='block_duplicate':yield r
    elif kind=='block_missing':done=True;continue
    elif kind=='block_reordered':r['read_index']=1
    else:r['pass0_match']=False
    done=True
   elif kind in ('final_hash','output_length','baseline_claim','missing_final') and typ=='full_read_result':
    if kind=='final_hash':r['pass1_sha256']='0'*64
    elif kind=='output_length':r['pass0_bytes']-=1
    elif kind=='baseline_claim':r['pass0_vs_current']['identical']=False
    else:done=True;continue
    done=True
   elif kind in ('cleanup_failed','extra_TX_count','missing_terminal') and typ=='probe_terminal':
    if kind=='cleanup_failed':r['cleanup_confirmed']=False
    elif kind=='extra_TX_count':r['state']['tx_attempts']+=1
    else:done=True;continue
    done=True
  yield r
 assert done,kind
 if kind=='after_terminal':yield dict(type='rom_block')
mutations=['startup_hash','wrong_backend','missing_startup','API_sequence','API_status','API_clock','block_address','block_length','block_payload','block_checksum','block_duplicate','block_missing','block_reordered','pass_mismatch','final_hash','output_length','baseline_claim','missing_final','cleanup_failed','extra_TX_count','missing_terminal']
for name in mutations:
 try:validate(modified(name),c,reference,False)
 except ValueError as e:checks.append(dict(case='tamper_'+name,status='PASS',expect='REJECT',reason=str(e)))
 else:raise AssertionError('Accepted mutation '+name)
out=A/'validator_cli';out.mkdir(exist_ok=False)
exe=Path(report['physical_executable']['path'])
for option,value in [('--address','128'),('--length','512'),('--passes','3'),('--kernel','alternate.bin'),('--entry','FFFF3008'),('--retry','1')]:
 argv=[str(exe),'--offline-fixture','success','--journal',str(out/'never_created.jsonl'),option,value]
 run=subprocess.run(argv,capture_output=True,text=True,timeout=10)
 assert run.returncode==2 and not (out/'never_created.jsonl').exists(),option
 checks.append(dict(case='reject_CLI_'+option,status='PASS',expect='REJECT_BEFORE_PROVIDER',exit_code=run.returncode,stderr=run.stderr))
result=dict(status='PASS',test_cases=len(checks),passed_cases=len(checks),physical_operations=0,real_provider_loads=0,scope='38_RETAINED_NATIVE_CASES_PLUS_VALIDATOR_TAMPER_AND_FAKE_CLI_BOUNDS',checks=checks,files=[pin(p) for p in [Path(__file__),A/'validate_final.py',reportpath,cp,exe]],native_test_reruns=0)
with (A/'FINAL_VALIDATOR_TESTS.json').open('x',encoding='utf8',newline='\n') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(status='PASS',cases=len(checks),report=pin(A/'FINAL_VALIDATOR_TESTS.json'))))
