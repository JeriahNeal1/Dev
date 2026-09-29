"""Retain the interrupted tool sources and old candidate seal without edits."""
import hashlib,json,shutil,stat
from pathlib import Path
R=Path(__file__).resolve().parents[1]
out=R/'evidence/rk02/input_snapshot';out.mkdir(parents=True,exist_ok=False)
files=[]
for folder in ('sim','host','fake','tools'):
    for p in sorted((R/folder).glob('*')):
        if p.is_file() and p.suffix in ('.py','.cpp','.json','.md'):
            q=out/p.relative_to(R);q.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(p,q);q.chmod(stat.S_IREAD)
            files.append({'path':str(p),'copy':str(q),'sha256':hashlib.sha256(q.read_bytes()).hexdigest()})
sealed=[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted((R/'evidence/rk01_superseded').rglob('*')) if p.is_file()]
(out/'MANIFEST.json').write_text(json.dumps({'files':files,'rk01_superseded_unchanged_seal':sealed},indent=2)+'\n')
print(json.dumps({'files':len(files),'rk01_files':len(sealed)}))
