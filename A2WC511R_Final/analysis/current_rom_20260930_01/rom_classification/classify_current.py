"""Exhaustive, read-only current image classification against pinned stock.

Uses retained native RomRaider objects and stock IDA/Diaphora inventories.
No editor, emulator, IDA process, provider or vehicle operation is invoked.
"""
import sys
sys.dont_write_bytecode = True
import csv
import hashlib
import importlib.util
import json
import sqlite3
import struct
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
BASE = Path('C:/Dev/Astra_A2WC511R')
CURRENT = OUT.parent/'current.preserved.bin'
SOURCE = Path('C:/Dev/SubaruRoms/current.bin')
STOCK = Path('C:/Dev/SubaruRoms/OEM/A2WC511R.bin')
CURRENT_SHA = 'bf10be6d7c75b4f2ae663b0d57a912e6e9ef7654ccfc985195954596e50427b2'
STOCK_SHA = '22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218'
SNAPSHOT = BASE/'reports/local/interfaces/native_snapshot.json'
EXTENTS = BASE/'reports/local/gate_closure/rom/definition_overlap.json'
IDA = BASE/'reports/local/gate_closure/ida/defined_code_export.json'
INDEX = BASE/'reports/local/diaphora/EXPORT_INDEX.json'
CHECKSUM = BASE/'reports/local/interfaces/checksum_audit.py'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pin(path):
    path = Path(path)
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': digest(data)}


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(name, data):
    (OUT/name).write_text(json.dumps(data, indent=2)+'\n')


def runs(positions):
    result = []
    for p in positions:
        if result and result[-1][1] == p:
            result[-1][1] += 1
        else:
            result.append([p, p+1])
    return result


def raw_value(data, address, width, storage_type, signed):
    b = data[address:address+width]
    return struct.unpack('>f', b)[0] if storage_type == 99 else int.from_bytes(b, 'big', signed=signed)


