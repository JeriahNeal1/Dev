"""Retain narrow matcher-reporting source delta and regression provenance."""
from pathlib import Path
import subprocess,json,hashlib,sys
ROOT=Path('C:/Dev/Astra_A2WC511R');TOOL=Path('C:/Dev/Tools/diaphora-3.4.2-a2wc');OUT=ROOT/'reports/local/diaphora/setup/matcher_partition_repair'
OUT.mkdir(parents=True,exist_ok=False)
def git(*args):return subprocess.check_output(['git','-C',str(TOOL),*args])
previous=git('rev-parse','HEAD').decode().strip()
(OUT/'repair.diff').write_bytes(git('diff','--','diaphora.py','tester/test_a2wc_unmatched_sides.py'))
# The fail/pass transcript is the actual assertion seen in the preceding tool
# execution. No unperformed native or full matcher test is claimed here.
(OUT/'REGRESSION_RESULT.json').write_text(json.dumps({'before':'test_discarded_tentative_match_is_reported_unmatched FAILED: [] != [16]',
    'after':'2 unittest cases PASS: asymmetric labels/roles/save and discarded tentative match',
    'command':[sys.executable,'-B',str(TOOL/'tester/test_a2wc_unmatched_sides.py')],
    'scope':'No matcher scoring changes; unmatched is complement of retained chooser addresses',
    'affected_final_pairs':['511R/412D','511R/500R','511R/521C','511R/521R','511R/F200R'],
    'original_missing_source_counts':[8,3,2,2,3]},indent=2)+'\n',encoding='utf-8')
subprocess.run(['git','-C',str(TOOL),'add','--','diaphora.py','tester/test_a2wc_unmatched_sides.py'],check=True)
subprocess.run(['git','-C',str(TOOL),'commit','-m','Report unmatched from retained final matches, not stale tentative cache'],check=True)
current=git('rev-parse','HEAD').decode().strip()
(OUT/'COMPATIBILITY_PATCH_ALL.diff').write_bytes(git('diff','89d9981cf4ccd1f3087830a424e199ef8d6908e7',current,'--'))
manifest={'baseline':'89d9981cf4ccd1f3087830a424e199ef8d6908e7','previous_commit':previous,'commit':current,
          'diaphora_py_sha256':hashlib.sha256((TOOL/'diaphora.py').read_bytes()).hexdigest(),
          'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.iterdir())}}
(OUT/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
with (ROOT/'reports/local/diaphora/SETUP_REPAIR_LOG.md').open('a',encoding='utf-8') as f:
    f.write('\nContinuation row-partition audit found a second unmatched-reporting defect: final_pass removes tentative pairs but find_unmatched consulted stale matched-name caches. Five family comparisons silently omitted8/3/2/2/3 sourcefunctions. The narrow fix derives unmatched addresses from the four retained result choosers; it changes no scores or retained proposals. The new discarded-pair regression failedbefore ([] != [16]) and both reporting regressions passafter. Onlyaffectedcomparisons were regenerated; 412D cleanrepeat verifies deterministic result hashes. compare_exports.py now requires matched/unmatched rows to partition both complete sourceinventories. No export, installation or stockselftest was redone. Full diff/provenance: setup/matcher_partition_repair.\n')
print(json.dumps(manifest))
