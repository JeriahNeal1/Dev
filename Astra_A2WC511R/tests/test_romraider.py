from __future__ import annotations
import copy,importlib.util,io,json,math,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'integrations/romraider_mcp'))
import core as rr
spec=importlib.util.spec_from_file_location('rr_server',ROOT/'integrations/romraider_mcp/server.py');server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)

def table(key,values,static=False):
 return {'key':key,'name':key,'rows':len(values),'columns':len(values[0]),'static':static,'locked':False,'edit_capability':'static_not_rom_backed' if static else 'numeric_native_preview_required','scale':{'units':'unit'},'cells':[[{'real':float(v),'raw':None if static else float(v),'static_text':str(v) if static else None} for v in row]for row in values]}
def snapshot():
 return {'schema':'rr-model-snapshot-v1','captured_utc':'2026-09-25T00:00:00Z','bridge_session':'session','rom':{'rom_id':'rom_1','binary_sha256':'a'*64,'calid':'A2WC511R'},'model_sha256':'b'*64,'tables':[table('Surface',[[10,20],[30,40]]),table('Surface::x',[[0,1]],True),table('Surface::y',[[0,1]],True)]}
class MockBridge:
 def request(self,op,args):
  if op=='snapshot':return snapshot()
  if op=='status':return {'session':'session','roms':[]}
  if op=='preview':return {'preview_id':'test','changes':args['changes'],'rom_restored':True}
  raise ValueError(op)