def main():
    current, stock = CURRENT.read_bytes(), STOCK.read_bytes()
    identity = {'current': pin(CURRENT), 'source': pin(SOURCE), 'stock': pin(STOCK),
                'expected_size': 1048576, 'current_size': len(current),
                'calid_at_2000': current[0x2000:0x2008].decode('ascii', errors='replace'),
                'ecuid_at_CDAD8': current[0xCDAD8:0xCDADD].hex().upper(),
                'reset_words': [f'{int.from_bytes(current[p:p+4], "big"):08X}' for p in range(0,16,4)]}
    valid = (len(current) == len(stock) == 0x100000 and digest(current) == CURRENT_SHA and
             digest(SOURCE.read_bytes()) == CURRENT_SHA and digest(stock) == STOCK_SHA and
             current[0x2000:0x2008] == b'A2WC511R' and current[0xCDAD8:0xCDADD] == bytes.fromhex('2f12515306'))
    identity['identity_and_size_valid'] = valid
    write_json('IDENTITY.json', identity)
    if not valid:
        raise SystemExit('STOP: identity/size/hash mismatch; classification not performed')

    ss, ext = read_json(SNAPSHOT), read_json(EXTENTS)
    assert digest(SNAPSHOT.read_bytes()) == ext['native_snapshot_sha256']
    assert ss['rom']['binary_sha256'] == STOCK_SHA and ss['rom']['calid'] == 'A2WC511R'
    definition = Path(ss['rom']['definition_path'])
    # loaded_document_sha256 hashes a Java-serialized DOM, not raw XML bytes.
    # Raw XML is independently pinned by the retained inheritance report.
    assert digest(definition.read_bytes()) == read_json(BASE/'reports/definition_inheritance.json')['sha256']
    objects = []
    for t in ss['tables']:
        width = {0:0, 1:1, 2:2, 4:4, 99:4}[t['storage_type']]
        if not width or t.get('static'):
            continue
        count = max([int(c['storage_index'])+1 for row in t.get('cells', []) for c in row]+[t['rows']*t['columns']])
        count = max([int(p.get('offset',0))+len(p.get('data',[])) for p in t.get('presets',[])]+[count])
        start = t['storage_address']
        category = 'checksum' if t['name'] == 'Checksum Fix' else 'axis' if t['key'].endswith(('::x','::y','::axis')) else 'scalar' if count == 1 else 'table'
        objects.append({'key': t['key'], 'name': t['name'], 'category': category,
                        'start': start, 'end': start+width*count, 'width': width, 'count': count,
                        'storage_type': t['storage_type'], 'signed': t['signed'], 'endian': t['endian'],
                        'native_type': t['type'], 'scale': t.get('scale'), 'source': 'native_snapshot.json'})
    declared = [{'name': t['name'], 'start': t['start'], 'end': t['end'], 'width': t['width'], 'count': t['count']} for t in objects]
    assert declared == ext['table_extents']
    changed = [p for p, (a,b) in enumerate(zip(stock,current)) if a != b]
    byte_rows = []
    for p in changed:
        owners = [t for t in objects if t['start'] <= p < t['end']]
        if 0xFFC4C <= p < 0xFFC50:
            category, keys = 'metadata', ['RomRaider edit stamp']
        elif owners:
            categories = {t['category'] for t in owners}
            assert len(categories) == 1, (hex(p), owners)
            category, keys = categories.pop(), [t['key'] for t in owners]
        else:
            category, keys = 'unknown', []
        byte_rows.append({'address': p, 'address_hex': f'0x{p:05X}', 'stock': stock[p], 'current': current[p],
                          'classification': category, 'object_keys': keys})
    assert len({r['address'] for r in byte_rows}) == len(changed)
    changed_set = set(changed)
    categories = Counter(row['classification'] for row in byte_rows)
    for name in ('table','axis','scalar','checksum','metadata','code','padding','unknown'):
        categories.setdefault(name, 0)
    annotate = {row['address']: row for row in byte_rows}
    range_rows = []
    for start,end in runs(changed):
        segments = []
        for p in range(start,end):
            key = (annotate[p]['classification'], tuple(annotate[p]['object_keys']))
            if segments and segments[-1]['end_exclusive'] == p and (segments[-1]['classification'],tuple(segments[-1]['object_keys'])) == key:
                segments[-1]['end_exclusive'] += 1
            else:
                segments.append({'start': p, 'end_exclusive': p+1, 'classification': key[0], 'object_keys': list(key[1])})
        range_rows.append({'start': start, 'end_exclusive': end, 'start_hex': f'0x{start:05X}',
                           'end_exclusive_hex': f'0x{end:05X}', 'length': end-start,
                           'stock_hex': stock[start:end].hex(), 'current_hex': current[start:end].hex(), 'segments': segments})
    write_json('CHANGED_RANGES.json', {'changed_byte_count': len(changed), 'range_count': len(range_rows), 'ranges': range_rows})
    with (OUT/'CHANGED_BYTES.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['address','address_hex','stock','current','classification','object_keys'])
        writer.writeheader()
        writer.writerows(dict(row,object_keys=' | '.join(row['object_keys'])) for row in byte_rows)

    touched = []
    for obj in objects:
        positions = sorted(changed_set.intersection(range(obj['start'],obj['end'])))
        if not positions:
            continue
        cell_indices = sorted({(p-obj['start'])//obj['width'] for p in positions})
        cells = []
        for index in cell_indices:
            p = obj['start']+index*obj['width']
            cells.append({'storage_index': index, 'address': p,
                          'stock_hex': stock[p:p+obj['width']].hex(), 'current_hex': current[p:p+obj['width']].hex(),
                          'stock_raw': raw_value(stock,p,obj['width'],obj['storage_type'],obj['signed']),
                          'current_raw': raw_value(current,p,obj['width'],obj['storage_type'],obj['signed'])})
        touched.append(dict(obj, changed_bytes=len(positions), changed_cells=len(cells), cells=cells,
                            stock_object_sha256=digest(stock[obj['start']:obj['end']]),
                            current_object_sha256=digest(current[obj['start']:obj['end']])))
    write_json('CHANGED_OBJECTS.json', {'native_extent_count': len(objects), 'changed_object_count': len(touched), 'objects': touched})

    spec = importlib.util.spec_from_file_location('current_readonly_checksum', CHECKSUM)
    checksum = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checksum)
    stock_checks, current_checks = checksum.records(stock), checksum.records(current)
    checks = {'current_records': current_checks, 'stock_records': stock_checks,
              'geometry_equal': [(r['start'],r['end_parameter']) for r in current_checks] == [(r['start'],r['end_parameter']) for r in stock_checks],
              'all_14_records_valid': all(r['valid'] for r in current_checks),
              'first_record_enabled': not current_checks[0]['disabled'],
              'enabled_count': sum(not r['disabled'] for r in current_checks),
              'metadata': {'edit_stamp_address': '0xFFC4C', 'stock_hex': stock[0xFFC4C:0xFFC50].hex(), 'current_hex': current[0xFFC4C:0xFFC50].hex(),
                           'interpretation': 'Native RomRaider edit stamp, separate from checksum correction; not read-session freshness evidence.'}}
    write_json('CHECKSUMS.json', checks)

    ida = read_json(IDA)
    assert all(int.from_bytes(stock[r['ea']:r['ea']+2], 'big') == r['word'] for r in ida['code'])
    index = read_json(INDEX)['exports']['A2WC511R_stock_03']
    for kind in ('rom','export','analysis'):
        assert pin(index[kind]['path'])['sha256'] == index[kind]['sha256']
    analysis = read_json(index['analysis']['path'])
    assert analysis['rom_sha256'] == STOCK_SHA
    conn = sqlite3.connect(Path(index['export']['path']).as_uri()+'?mode=ro&immutable=1', uri=True)
    insns = conn.execute('SELECT address, mnemonic, disasm, func_id FROM instructions').fetchall()
    instruction_addresses = sorted({int(row[0]) for row in insns})
    assert all(0 <= p < 0xFFFFF and p%2 == 0 for p in instruction_addresses)
    changed_instruction_addresses = [p for p in instruction_addresses if stock[p:p+2] != current[p:p+2]]
    changed_functions, contained_data = [], []
    for f in analysis['functions']:
        assert [digest(stock[a:b]) for a,b in f['chunks']] == f['chunk_sha256'], f['name']
        hits = sorted({p for a,b in f['chunks'] for p in changed_set if a<=p<b})
        if not hits:
            continue
        code_hits = sorted({p for p in changed_instruction_addresses if any(a<=p<b for a,b in f['chunks'])})
        entry = {'start': f['start'], 'end': f['end'], 'name': f['name'], 'chunks': f['chunks'],
                 'changed_byte_positions': hits, 'changed_instruction_addresses': code_hits,
                 'stock_chunk_sha256': f['chunk_sha256'], 'current_chunk_sha256': [digest(current[a:b]) for a,b in f['chunks']],
                 'classifications': [annotate[p] for p in hits]}
        (changed_functions if code_hits else contained_data).append(entry)
    assert stock[0x15474:0x15476] == bytes.fromhex('c761')
    assert (0x15474 & ~3)+4+4*stock[0x15475] == 0x155FC
    assert stock[0x15478:0x1547A] == bytes.fromhex('f608')
    assert current[0x15474:0x1547A] == stock[0x15474:0x1547A]
    scalar_proof = {'scalar_address': '0x155FC', 'changed_byte': '0x155FD', 'object': 'Max Wastegate Duty Limit Post-Compensation',
                    'stock_be_float32': struct.unpack('>f',stock[0x155FC:0x15600])[0],
                    'current_be_float32': struct.unpack('>f',current[0x155FC:0x15600])[0],
                    'MOVA': {'address':'0x15474','bytes':'c761','decoded_target':'0x155FC'},
                    'load': {'address':'0x15478','bytes':'f608','meaning':'FMOV.S @R0,FR6'},
                    'instructions_unchanged': True, 'interpretation': 'Embedded calibration literal inside function extent; changed data affects behavior without changing executable opcodes.'}
    # Whole-image complement closes the gap left by partial static discovery.
    # Every changed position is independently owned by an exact native object or metadata.
    non_data_changed = [r for r in byte_rows if r['classification'] in ('unknown','code','padding')]
    executable_identical = not changed_instruction_addresses and not non_data_changed
    code_report = {'executable_code_identical': executable_identical,
                   'scope': 'All changed bytes classified as exact RomRaider data/checksum/edit stamp, plus byte comparison of retained stock instruction inventories.',
                   'older_IDA_export': {'defined_instruction_count':len(ida['code']), 'stock_word_validation':True,
                                        'changed_instruction_count':sum(stock[r['ea']:r['ea']+r['size']]!=current[r['ea']:r['ea']+r['size']] for r in ida['code'])},
                   'Diaphora_stock_inventory': {'function_count':len(analysis['functions']), 'instruction_rows':len(insns),
                                               'unique_instruction_words':len(instruction_addresses), 'instruction_bytes':len(instruction_addresses)*2,
                                               'changed_instruction_addresses':changed_instruction_addresses,
                                               'coverage_claim':analysis['coverage_claim']},
                   'changed_executable_functions':changed_functions,
                   'function_contained_data_changes':contained_data,
                   'embedded_scalar_proof':scalar_proof,
                   'all_bytes_outside_exact_known_data_changes_identical':not non_data_changed,
                   'fresh_Diaphora_matching_performed':False,
                   'Diaphora_decision':'No changed instruction bytes or unknown changed regions; exact aligned comparison plus retained instruction/function inventories is conclusive for this image. Fresh structural matching would add no evidence.',
                   'limits':['Static instruction inventories are partial, not a complete firmware reachability proof.',
                             'Data classification uses exact native loaded definition objects, not near-table addresses.',
                             'Unchanged instruction bytes do not imply unchanged behavior: calibration data changed.',
                             'One ECUFlash file is not independently proven lossless acquisition; compare with physical/provenance assessment separately.']}
    write_json('EXECUTABLE_COMPARISON.json',code_report)

    registry = read_json(BASE/'tools/prehardware/validator_registry.json')
    hooks = []
    for address, expected in registry['common']['preserved_hook_words'].items():
        address = int(address)
        hooks.append({'address':address,'expected_stock_word':expected,
                      'stock_word':int.from_bytes(stock[address:address+4],'big'),
                      'current_word':int.from_bytes(current[address:address+4],'big'),
                      'unchanged':current[address:address+4]==stock[address:address+4]})
    write_json('PRESERVED_HOOKS.json',{'hooks':hooks,'all_unchanged':all(h['unchanged'] for h in hooks),
                                     'reviewed_rom_spans':[{'start':a,'end_exclusive':b,'unchanged':stock[a:b]==current[a:b]} for a,b in [[0,0x2000],[0x11AD8,0x11AE0],[0x4F310,0x4F950],[0xE1000,0xE1364],[0xFFC50,0x100000]]]})
    summary = {'status':'PASS_COMPLETE_BYTE_CLASSIFICATION', 'designation':'CURRENT_PHYSICAL_CAPTURE',
               'factory_stock':False,'current_sha256':CURRENT_SHA,'stock_sha256':STOCK_SHA,
               'changed_bytes':len(changed),'changed_ranges':len(range_rows),'changed_native_objects':len(touched),
               'classification_byte_counts':dict(categories),'unclassified_changed_bytes':len(non_data_changed),
               'executable_code_identical':executable_identical,'changed_executable_functions':[],
               'function_contained_data_change_count':len(contained_data),'checksum_status':checks,
               'physical_activity':False,'input_files_modified':False,
               'file_designation_limit':'Analyzes the user-associated ECUFlash capture as supplied; does not upgrade its acquisition exactness to independently verified two-pass raw read.',
               'evidence':[pin(p) for p in [SOURCE,CURRENT,STOCK,SNAPSHOT,EXTENTS,IDA,INDEX,definition,CHECKSUM,
                                          Path(index['export']['path']),Path(index['analysis']['path']),
                                          BASE/'reports/definition_inheritance.json',
                                          BASE/'integrations/romraider/src/rombridge/RomAccess.java',
                                          BASE/'tools/prehardware/validator_registry.json',Path(__file__)]]}
    assert not non_data_changed and executable_identical
    assert checks['geometry_equal'] and checks['all_14_records_valid'] and checks['first_record_enabled']
    assert digest(CURRENT.read_bytes())==CURRENT_SHA and digest(SOURCE.read_bytes())==CURRENT_SHA and digest(STOCK.read_bytes())==STOCK_SHA
    write_json('CLASSIFICATION_SUMMARY.json', summary)
    print(json.dumps({k:summary[k] for k in ['status','changed_bytes','changed_ranges','changed_native_objects','classification_byte_counts','executable_code_identical','function_contained_data_change_count']}))


if __name__ == '__main__':
    main()
