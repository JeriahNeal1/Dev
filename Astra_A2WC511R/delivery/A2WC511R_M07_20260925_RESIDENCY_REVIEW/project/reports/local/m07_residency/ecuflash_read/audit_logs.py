"""Parse existing historical logs only; no application/device execution."""
import json
import re
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).parent
LOGS = Path(r'C:\Users\Jeriah Neal\AppData\Roaming\OpenECU\EcuFlash\logs')
reports = []
for path in sorted(LOGS.glob('*.txt')):
    raw = path.read_bytes()
    lines = raw.decode('utf-8', errors='replace').splitlines()
    reads, uploads, milestones = [], [], []
    for n, line in enumerate(lines, 1):
        read = re.search(r'kernel read area: addr: ([0-9A-Fa-f]+) len: ([0-9A-Fa-f]+)', line)
        upload = re.search(r'SSM2 write kernel ram block addr: ([0-9A-Fa-f]+) len: ([0-9A-Fa-f]+)', line)
        if read:
            reads.append(dict(line=n, address=int(read[1],16), size=int(read[2],16)))
        if upload:
            uploads.append(dict(line=n, address=int(upload[1],16), size=int(upload[2],16)))
        if re.search(r'writing kernel area|kernel version is|dumping ECU|checksum|crc32|kernel flash enable|kernel flash disable|kernel blank flash page|reset|interface close|Seed|Sending Key|comm buffer size set|flash buffer size set|EcuFlash Version|SSM2 ECU ID', line, re.I):
            milestones.append(dict(line=n,text=line))
    if not reads and not uploads:
        continue
    intervals = []
    for row in sorted(reads, key=lambda r:r['address']):
        a,b=row['address'],row['address']+row['size']
        if intervals and a<=intervals[-1][1]: intervals[-1][1]=max(b,intervals[-1][1])
        else: intervals.append([a,b])
    gaps=[]
    cursor=0
    for a,b in intervals:
        if a>cursor:gaps.append([cursor,a])
        cursor=max(cursor,b)
    if cursor<0x100000:gaps.append([cursor,0x100000])
    reports.append(dict(path=str(path),sha256=sha256(raw).hexdigest(),read_count=len(reads),
                        explicitly_logged_read_bytes=sum(b-a for a,b in intervals),
                        logged_read_intervals=[[f'{a:08X}',f'{b:08X}'] for a,b in intervals],
                        no_read_log_spans=[[f'{a:08X}',f'{b:08X}'] for a,b in gaps],
                        uploads=uploads, reads=reads, milestones=milestones,
                        flash_enable_logged=any('kernel flash enable' in s for s in lines),
                        flash_erase_logged=any('kernel blank flash page' in s for s in lines),
                        flash_commit_logged=any('kernel commit flash' in s for s in lines)))
out=dict(status='HISTORICAL_LOG_EVIDENCE_NOT_CURRENT_ROM_ATTESTATION',reports=reports,
         limits=['No raw response payloads or command bytes are present in these logs.',
                 'Absence of a logged flash/reset command does not prove it was not sent.',
                 'Unlogged ROM spans may be optimized based on other checks; exact method is unproved.'])
(HERE/'historical_log_audit.json').write_text(json.dumps(out,indent=2)+'\n')
for r in reports:
    print(json.dumps({k:v for k,v in r.items() if k not in ('uploads','reads','milestones')}))
