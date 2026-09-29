"""Exercise hardened coverage gates with their genuine sealed inputs present."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
# Reuse only the reviewed deterministic index construction, not its test loop
# or report writer. This source is local project test code, not external input.
scope={'__file__':str(HERE/'retest.py')}
source=(HERE/'retest.py').read_text().split('out=[]')[0]
exec(compile(source,str(HERE/'retest.py'),'exec'),scope)
v,index,item,ROOT=scope['v'],scope['index'],scope['item'],scope['ROOT']
import json
for p in (ROOT/'evidence/sim/stock_full_01/coverage.json',ROOT/'evidence/sim/faults_02/coverage.json'):
    index['files'].append(item(p))
base=v.validate(index)
byname={x['gate']:x for x in base['checks']}
positive=['COVERAGE_BINARY_IDENTITY','COVERAGE_AGGREGATE_RECONCILIATION','ALL_EMITTED_INSTRUCTIONS',
          'ALL_CONDITIONAL_DIRECTIONS','EXACT_STACK_BOUND','EVERY_OBSERVED_STORE_DECLARED']
assert all(byname[g]['status']=='PASS' for g in positive),byname
cp=ROOT/'evidence/sim/validator_review_01/coverage_wrong_identity_empty_writes_unreviewed_entry.json'
index['files'].append(item(cp));index['aggregate_coverage']=str(cp)
negative=v.validate(index);bynegative={x['gate']:x for x in negative['checks']}
expected=['COVERAGE_BINARY_IDENTITY','COVERAGE_AGGREGATE_RECONCILIATION',
          'ALL_EMITTED_INSTRUCTIONS','EVERY_OBSERVED_STORE_DECLARED']
assert all(bynegative[g]['status']=='FAIL' for g in expected),bynegative
report={'schema':1,'status':'PASS','validator_source':item(ROOT/'tools/validate.py'),
  'genuine_coverage_gates':[byname[g] for g in positive],
  'altered_coverage_rejection_gates':[bynegative[g] for g in expected],
  'scope':'Coverage-only positive and mutated negative; complete release index remains separately pending.',
  'physical_operations':0,'provider_loaded':False}
out=HERE/'DEEPER_RETEST.json'
if out.exists():raise FileExistsError(out)
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
