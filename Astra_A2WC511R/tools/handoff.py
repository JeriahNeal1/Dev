"""CLI for offline project diagnostics. No vehicle interface."""
import argparse, json
from pathlib import Path
from project_core import rom_audit, binary_diff, csv_summary, gear_log_analysis, logger_validate, sha256

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['rom-audit','diff','csv-summary','gear-log','logger-validate','manifest'])
    p.add_argument('paths',nargs='+')
    p.add_argument('--output',type=Path)
    a=p.parse_args()
    if a.action=='diff':
        if len(a.paths)!=2: p.error('diff needs two files')
        result=binary_diff(*map(Path,a.paths))
    elif a.action=='manifest':
        root=Path(a.paths[0]).resolve()
        result=[{'path':str(f.relative_to(root)).replace('\\','/'),'size':f.stat().st_size,'sha256':sha256(f)} for f in sorted(root.rglob('*')) if f.is_file() and '.git' not in f.parts and '.runtime' not in f.parts and '__pycache__' not in f.parts]
    else:
        if len(a.paths)!=1:p.error('This action needs one file')
        result={'rom-audit':rom_audit,'csv-summary':csv_summary,'gear-log':gear_log_analysis,'logger-validate':logger_validate}[a.action](Path(a.paths[0]))
    text=json.dumps(result,indent=2,ensure_ascii=False)
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(text+'\n',encoding='utf-8')
        print('Wrote',a.output)
    else: print(text)

if __name__=='__main__':main()
