"""Read-only analysis helpers. Python 3.10+; standard library only.
No ECU I/O, flashing, ROM modification, XML expressions, or subprocess execution.
"""
from __future__ import annotations
import csv, hashlib, io, math, statistics
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET

ROM_SIZE = 0x100000
ECU_ID = '2F12515306'
HOOKS = {
    0x7A04: (0x209C, 'MAF interpolation pointer'),
    0x122B4: (0x14B20, 'WGDC routine pointer'),
    0x127E8: (0x317D8, 'rev-limit routine pointer'),
    0xD324: (0xF928, 'memory reset routine pointer'),
    0xFFF8: (0xFFFFBFFB, 'memory reset upper limit'),
    0x114E0: (0x35B96, 'base timing pointer; semantics still need audit'),
    0x1281C: (0x2E2E8, 'POLF pointer; semantics still need audit'),
    0x35C3C: (0x2150, 'timing interpolation pointer candidate'),
    0x35C40: (0x84944, 'base timing descriptor pointer candidate'),
    0x2E538: (0x2150, 'POLF interpolation pointer candidate'),
    0x2E544: (0x842E4, 'POLF descriptor pointer candidate'),
}
EXPECTED_CHANNELS = {
    'E_A2WC511R_TCU_STATUS_FLAGS': 0xFF4C50,
    'E_A2WC511R_TCU_DERIVED_DATA_VALID': 0xFF4CA1,
    'E_A2WC511R_PACKED_GEAR_RANGE_SOURCE': 0xFF4C75,
    'E_A2WC511R_PACKED_GEAR_RANGE': 0xFF4C8D,
}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()

def load_bytes(path: Path, max_size: int = 32*1024*1024) -> bytes:
    p = Path(path)
    if not p.is_file(): raise ValueError('Not a regular file: ' + str(p))
    if p.stat().st_size > max_size: raise ValueError('File exceeds analysis limit')
    return p.read_bytes()

def ff_runs(data: bytes, min_length: int = 256) -> list[dict]:
    import re
    return [{'start': hex(m.start()), 'end_exclusive': hex(m.end()), 'length': m.end()-m.start()}
            for m in re.finditer(b'\xff{' + str(min_length).encode() + b',}', data)]

def rom_audit(path: Path) -> dict:
    data = load_bytes(path)
    if len(data) != ROM_SIZE: raise ValueError(f'Expected {ROM_SIZE} bytes, got {len(data)}')
    hooks = []
    for a, (expected, role) in HOOKS.items():
        actual = int.from_bytes(data[a:a+4], 'big')
        hooks.append({'offset': hex(a), 'role': role, 'expected': hex(expected),
                      'actual': hex(actual), 'matches': actual == expected})
    calid = data[0x2000:0x2008].decode('ascii', errors='replace')
    return {'file': str(path), 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'calid_at_2000': calid, 'ecuid_at_CDAD8': data[0xCDAD8:0xCDADD].hex().upper(),
            'identity_matches': calid == 'A2WC511R' and data[0xCDAD8:0xCDADD].hex().upper() == ECU_ID,
            'reset_pc': hex(int.from_bytes(data[:4], 'big')),
            'reset_sp': hex(int.from_bytes(data[4:8], 'big')),
            'rom_tail': data[-8:].hex(' '), 'hook_old_values': hooks,
            'ff_runs': ff_runs(data),
            'warning': 'Identity and matching pointers do NOT establish stock provenance, compatibility, checksum validity, unused memory, or flash safety.'}

def binary_diff(a: Path, b: Path, max_ranges: int = 1000) -> dict:
    x, y = load_bytes(a), load_bytes(b)
    runs, count, start = [], 0, None
    for i in range(max(len(x), len(y))):
        different = i >= len(x) or i >= len(y) or x[i] != y[i]
        if different:
            count += 1
            if start is None: start = i
        elif start is not None:
            runs.append((start, i)); start = None
    if start is not None: runs.append((start, max(len(x), len(y))))
    return {'a': str(a), 'b': str(b), 'a_size': len(x), 'b_size': len(y),
            'a_sha256': hashlib.sha256(x).hexdigest(), 'b_sha256': hashlib.sha256(y).hexdigest(),
            'identical': x == y, 'changed_byte_positions': count, 'total_ranges': len(runs),
            'ranges': [{'start': hex(s), 'end_exclusive': hex(e), 'length': e-s,
                        'a_first16': x[s:min(e,s+16)].hex(' '), 'b_first16': y[s:min(e,s+16)].hex(' ')}
                       for s,e in runs[:max_ranges]], 'truncated': len(runs) > max_ranges,
            'warning': 'A diff is not a semantic, checksum, relocation, RAM-allocation, or flash-safety validation.'}

def read_csv(path: Path) -> tuple[list[str], list[dict[str,str]]]:
    data = load_bytes(path)
    try: text = data.decode('utf-8-sig')
    except UnicodeDecodeError: text = data.decode('cp1252')
    reader = csv.DictReader(io.StringIO(text))
    cols = reader.fieldnames or []
    if not cols: raise ValueError('No CSV header')
    if len(cols) != len(set(cols)): raise ValueError('Duplicate column names; resolve explicitly')
    rows = list(reader)
    if any(None in r for r in rows): raise ValueError('CSV contains rows wider than its header')
    return cols, rows

def number(value):
    try:
        n = float(value)
        return n if math.isfinite(n) else None
    except (ValueError, TypeError): return None

