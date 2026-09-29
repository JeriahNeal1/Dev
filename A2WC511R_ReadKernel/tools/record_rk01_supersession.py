"""Record permanent supersession beside, never inside, preserved RK01 evidence."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def pin(p):return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
snapshot=json.loads((R/'evidence/rk02/input_snapshot/MANIFEST.json').read_text())
for item in snapshot['rk01_superseded_unchanged_seal']:
    assert pin(Path(item['path']))['sha256']==item['sha256']
report={'schema':1,'identity':'A2WC511R-RK01','status':'SUPERSEDED_NOT_FOR_HARDWARE',
 'permanent':True,'kernel_sha256':'3d70abfb8617b87e1b9c52724fd27ed4066ba231818994e780c8ba3006de273f',
 'reason':'RX remained enabled during TX. Explicit SCI2 self-echo receives one byte, then raises ORER and prevents the next request.',
 'old_positive_scope':'Old no-self-echo fixture equality is retained evidence, not communication qualification.',
 'no_requalification_of_RK01_permitted':True,
 'negative_control':pin(R/'evidence/sim/echo_audit_02/CURRENT_KERNEL_ECHO_FAILURE.json'),
 'manual_OEM_contract':pin(R/'evidence/contracts/SCI_SELF_ECHO_CONTRACT.json'),
 'preserved_source_snapshot':pin(R/'evidence/rk01_superseded/SOURCE_SNAPSHOT.json'),
 'preserved_directory_files':snapshot['rk01_superseded_unchanged_seal'],
 'physical_operations':False}
out=R/'evidence/RK01_SUPERSEDED.json'
with out.open('x') as f:f.write(json.dumps(report,indent=2)+'\n')
print(json.dumps(pin(out)))
