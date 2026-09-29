"""Use only the existing official MCP instance; fail closed, no mutation retries."""
from pathlib import Path
from hashlib import sha256
import json
from persistent_client import request
OUT = Path(__file__).parent
INSTANCE = '03e1b74a4e7b'
def call(name, arguments):
    result = request('tools/call', {'name':name,'arguments':arguments})
    print(name, json.dumps(result.get('result',{}))[:1500])
    return result
call('reference', {'query':'ida comments get_cmt set_cmt save database'})
call('execute_python', {'instance_id':INSTANCE, 'timeout':60,
    'code':(OUT/'annotate_m07.py').read_text()})
call('save_database', {'instance_id':INSTANCE})
call('close_database', {'instance_id':INSTANCE})
path = Path('C:/Dev/SubaruRoms/OEM/A2WC511R_STOCK_ROMRAIDER.bin.i64')
(OUT/'FINAL_IDB_IDENTITY.json').write_text(json.dumps({'path':str(path),
    'sha256':sha256(path.read_bytes()).hexdigest(), 'official_save_and_close':True,
    'metadata_only':True},indent=2)+'\n')