class Tests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.store=rr.Store(self.root,MockBridge());self.sid=self.store.put('snapshots',snapshot())
 def tearDown(self):self.temp.cleanup()
 def ingest(self,content='t,x,y,metric,rpm\n0,0,0,1,700\n10,0.5,0.5,2,700\n20,1,1,3,700\n'):
  (self.root/'log.csv').write_text(content);return self.store.ingest_log('log.csv',self.sid,'user_attested_applied_rom','operator test')['log_id']
 def overlay(self,lid,**kwargs):
  args=dict(log_id=lid,table_key='Surface',bindings={a:{'column':a,'unit':'unit','factor':1,'offset':0}for a in ('x','y')},metric_column='metric',time_column='t',time_unit='ms',filters=[],active_table_evidence='synthetic fixture')
  args.update(kwargs);return self.store.overlay(**args)
 def calc(self,**kwargs):
  q=dict(snapshot_id=self.sid,table_key='Surface',expression='old + adjustment',cells=[{'row':0,'column':0}],constants={'adjustment':1},constraints={'minimum':0,'maximum':100,'max_abs_delta':2,'min_samples':0,'tolerance':.1},reason='unit test, not vehicle tune',evidence=['synthetic'])
  q.update(kwargs);return self.store.calculate(**q)
 def test_expression(self):self.assertEqual(rr.safe_expression('min(old*factor, 20)',{'old':10,'factor':1.1}),11)
 def test_expression_no_execution(self):
  for s in ['__import__("os")','old.__class__','[x for x in range(10)]','2**100000','True','1/0','exp(10000)']:
   with self.assertRaises((ValueError,SyntaxError,ZeroDivisionError,OverflowError)):rr.safe_expression(s,{'old':1})
 def test_axis_ascending_descending(self):
  self.assertEqual(rr.bracket([0,1],.5),[(0,.5),(1,.5)]);self.assertEqual(rr.bracket([1,0],.5),[(1,.5),(0,.5)]);self.assertIsNone(rr.bracket([0,1],2))
 def test_bad_axis(self):
  for a in [[0,0],[0,2,1],[float('nan')]]:
   with self.assertRaises(ValueError):rr.validate_axis(a)
 def test_immutable_records(self):
  p=self.store.home/'snapshots'/(self.sid+'.json');p.write_text('{}')
  with self.assertRaises(ValueError):self.store.get('snapshots',self.sid)
 def test_paths(self):
  for p in ['../notmine','.runtime/token','/etc/passwd']:
   with self.assertRaises(ValueError):self.store.inside(p)
 def test_capture(self):self.assertEqual(self.store.capture('rom_1','baseline')['tables_and_axes'],3)
 def test_compare_axis_change(self):
  b=snapshot();b['tables'][0]['cells'][0][0]['real']=12;b['tables'][1]['cells'][0][1]['real']=2
  bid=self.store.put('snapshots',b);out=self.store.compare(self.sid,bid);r=self.store.get('comparisons',out['comparison_id']);surface=next(x for x in r['tables']if x['table']=='Surface');self.assertFalse(surface['axes_equal']);self.assertFalse(surface['cellwise_meaning_comparable'])
 def test_ingest_requires_association(self):
  self.ingest()
  with self.assertRaises(ValueError):self.store.ingest_log('log.csv',self.sid,'filename_date','bad')
 def test_partial_csv(self):
  h,r,p=rr.csv_rows(b't,x\n0,1\n2,');self.assertEqual(len(r),2) # Complete column count: retained missing values are later filtered.
  h,r,p=rr.csv_rows(b't,x\n0,1\n2');self.assertTrue(p);self.assertEqual(len(r),1)
 def test_duplicate_header(self):
  with self.assertRaises(ValueError):rr.csv_rows(b'x,x\n1,2\n')
 def test_bilinear_timeline(self):
  lid=self.ingest();out=self.overlay(lid);o=self.store.get('overlays',out['overlay_id']);self.assertEqual(o['accepted_samples'],3);self.assertEqual(o['timeline'][1]['table_lookup_estimate'],25);self.assertEqual(len(o['timeline'][1]['cell_weights']),4);self.assertEqual(len(o['cells']),4);self.assertTrue(Path(out['timeline_csv']).is_file());self.assertTrue(Path(out['html_report']).is_file())
 def test_unit_guard(self):
  lid=self.ingest();bindings={a:{'column':a,'unit':'WRONG','factor':1,'offset':0}for a in ('x','y')}
  with self.assertRaises(ValueError):self.overlay(lid,bindings=bindings)
 def test_timing_reset(self):
  lid=self.ingest('t,x,y,metric,rpm\n10,0,0,1,700\n0,1,1,2,700\n')
  with self.assertRaises(ValueError):self.overlay(lid)
 def test_filter_and_outside(self):
  lid=self.ingest('t,x,y,metric,rpm\n0,0,0,1,500\n10,2,2,2,700\n20,1,1,3,700\n');out=self.overlay(lid,filters=[{'column':'rpm','min':650,'max':800}]);self.assertEqual(out['accepted_samples'],1);self.assertEqual(out['skipped']['axis_outside'],1)
 def test_delay_direction(self):
  out=self.overlay(self.ingest(),metric_delay_ms=10,max_alignment_gap_ms=0);o=self.store.get('overlays',out['overlay_id']);self.assertEqual(o['accepted_samples'],2);self.assertEqual(o['timeline'][0]['metric'],2);self.assertEqual(o['timeline'][0]['metric_time_ms'],10)
 def test_calculation_preserves_other_cells(self):
  out=self.calc();p=self.store.get('proposals',out['proposal_id']);self.assertEqual(len(p['changes']),1);self.assertEqual(p['changes'][0]['value'],11);self.assertEqual(self.store.get('snapshots',self.sid)['tables'][0]['cells'][0][0]['real'],10)
 def test_constraints_reject_no_clamp(self):
  out=self.calc(constants={'adjustment':10});self.assertEqual(out['changed_cells'],0);self.assertEqual(out['rejected_cells'][0]['reason'],'constraint_violation')
 def test_insufficient_data_preserves(self):
  out=self.calc(constraints={'minimum':0,'maximum':100,'max_abs_delta':2,'min_samples':10,'tolerance':.1});self.assertEqual(out['changed_cells'],0)
 def test_overlay_formula(self):
  ov=self.overlay(self.ingest());out=self.calc(expression='old + mean',constants={},overlay_id=ov['overlay_id']);self.assertEqual(out['changed_cells'],1);self.assertAlmostEqual(self.store.get('proposals',out['proposal_id'])['changes'][0]['value'],11.2)
 def test_formula_missing_value(self):
  with self.assertRaises(ValueError):self.calc(expression='old+mean')
 def test_preset(self):
  s=snapshot();s['tables'].append(table('Switch',[[0,0]]));s['tables'][-1]['presets']=[{'name':'Example','offset':0,'data':[18,52]}];sid=self.store.put('snapshots',s);o=self.store.preset_proposal(sid,'Switch','Example','test',['fixture']);p=self.store.get('proposals',o['proposal_id']);self.assertEqual(p['changes'][1]['value'],52);self.assertEqual(p['changes'][1]['mode'],'raw')
 def test_preview_session(self):
  out=self.calc();res=self.store.preview(out['proposal_id']);self.assertTrue(res['rom_restored']);s=snapshot();s['bridge_session']='different';sid=self.store.put('snapshots',s);out=self.calc(snapshot_id=sid)
  with self.assertRaises(ValueError):self.store.preview(out['proposal_id'])
 def test_bridge_rejects_nonlocal(self):
  p=self.root/'conn.json'
  for u in ['http://evil.example/rpc','https://127.0.0.1:9/rpc','http://127.0.0.1:9/rpc?q=x','http://u:p@127.0.0.1:9/rpc']:
   p.write_text(json.dumps({'url':u,'token':'x'*64}))
   with self.assertRaises(ValueError):rr.Bridge(p).request('status',{})
 def test_mcp_handshake(self):
  q=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18'}},{'jsonrpc':'2.0','id':2,'method':'tools/list'},{'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'rr_status','arguments':{}}}];o=io.StringIO();server.serve(self.store,io.StringIO('\n'.join(map(json.dumps,q))),o);a=[json.loads(x)for x in o.getvalue().splitlines()];self.assertEqual(len(a[1]['result']['tools']),13);self.assertFalse(a[2]['result']['isError'])
if __name__=='__main__':unittest.main()