def csv_summary(path: Path) -> dict:
    cols, rows = read_csv(path)
    out = {'file': str(path), 'sha256': sha256(path), 'rows': len(rows), 'columns': cols,
           'header_only': not rows, 'numeric': {}}
    for col in cols:
        vals = [number(r.get(col)) for r in rows]
        valid = [v for v in vals if v is not None]
        if not valid: continue
        unique = Counter(valid)
        out['numeric'][col] = {'min': min(valid), 'max': max(valid), 'missing_or_invalid': len(vals)-len(valid),
                               'unique_count': len(unique)}
        if len(unique) <= 20: out['numeric'][col]['counts'] = {str(k):v for k,v in sorted(unique.items())}
    tc = next((c for c in cols if c.lower().startswith('time (msec)')), None)
    if tc and rows:
        t = [number(r.get(tc)) for r in rows]
        dt = [b-a for a,b in zip(t,t[1:]) if a is not None and b is not None]
        positive = [d for d in dt if d > 0]
        out['time'] = {'column': tc, 'first_ms': t[0], 'last_ms': t[-1],
                       'nonincreasing_steps': sum(d <= 0 for d in dt),
                       'median_interval_ms': statistics.median(positive) if positive else None,
                       'max_interval_ms': max(positive) if positive else None}
    return out

def gear_decode(nibble: int, previous: int | None = None) -> int | None:
    if not 0 <= nibble <= 15: raise ValueError('Not a nibble')
    return nibble if nibble < 8 else (0 if nibble == 8 else previous)

def gear_log_analysis(path: Path) -> dict:
    cols, rows = read_csv(path)
    def find(fragment): return next((c for c in cols if fragment.lower() in c.lower()), None)
    pcol = find('Packed Gear/Range Byte') or find('Packed Target/Current Gear Snapshot')
    acol = find('Raw Gear/Range A')
    bcol = find('Raw Gear Range Code')
    if not pcol: raise ValueError('No recognized packed-gear column; do not infer column semantics by order')
    comparisons = {k: {'compared':0,'mismatches':0} for k in ('upper_vs_BC1','lower_vs_BC2')}
    transitions, prev = [], None
    for i, r in enumerate(rows):
        val = number(r.get(pcol))
        if val is None or val != int(val) or not 0<=val<=255: continue
        packed = int(val)
        if packed != prev:
            transitions.append({'row_1based':i+2,'time_ms':number(r.get('Time (msec)')),
                                'packed_decimal':packed,'packed_hex':f'0x{packed:02X}',
                                'upper':packed>>4,'lower':packed&15})
            prev = packed
        for key,col,n in [('upper_vs_BC1',acol,packed>>4),('lower_vs_BC2',bcol,packed&15)]:
            actual = number(r.get(col)) if col else None
            expected = gear_decode(n)
            if actual is not None and expected is not None:
                comparisons[key]['compared'] += 1
                comparisons[key]['mismatches'] += actual != expected
    return {'file':str(path),'rows':len(rows),'comparisons':comparisons,'transitions':transitions,
            'warning':'Nibble names target/current are a working interpretation. Sequential polling, ECU scheduling and hydraulic shift completion are not equivalent. No communication-fault coverage is established.'}

def logger_validate(path: Path) -> dict:
    data = load_bytes(path)
    if b'<!ENTITY' in data.upper(): raise ValueError('Entity declarations not accepted by this validator')
    root = ET.fromstring(data)
    ssm = root.find("./protocols/protocol[@id='SSM']")
    if ssm is None: raise ValueError('No SSM protocol')
    custom = []
    for p in ssm.findall('./ecuparams/ecuparam'):
        if not p.get('id','').startswith('E_A2WC511R_'): continue
        ecus = p.findall('ecu')
        conversions = p.findall('./conversions/conversion')
        addresses = [a.text.strip() for e in ecus for a in e.findall('address')]
        custom.append({'id':p.get('id'), 'name':p.get('name'), 'addresses':addresses,
                       'exact_ecu':len(ecus)==1 and ecus[0].get('id')==ECU_ID,
                       'raw_uint8':len(conversions)==1 and conversions[0].get('storagetype')=='uint8' and conversions[0].get('expr')=='x' and conversions[0].get('format')=='0',
                       'target':p.get('target')})
    checks = {}
    for ident,addr in EXPECTED_CHANNELS.items():
        matches = [p for p in custom if p['id']==ident]
        checks[ident] = len(matches)==1 and matches[0]['exact_ecu'] and matches[0]['raw_uint8'] and matches[0]['target']=='1' and len(matches[0]['addresses'])==1 and int(matches[0]['addresses'][0],16)==addr
    id_counts = Counter(p['id'] for p in custom)
    return {'file':str(path),'sha256':sha256(path),'xml_well_formed':True,
            'version':root.get('version'),'custom_parameters':custom,'required_checks':checks,
            'duplicate_custom_ids':[k for k,v in id_counts.items() if v>1],
            'required_pass':all(checks.values()) and all(v==1 for v in id_counts.values()),
            'validation_scope':'XML well-formedness and exact project-channel checks, NOT RomRaider runtime or strict whole-document DTD validation. Existing stock DTD has repeated module IDs.'}

def resolve_inside(root: Path, relative: str) -> Path:
    root = Path(root).resolve()
    candidate = (root / relative).resolve()
    if not candidate.is_relative_to(root): raise ValueError('Path escapes project root')
    if any(p in {'.git','.runtime','.codex'} for p in candidate.relative_to(root).parts):
        raise ValueError('Secret/runtime/config directories are not readable through this tool')
    return candidate
