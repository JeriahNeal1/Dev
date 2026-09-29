from pathlib import Path
from hashlib import sha256
import json,sqlite3
ROOT=Path('C:/Dev/Astra_A2WC511R');a=ROOT/'reports/local/diaphora/correspondence_final_01';b=ROOT/'work/diaphora/reports/correspondence_determinism_01'
manifest={}
for path in sorted(a.iterdir()):
    if path.name=='DETERMINISM.json':continue
    counterpart=b/path.name;assert counterpart.is_file()
    digest=sha256(path.read_bytes()).hexdigest();assert digest==sha256(counterpart.read_bytes()).hexdigest(),path.name
    manifest[path.name]={'sha256':digest,'size':path.stat().st_size}
with sqlite3.connect(a/'FUNCTION_CORRESPONDENCE.sqlite') as db:
    assert db.execute('pragma integrity_check').fetchone()[0]=='ok'
    rows=db.execute('select count(*) from correspondence').fetchone()[0]
    counts=dict(db.execute('select confidence,count(*) from correspondence group by confidence'))
    assert rows==sum(1 for _ in (a/'FUNCTION_CORRESPONDENCE.jsonl').open(encoding='utf-8'))
result={'status':'PASS','exact_byte_determinism_across_clean_generator_processes':True,'function_rows':rows,'confidence_counts':counts,
        'first':str(a),'second':str(b),'files':manifest,'no_export_or_matcher_rerun_for_this_check':True}
(a/'DETERMINISM.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
