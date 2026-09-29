from __future__ import annotations
import hashlib,json,os,struct,subprocess,sys,tempfile,unittest,zipfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import package_acceptance
import audit_dev,codex_model_probe as probe,setup_cdev,release_check,run_build_plan,run_codex

class ModelTests(unittest.TestCase):
 def models(self):return [{'id':'astra-id','model':'gpt-6-astra','displayName':'GPT-6 Astra','hidden':False,'supportedReasoningEfforts':[{'reasoningEffort':'high'},{'reasoningEffort':'ultra'}]}]
 def test_exact_model_effort(self):self.assertEqual(probe.selected_model(self.models())['effort'],'ultra')
 def test_no_model_substitution(self):self.assertRaises(ValueError,probe.selected_model,self.models(),'unadvertised-model')
 def test_no_effort_substitution(self):self.assertRaises(ValueError,probe.selected_model,self.models(),'gpt-6-astra','infinite')
 def test_hidden_model(self):
  m=self.models();m[0]['hidden']=True;self.assertRaises(ValueError,probe.selected_model,m)
 def test_slim_usage_drops_account_secrets(self):
  r=probe.slim_usage({'token':'secret','credits':{'id':'secret'},'rateLimits':{'limitId':'codex','primary':{'usedPercent':12,'private':'secret'}}})
  self.assertNotIn('secret',json.dumps(r));self.assertEqual(r['rateLimits']['primary']['usedPercent'],12)
 def test_real_metadata_stdio_no_task(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'fake.py';p.write_text('''import sys,json
initialized=False
for line in sys.stdin:
 r=json.loads(line);m=r.get("method")
 if m=="initialized": initialized=True;continue
 if m=="initialize": out={"platformOs":"test"}
 elif m=="model/list" and initialized:out={"data":[],"nextCursor":None}
 else:out={"unexpected":True}
 print(json.dumps({"id":r.get("id"),"result":out}),flush=True)
''')
   c=probe.MetadataClient([sys.executable,str(p)],Path(td),timeout=3)
   try:
    c.initialize();self.assertEqual(c.request('model/list',{})['data'],[])
    self.assertRaises(ValueError,c.request,'turn/start',{})
    self.assertRaises(ValueError,c.request,'thread/start',{})
    self.assertEqual(c.methods,['initialize','model/list'])
   finally:c.close()

class SetupTests(unittest.TestCase):
 def test_root_block_idempotent(self):
  old='# User original\nKeep this.\n';block=setup_cdev.root_instructions(Path('/dev'),Path('/dev/Astra_A2WC511R'))
  once=setup_cdev.put_block(old,block);self.assertEqual(setup_cdev.put_block(once,block),once);self.assertIn(old,once)
 def test_config_preserves_other_tables(self):
  old='model = "old-model"\n[mcp_servers.other]\ncommand = "other.exe"\n'
  once=setup_cdev.replace_tables(old,{'mcp_servers.romraider':'[mcp_servers.romraider]\ncommand = "new.exe"\n'})
  self.assertIn('command = "other.exe"',once)
  twice=setup_cdev.replace_tables(once,{'mcp_servers.romraider':'[mcp_servers.romraider]\ncommand = "new.exe"\n'})
  self.assertEqual(once,twice)
 def test_rejects_inline_config_overwrite(self):
  self.assertRaises(ValueError,setup_cdev.replace_tables,'mcp_servers={romraider={command="old"}}',{'mcp_servers.romraider':'[mcp_servers.romraider]\ncommand="new"\n'})
 def test_backups_retain_original(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);p=d/'AGENTS.md';p.write_bytes(b'ORIGINAL\r\n')
   r=setup_cdev.backup_write(p,'NEW\n',d/'backups');self.assertEqual(Path(r['backup']).read_bytes(),b'ORIGINAL\r\n')
 def test_installs_only_expected_root_files(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);pkg=d/'Astra_A2WC511R';(pkg/'config').mkdir(parents=True);py=d/'python.exe';py.write_bytes(b'fake')
   r=setup_cdev.install(d,pkg,py);self.assertTrue((d/'AGENTS.md').is_file());self.assertTrue((d/'.codex/config.toml').is_file());self.assertFalse((d/'MerpMod').exists())

class AuditTests(unittest.TestCase):
 def test_elf_big_endian_sh2e(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'x';d=bytearray(52);d[:7]=b'\x7fELF\x01\x02\x01';struct.pack_into('>HHIIIIIHHHHHH',d,16,2,42,1,0xe00000,0,0,11,52,0,0,0,0,0);p.write_bytes(d)
   r=audit_dev.elf_header(p);self.assertEqual(r['sh_machine_nibble'],11);self.assertEqual(r['byte_order'],'big')
 def test_actual_uploaded_baseline_and_four_byte_diff(self):
  with zipfile.ZipFile(ROOT/'evidence/Dev_2026-09-25_original.zip') as z:
   a=z.read('Dev/SubaruRoms/OEM/A2WC511R.bin');b=z.read('Dev/SubaruRoms/OEM/A2WC511R_STOCK_ROMRAIDER.bin')
   self.assertEqual(hashlib.sha256(a).hexdigest(),audit_dev.BASELINE)
   self.assertEqual([i for i in range(len(a)) if a[i]!=b[i]],list(range(0xFFC4C,0xFFC50)))
 def test_actual_audit_wrong_target(self):
  r=json.loads((ROOT/'reports/dev_snapshot/dev_audit.json').read_text())
  self.assertEqual(r['generated_build']['TargetHeader.h']['ECU_CALIBRATION_ID'],'A8DH202X')
  self.assertEqual(r['generated_build']['TargetConfig.h']['AUTO_TRANS'],'0')
  self.assertEqual(r['generated_build']['A2WC511R_target_files'],[])

class BuildTests(unittest.TestCase):
 def plan(self,base,out,exitcode=0,output=True):
  code='from pathlib import Path\n'+("Path(r'"+str(out/'made.txt')+"').write_text('made')\n" if output else '')+f'raise SystemExit({exitcode})\n'
  src=base/'job.py';src.write_text(code)
  return {'target_calid':'A2WC511R','reviewed':True,'inputs':[{'path':'job.py','sha256':hashlib.sha256(src.read_bytes()).hexdigest()}],
    'steps':[{'name':'test','argv':[sys.executable,str(src)],'exe_sha256':hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),'outputs':['${OUT}/made.txt']}]}
 def test_fresh_artifact_success(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);out=d/'new';self.assertTrue(run_build_plan.run(self.plan(d,out),d,out)['passed'])
 def test_failed_native_command_not_banner(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);out=d/'new';self.assertFalse(run_build_plan.run(self.plan(d,out,1),d,out)['passed'])
 def test_missing_output_rejects_zero_exit(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);out=d/'new';self.assertFalse(run_build_plan.run(self.plan(d,out,0,False),d,out)['passed'])
 def test_stale_run_directory_refused(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);out=d/'new';plan=self.plan(d,out);out.mkdir();self.assertRaises(ValueError,run_build_plan.run,plan,d,out)

class ReleaseTests(unittest.TestCase):
 def fixture(self,d):
  x=bytearray(b'\xff'*0x100000);x[0x2000:0x2008]=b'A2WC511R';x[0xCDAD8:0xCDADD]=bytes.fromhex('2F12515306');a=d/'base.bin';a.write_bytes(x)
  y=x[:];y[0xE1000]=1;b=d/'candidate.bin';b.write_bytes(y)
  desc=lambda p:{'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
  reviews={}
  for name in release_check.REQUIRED_REVIEWS:
   p=d/(name+'.md');p.write_text('Synthetic engineering review fixture, never a real vehicle approval. '+name);reviews[name]=desc(p)
  return {'target_calid':'A2WC511R','target_ecuid':'2F12515306','scope':'diagnostic_only','baseline':desc(a),'candidate':desc(b),
  'expected_output_identity':{'calid':'A2WC511R','ecuid':'2F12515306'},'allowed_changes':[{'start':'0xE1000','end_exclusive':'0xE1001','purpose':'synthetic change','review_key':'rom_allocation','baseline_range_sha256':hashlib.sha256(b'\xff').hexdigest()}],'reviews':reviews}
 def test_linked_envelope_not_physical_certificate(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);r=release_check.check(self.fixture(d),d);self.assertTrue(r['envelope_passed']);self.assertIn('HUMAN_REVIEW_REQUIRED',r['status']);self.assertTrue(r['not_checked_here'])
 def test_outside_allowlist(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);m=self.fixture(d);m['allowed_changes'][0]['start']='0xE1001';m['allowed_changes'][0]['end_exclusive']='0xE1002';self.assertFalse(release_check.check(m,d)['envelope_passed'])
 def test_missing_review(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);m=self.fixture(d);m['reviews'].pop('ram_allocation');self.assertFalse(release_check.check(m,d)['envelope_passed'])
 def test_modified_review(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);m=self.fixture(d);(d/'ram_allocation.md').write_text('Changed');self.assertFalse(release_check.check(m,d)['envelope_passed'])
 def test_noop_candidate(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);m=self.fixture(d);m['candidate']=m['baseline'];self.assertFalse(release_check.check(m,d)['envelope_passed'])

class LaunchTests(unittest.TestCase):
 def test_command_full_access_root_and_ultra(self):
  c=run_codex.command('codex.exe',r'C:\Dev','gpt-6-astra','ultra','batch',None,Path('/reports'))
  self.assertIn('danger-full-access',c);self.assertIn('never',c);self.assertIn('--skip-git-repo-check',c);self.assertIn('model_reasoning_effort="ultra"',c);self.assertNotIn('--ephemeral',c);self.assertEqual(c[-1],'-')
 def test_explicit_same_session_resume(self):
  c=run_codex.command('codex.exe',r'C:\Dev','gpt-6-astra','ultra','batch','session_12345',Path('/reports'))
  self.assertIn('session_12345',c);self.assertIn('resume',c);self.assertNotIn('--last',c)
 def test_changed_cli_fails_readiness(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);p=d/'codex.exe';p.write_bytes(b'fake');dt=datetime.now(timezone.utc).isoformat()
   r={'ready_to_start_offline_port':True,'generated_at':dt};m={'ready_for_model_run':True,'generated_at':dt,'codex_exe':str(p),'codex_sha256':'bad','cwd':str(d),'selected':{'model':'gpt-6-astra','effort':'ultra'}}
   self.assertRaises(ValueError,run_codex.validate_readiness,r,m,p,d)


class IntegrityTests(unittest.TestCase):
 def fixture(self,d):
  (d/'evidence').mkdir();(d/'evidence/original.txt').write_bytes(b'evidence');(d/'state.md').write_bytes(b'initial')
  files=[{'path':p.relative_to(d).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':p.stat().st_size} for p in (d/'evidence/original.txt',d/'state.md')]
  (d/'PACKAGE_MANIFEST.json').write_text(json.dumps({'files':files}))
 def test_initial_all_hashes_checked(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);self.fixture(d);r=package_acceptance.check(d);self.assertTrue(r['initial_acceptance']);self.assertEqual(r['checked_files'],2)
 def test_workspace_edits_do_not_break_resume(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);self.fixture(d);package_acceptance.check(d);(d/'state.md').write_text('checkpoint updated');r=package_acceptance.check(d);self.assertFalse(r['initial_acceptance']);self.assertEqual(len(r['workspace_changes']),1)
 def test_original_evidence_still_immutable(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);self.fixture(d);package_acceptance.check(d);(d/'evidence/original.txt').write_text('changed');self.assertRaises(ValueError,package_acceptance.check,d)
 def test_modified_pristine_package_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);self.fixture(d);(d/'state.md').write_text('changed');self.assertRaises(ValueError,package_acceptance.check,d)

if __name__=='__main__':unittest.main()
