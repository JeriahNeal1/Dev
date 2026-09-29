from __future__ import annotations
import contextlib,importlib.util,io,json,os,subprocess,sys,tempfile,threading,types,unittest
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import project_core as core

def module(path,name):
 spec=importlib.util.spec_from_file_location(name,path);obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj
PROJECT=module(ROOT/'integrations/project_mcp/server.py','project_server_test')

class CoreTests(unittest.TestCase):
 def test_nibble_decoding(self):
  for n in range(8):self.assertEqual(core.gear_decode(n),n)
  self.assertEqual(core.gear_decode(8,5),0)
  for n in range(9,16):self.assertEqual(core.gear_decode(n,5),5)
  with self.assertRaises(ValueError):core.gear_decode(16)
 def test_paths(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td).resolve();self.assertEqual(core.resolve_inside(root,'data.txt'),root/'data.txt')
   for path in ('../outside','./.runtime/ida_connection.json','.git/config','.codex/config.toml'):
    with self.assertRaises(ValueError):core.resolve_inside(root,path)
 def test_rom_audit_and_diff(self):
  with tempfile.TemporaryDirectory() as td:
   a=Path(td)/'a.bin';b=Path(td)/'b.bin';data=bytearray(b'\xff'*0x100000)
   data[0x2000:0x2009]=b'A2WC511R\0';data[0xCDAD8:0xCDADD]=bytes.fromhex(core.ECU_ID)
   for ea,(expected,_) in core.HOOKS.items():data[ea:ea+4]=expected.to_bytes(4,'big')
   a.write_bytes(data);r=core.rom_audit(a);self.assertTrue(r['identity_matches']);self.assertTrue(all(x['matches'] for x in r['hook_old_values']))
   data[100]=0;data[101]=0;b.write_bytes(data);d=core.binary_diff(a,b)
   self.assertEqual(d['changed_byte_positions'],2);self.assertEqual(d['total_ranges'],1)
   self.assertFalse(d['identical']);self.assertTrue(core.binary_diff(a,a)['identical'])
 def test_csv(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'a.csv';p.write_text('Time (msec),Value\n0,3\n36,4\n72,4\n',encoding='utf-8')
   r=core.csv_summary(p);self.assertEqual(r['rows'],3);self.assertEqual(r['time']['median_interval_ms'],36)
   p.write_text('x,x\n1,2\n');self.assertRaises(ValueError,core.read_csv,p)
 def test_header_only(self):
  p=ROOT/'evidence/original/romraiderlog_20260824_131151.csv';self.assertTrue(core.csv_summary(p)['header_only'])
 def test_actual_latest_xml(self):
  r=core.logger_validate(ROOT/'definitions/logger_STD_EN_v370_A2WC511R_tcu_validity_test.xml');self.assertTrue(r['required_pass'])
 def test_actual_packed_log(self):
  r=core.gear_log_analysis(ROOT/'evidence/original/romraiderlog_20260824_143124.csv')
  self.assertEqual(r['rows'],6453);self.assertEqual(r['comparisons']['lower_vs_BC2']['mismatches'],0)
  self.assertEqual(r['comparisons']['upper_vs_BC1']['mismatches'],28)
 def test_project_mcp_handshake(self):
  req=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18'}},
       {'jsonrpc':'2.0','method':'notifications/initialized'},
       {'jsonrpc':'2.0','id':2,'method':'tools/list'},
       {'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'logger_validate','arguments':{'path':'definitions/logger_STD_EN_v370_A2WC511R_tcu_validity_test.xml'}}},
       {'jsonrpc':'2.0','id':4,'method':'tools/call','params':{'name':'csv_summary','arguments':{'path':'../not-allowed'}}}]
  inp=io.StringIO('\n'.join(map(json.dumps,req))+'\n');out=io.StringIO();PROJECT.serve(ROOT,inp,out)
  rs=[json.loads(s) for s in out.getvalue().splitlines()]
  self.assertEqual(len(rs),4);self.assertEqual(rs[0]['result']['protocolVersion'],'2025-06-18')
  self.assertEqual(len(rs[1]['result']['tools']),5);self.assertFalse(rs[2]['result']['isError']);self.assertTrue(rs[3]['result']['isError'])
 def test_project_stdio_process(self):
  req={'jsonrpc':'2.0','id':1,'method':'initialize','params':{}}
  p=subprocess.run([sys.executable,str(ROOT/'integrations/project_mcp/server.py'),'--root',str(ROOT)],input=json.dumps(req)+'\n',text=True,capture_output=True,timeout=20)
  self.assertEqual(p.returncode,0);self.assertEqual(json.loads(p.stdout)['id'],1);self.assertEqual(p.stderr,'')

if __name__ == '__main__': unittest.main()
