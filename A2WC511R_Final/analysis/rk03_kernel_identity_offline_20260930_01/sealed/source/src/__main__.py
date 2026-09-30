"""Offline model entry point: no arguments, no paths, no physical backend."""
import json
import sys
from identity_model import run

if len(sys.argv)!=1:
    print('This static offline model accepts no arguments.',file=sys.stderr)
    raise SystemExit(2)
result=run()
print(json.dumps(result,sort_keys=True,separators=(',',':')))
raise SystemExit(0 if result['status']=='PASS_OFFLINE_KERNEL_START_IDENTITY_ONLY' else 1)
