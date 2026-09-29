from pathlib import Path
import json,datetime
root=Path('C:/Dev/Astra_A2WC511R');state=root/'state';now=datetime.datetime.now(datetime.timezone.utc).isoformat()
checkpoint=state/'CHECKPOINT.json';d=json.loads(checkpoint.read_text())
d.update({'phase':'DIAPHORA_COMPARATIVE_ANALYSIS_IN_PROGRESS','updated_utc':now,'current_evidence':'reports/local/diaphora',
          'current_task':'Durable Diaphora3.4.2/nativeIDA9.4 comparative evidence for M07/M08 ownership',
          'authoritative_idb_reopen_status':'FAIL_MISSING_21_ROOT_NODE_RECORDS_ORIGINAL_PRESERVED',
          'diaphora_path':'C:/Dev/Tools/diaphora-3.4.2-a2wc','diaphora_python':'Native IDAPython9.4.0 / CPython3.14.7 AMD64',
          'ownership_remains_fail':True,'new_physical_actions':False})
checkpoint.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
with (state/'SESSION_LOG.md').open('a',encoding='utf-8') as f:f.write(f'\n{now} Diaphora milestone: native ABI probe, preserved upstream writable worktree/vendor, strict structural export and matcher repair complete. Fresh stock/M07/sibling native exports under work/diaphora. Comparisons and correspondence in progress. Current IDB Root Node defect isolated on copies; no authority replacement. Ownership remainsFAIL.\n')
path=state/'CURRENT_STATE.md';old=path.read_text(encoding='utf-8')
header='# Active Diaphora comparative run\n\nNative IDA9.4 / IDAPython9.4.0 / CPython3.14.7 has been probed. The writable\nDiaphora3.4.2 tree is C:/Dev/Tools/diaphora-3.4.2-a2wc. Fresh ROM exports and\ncomparisons are in work/diaphora; evidence and repair journals in reports/local/diaphora.\nNo M0/M06/M07 frozen artifact, original Diaphora source, physical provider or ECU changed.\nThe latest authoritative IDB has a separately proven missing Root Node defect;\nforensic recovery is on a copy only. Continue exports/comparisons/correspondence\nand actual ownership analysis; installation alone is not task completion.\n\n'
if not old.startswith('# Active Diaphora'):path.write_text(header+old,encoding='utf-8')
print(now)
