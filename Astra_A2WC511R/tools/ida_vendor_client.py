"""Local transport client for the installed official Hex-Rays MCP (not a server)."""
import argparse, datetime, json, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def request(method, params=None):
    payload = {'jsonrpc': '2.0', 'id': 1, 'method': method}
    if params is not None:
        payload['params'] = params
    req = urllib.request.Request('http://127.0.0.1:8737/mcp',
        data=json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'})
    out = ROOT / 'reports/local/ida'
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    record = out / (stamp + '.json')
    try:
        with urllib.request.urlopen(req, timeout=380) as response:
            raw = response.read().decode()
    except Exception as error:
        record.write_text(json.dumps({'request': payload, 'transport_error': repr(error)}, indent=2), encoding='utf-8')
        raise
    if raw.startswith('event:') or raw.startswith('data:'):
        raw = '\n'.join(line[5:].strip() for line in raw.splitlines() if line.startswith('data:'))
    result = json.loads(raw)
    record.write_text(json.dumps({'request': payload, 'response': result}, indent=2), encoding='utf-8')
    if 'error' in result or result.get('result', {}).get('isError'):
        raise RuntimeError('Official IDA MCP returned an error; see ' + str(record))
    return result

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('method')
    p.add_argument('--params', type=Path)
    p.add_argument('--script', type=Path)
    a = p.parse_args()
    params = json.loads(a.params.read_text(encoding='utf-8')) if a.params else None
    if a.script:
        params = {'name': 'execute_python', 'arguments': {'code': a.script.read_text(encoding='utf-8')}}
    print(json.dumps(request(a.method, params), indent=2))
