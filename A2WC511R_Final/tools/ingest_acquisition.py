"""Offline RK02 ingestion. No transport, image repair, IDA or boot execution.

Copies are evidence only. Human vehicle/session association remains a separate
review even when an operator association document is supplied.
"""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import types
import zipfile
import zlib

FINAL = Path('C:/Dev/A2WC511R_Final')
RK = Path('C:/Dev/A2WC511R_ReadKernel')
OLD = Path('C:/Dev/Astra_A2WC511R')
SIZE = 0x100000
STOCK_SHA = '22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218'
KERNEL_SHA = '3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581'
HOST_SHA = '58d0867b85162e6fa4ccd3ac7fe0413c40e4054cbc416d12e39e29f926e60862'
PINS = {
    RK/'host/__init__.py': '19891087e3d3f09eadbd6535914e59bb738c97671ab135811f5a4185c91ea050',
    RK/'host/finalize.py': 'b55d0c85e6f3e6026a12c1360a77ad8bac892ed16891e69ddef4b18cfc1666ef',
    RK/'host/protocol.py': 'd7909dc2026fae0545d94d048c2c71ab366e804df84c5ee563d656d3774dbf38',
    RK/'host/state.py': 'f25e179632e2635236450c7d74aa067db3ac77d398cc88401879d56b058b3d06',
    RK/'host/stream.py': 'f5eea7776b7e641378df94187ca59440cf3ab26853b747bd164810d56d5a6887',
    RK/'host/physical_build/rk02_physical_01/BUILD_MANIFEST.json': 'fb761f3e5e3951b81a402b8f82b159ff1c691762cf3f8abcc20bd3aa44708d70',
    OLD/'reports/local/interfaces/checksum_audit.py': '00b868761261d819572a8e5a51655e7a526849d8d9ba4828dbd904d0bb9dc6bc',
    OLD/'tools/prehardware/validator_registry.json': 'e715887f064e605371f3d413beba55876a62fe0290c4da6aefee9e85e0a7a861',
    OLD/'work/diaphora/exports/A2WC511R_stock_02.analysis.json': '7c08c4b444c5742ace6b29302d57178ecc3cc505e0de17162ae14325b24bda3c',
    OLD/'reports/local/gate_closure/ida/defined_code_export.json': 'db77bfa6d563df046d58fd666b6ccf90ddcbb53c171c2f96d2076eee0a3f7578',
    OLD/'reports/local/gate_closure/calibration/inventory.json': '0d81f057d303cd611748f3009eca2c02c3776ea2454414db1dbcb1aab8b63534',
    OLD/'reports/local/gate_closure/calibration/history_comparison.json': '15bfc195a1b74c33e62a2304bb7e4b00b7158a45cc51118791d747bfb1910cd0',
    OLD/'reports/local/prehardware/acquisition/LOCAL_IMAGE_ATTESTATION_CATALOG.json': 'd936007e5c7f29867b91d0210de3f8d10c7084d8bbeb4b1d935ce522a385d986',
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


class Inputs:
    """Retain the exact validated buffers and detect change before publication."""
    def __init__(self):
        self.buffers = {}

    def read(self, path, expected=None):
        path = Path(path).resolve()
        if path not in self.buffers:
            self.buffers[path] = path.read_bytes()
        raw = self.buffers[path]
        require(expected is None or sha(raw) == expected, 'Input hash mismatch: '+str(path))
        return raw

    def json(self, path):
        return json.loads(self.read(path))

    def recheck(self):
        for path, raw in self.buffers.items():
            require(path.read_bytes() == raw, 'Input changed during ingestion: '+str(path))

    def manifest(self):
        return [{'path': str(p), 'sha256': sha(b), 'bytes': len(b)} for p, b in self.buffers.items()]


def load_apis(inputs):
    for path, expected in PINS.items():
        inputs.read(path, expected)
    names = ('host', 'host.protocol', 'host.state', 'host.stream', 'host.finalize')
    previous = {name: sys.modules.get(name) for name in names}
    original_path = list(sys.path)
    try:
        # Execute the pinned source buffers, never cached .pyc or prior modules.
        for name in names:
            path = RK/'host'/('__init__.py' if name == 'host' else name.split('.')[-1]+'.py')
            module = types.ModuleType(name)
            module.__file__ = str(path)
            module.__package__ = 'host'
            if name == 'host':
                module.__path__ = [str(RK/'host')]
            sys.modules[name] = module
            exec(compile(inputs.read(path), str(path), 'exec'), module.__dict__)
        api = sys.modules['host.finalize']
    finally:
        for name, module in previous.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
        sys.path[:] = original_path
    path = OLD/'reports/local/interfaces/checksum_audit.py'
    checksum = types.ModuleType('ingest_checksum_audit')
    checksum.__file__ = str(path)
    exec(compile(inputs.read(path), str(path), 'exec'), checksum.__dict__)
    return api, checksum


def check_record(inputs, record, expected_path):
    require(Path(record['path']).resolve() == expected_path.resolve(), 'Capture record path mismatch')
    raw = inputs.read(expected_path, record['sha256'])
    require(len(raw) == record['bytes'], 'Capture record size mismatch')
    return raw


def validate_pair(first, second):
    require(len(first) == len(second) == SIZE, 'Two exact 1MiB reads required')
    require(first == second and sha(first) == sha(second), 'Two raw passes differ')


def validate_capture(capture, inputs, api):
    capture = Path(capture).resolve()
    report_path = capture/'finalized/FINALIZATION.json'
    report = inputs.json(report_path)
    require(report.get('schema') == 1 and report.get('status') == 'PASS_RAW_CAPTURE_INTEGRITY', 'Successful finalization required')
    require(report.get('classification') == 'USER_PHYSICAL_CAPTURE_REQUIRES_SESSION_ASSOCIATION'
            and report.get('capture_declared_physical') is True, 'Physical capture required; virtual fixtures rejected')
    require(report.get('current_ROM_identified') is False and report.get('physical_session_association_proven') is False,
            'Finalizer must not assert vehicle association')
    require(report.get('kernel_sha256') == KERNEL_SHA and report.get('client_sha256') == HOST_SHA, 'Wrong RK02 kernel/host identity')
    require(report.get('provider_loaded_by_finalizer') is False and report.get('physical_transport_used_by_finalizer') is False,
            'Unexpected finalizer transport claim')
    require(report.get('provenance_hashes_derived_from_exact_validated_buffers') is True
            and report.get('inputs_rechecked_before_publication') is True, 'Finalizer integrity contract missing')
    check_record(inputs, report['source'], RK/'host/finalize.py')
    release, binding, binary, executable_name, kernel = api.load_release('rk02_physical_01', True)
    require(binary['sha256'] == HOST_SHA and binding['kernel_sha256'] == KERNEL_SHA, 'Fixed release identity')
    # Cache every load_release dependency too, so its results cannot outlive input changes.
    for record in (release['certificate'], binary,
                   {'path': binding['kernel_path'], 'sha256': KERNEL_SHA},
                   {'path': binding['manifest_path'], 'sha256': binding['manifest_sha256']}):
        inputs.read(record['path'], record['sha256'])
    inputs.read(capture/executable_name, HOST_SHA)
    journal = check_record(inputs, report['native_journal'], capture/'native_api.jsonl')
    banner = check_record(inputs, report['native_banner'], capture/'native.log')
    require('PASS_NATIVE_FIXED_PHYSICAL_TWO_FULL_READS' in banner.decode(), 'Physical success banner missing')
    events = [json.loads(line) for line in journal.decode().splitlines()]
    replay, proof = api.replay_native(events, kernel, KERNEL_SHA, True)
    require(report['proof'] == proof, 'Finalization replay proof differs')
    require(len(report['raw_copies']) == len(report['input_raw_files']) == 2, 'Exactly two raw record pairs')
    raws = []
    for index in (0, 1):
        raw = check_record(inputs, report['raw_copies'][index], capture/f'finalized/raw_pass{index}.bin')
        original = check_record(inputs, report['input_raw_files'][index], capture/f'pass{index}.partial.bin')
        require(raw == original == replay.images[index], 'Raw not identical to original and journal replay')
        raws.append(raw)
    validate_pair(*raws)
    require(report['CAL_ID_literal_offsets'] == [i for i in range(SIZE) if raws[0].startswith(b'A2WC511R', i)],
            'CAL literal offset evidence mismatch')
    return raws, report_path, proof


def image_checks(raw, common, checksum):
    checks = []
    def add(name, ok, detail):
        checks.append({'id': name, 'status': 'PASS' if ok else 'FAIL', 'detail': detail})
    add('LENGTH', len(raw) == SIZE, len(raw))
    if len(raw) != SIZE:
        return checks
    for key in ('calid', 'ecuid'):
        offset = common['identity'][key+'_offset']
        expected = bytes.fromhex(common['identity'][key+'_hex'])
        actual = raw[offset:offset+len(expected)]
        add(key.upper(), actual == expected, {'offset': offset, 'actual_hex': actual.hex()})
    words = list(struct.unpack_from('>4I', raw))
    add('RESET_BIG_ENDIAN', words == common['reset_words'] and words[0] % 2 == words[2] % 2 == 0, words)
    add('INITIAL_SP', words[1] == words[3] == 0xFFFFBFA0, [words[1], words[3]])
    try:
        rows = checksum.records(raw)
        actual = [(r['descriptor_offset'], r['start'], r['end_parameter']) for r in rows]
        expected = [(r['offset'], r['start'], r['end_parameter']) for r in common['checksum_descriptors']]
        add('CHECKSUM_GEOMETRY_ENABLED', actual == expected and not rows[0]['disabled'], actual)
        add('CHECKSUM_VALIDITY', all(r['valid'] for r in rows), rows)
    except (ValueError, struct.error) as error:
        add('CHECKSUM_GEOMETRY_ENABLED', False, str(error))
        add('CHECKSUM_VALIDITY', False, 'Not calculated')
    return checks


CATEGORIES = ('calibration', 'checksum', 'stamp', 'executable', 'function_chunk_candidate', 'control_or_vector', 'referenced_data_candidate')


def category_map(common, code, analysis):
    masks = [0]*SIZE
    def mark(start, end, category):
        if 0 <= start < end <= SIZE:
            bit = 1 << CATEGORIES.index(category)
            for pos in range(start, end):
                masks[pos] |= bit
    for extent in common['calibration_extents']:
        mark(extent['start'], extent['end'], 'calibration')
    for row in common['checksum_descriptors']:
        mark(row['offset']+8, row['offset']+12, 'checksum')
    mark(0xFFC4C, 0xFFC50, 'stamp')
    mark(0, 16, 'control_or_vector')
    mark(0xFFC50, SIZE, 'control_or_vector')
    mark(0x484B0, 0x484BC, 'control_or_vector')
    for address in common['preserved_hook_words']:
        mark(int(address), int(address)+4, 'control_or_vector')
    for item in code['code']:
        mark(item['ea'], item['ea']+item['size'], 'executable')
    for function in analysis['functions']:
        for start, end in function['chunks']:
            mark(start, end, 'function_chunk_candidate')
        for reference in function['references']:
            if reference['iscode'] is False:
                # Width is unknown: four bytes are a triage hint, never a typed-data claim.
                mark(reference['to'], reference['to']+4, 'referenced_data_candidate')
    return masks


def difference(before, after, masks):
    require(len(before) == len(after) == len(masks) == SIZE, 'Diff size mismatch')
    ranges = []
    counts = {name: 0 for name in (*CATEGORIES, 'unknown')}
    changed = uncertain = 0
    for index, (a, b) in enumerate(zip(before, after)):
        if a == b:
            continue
        mask = masks[index]
        names = [name for n, name in enumerate(CATEGORIES) if mask & (1 << n)] or ['unknown']
        ambiguous = len(names) > 1 or any(name in names for name in ('unknown', 'function_chunk_candidate', 'referenced_data_candidate'))
        changed += 1
        uncertain += ambiguous
        for name in names:
            counts[name] += 1
        if ranges and ranges[-1]['end_exclusive'] == index and ranges[-1]['categories'] == names:
            ranges[-1]['end_exclusive'] += 1
        else:
            ranges.append({'start': index, 'end_exclusive': index+1, 'categories': names, 'overlap_or_uncertain': ambiguous})
    for item in ranges:
        start, end = item['start'], item['end_exclusive']
        item.update(before_hex=before[start:end].hex(), after_hex=after[start:end].hex())
    trigger = any(counts[name] for name in ('executable', 'function_chunk_candidate', 'control_or_vector', 'referenced_data_candidate', 'unknown'))
    return {'changed_bytes': changed, 'category_counts_overlapping': counts, 'uncertain_changed_bytes': uncertain,
            'diaphora_review_trigger': trigger, 'ranges': ranges}


def historical_bytes(label, expected, inputs):
    if '::' not in label:
        raw = inputs.read(label, expected)
    else:
        path, member = label.split('::', 1)
        container = inputs.read(path)
        if member.startswith('payload@'):
            start = int(member.split('@')[1], 16)
            raw = container[start:start+SIZE]
        else:
            import io
            with zipfile.ZipFile(io.BytesIO(container)) as archive:
                require(archive.getinfo(member).file_size == SIZE, 'Historical ZIP size')
                raw = archive.read(member)
    require(len(raw) == SIZE and sha(raw) == expected, 'Historical image identity mismatch')
    return raw


def compare_catalogs(raw, inputs, common):
    inventory = inputs.json(OLD/'reports/local/gate_closure/calibration/inventory.json')
    history = inputs.json(OLD/'reports/local/gate_closure/calibration/history_comparison.json')
    catalog = inputs.json(OLD/'reports/local/prehardware/acquisition/LOCAL_IMAGE_ATTESTATION_CATALOG.json')
    analysis = inputs.json(OLD/'work/diaphora/exports/A2WC511R_stock_02.analysis.json')
    code = inputs.json(OLD/'reports/local/gate_closure/ida/defined_code_export.json')
    stock = inputs.read(common['baseline']['path'], STOCK_SHA)
    require(analysis['rom_sha256'] == STOCK_SHA, 'Function map targets wrong stock')
    require(code['rom_sha256'] in (STOCK_SHA, 'a34c4ce8238bf28bdc18c191bbe73b2179130aa9846e952a6fa332bae442de96'),
            'Instruction map targets wrong stock/stamp-only reference')
    require(all(item['size'] == 2 and int.from_bytes(stock[item['ea']:item['ea']+2], 'big') == item['word']
                for item in code['code']), 'Defined instruction map differs from immutable stock')
    masks = category_map(common, code, analysis)
    comparisons = [{'label': 'stock', 'sha256': STOCK_SHA, **difference(stock, raw, masks)}]
    for row in inventory['unique_images']:
        if row['classification'] == 'historical_tuned':
            before = historical_bytes(row['first_seen_path'], row['sha256'], inputs)
            comparisons.append({'label': row['first_seen_path'], 'sha256': row['sha256'], **difference(before, raw, masks)})
    pages = history['logged_pages']
    require(len(pages) == 16 and pages[0]['start'] == 0 and pages[-1]['start']+pages[-1]['length'] == SIZE
            and all(a['start']+a['length'] == b['start'] for a, b in zip(pages, pages[1:])), 'CRC page geometry')
    vector = [f"{zlib.crc32(raw[p['start']:p['start']+p['length']]):08x}" for p in pages]
    matches = [{'sha256': row['sha256'], 'paths': row['paths'],
                'exact_sha256_match': row['sha256'] == sha(raw),
                'page_CRC_matches': sum(a == b for a, b in zip(vector, row['page_crc32']))}
               for row in catalog['images']]
    return {'stock_and_historical_differences': comparisons, 'page_crc32': vector,
            'page_geometry': [{'start': p['start'], 'length': p['length']} for p in pages], 'catalog_matches': matches,
            'classification_limits': 'Overlapping categories are retained. Native calibration and defined-code coverage is incomplete; function chunks and four-byte data-reference hints are candidates, not ownership/type proof. All unclassified changes remain unknown. CRC matches do not establish cryptographic identity.'}


def association_review(path, inputs, raw_sha, finalization_sha):
    if path is None:
        return {'status': 'PENDING', 'reason': 'Human vehicle/session, pre/post BF and power-down association not supplied'}
    document = inputs.json(path)
    require(document.get('schema') == 1 and document.get('raw_sha256') == raw_sha
            and document.get('finalization_sha256') == finalization_sha, 'Association image/finalization binding')
    require(document.get('operator_confirmed_physical_session') is True and document.get('verified_power_down_and_OEM_return') is True,
            'Association needs explicit operator physical/power-down confirmation')
    for key in ('session_id', 'vehicle_reference', 'operator_confirmation', 'power_down_method'):
        require(isinstance(document.get(key), str) and document[key].strip(), 'Missing association '+key)
    for key in ('pre_BF_evidence', 'post_BF_evidence'):
        record = document[key]
        evidence = inputs.read(record['path'], record['sha256'])
        require(evidence, 'Empty BF evidence')
    return {'status': 'PENDING_HUMAN_REVIEW', 'document_sha256': sha(inputs.read(path)),
            'reason': 'Operator declarations and BF evidence are hash-linked; this tool does not authenticate their physical origin or approve their interpretation'}


def write_readonly(path, raw):
    with path.open('xb') as file:
        file.write(raw)
        file.flush()
        os.fsync(file.fileno())
    path.chmod(0o444)


def ingest(capture, output, association=None):
    output = Path(output).resolve()
    require(output.is_relative_to(FINAL.resolve()) and output != FINAL.resolve(), 'Output must be a new directory below A2WC511R_Final')
    output.mkdir(parents=True, exist_ok=False)
    inputs = Inputs()
    result = {'schema': 1, 'status': 'FAIL', 'current_ROM_identified': False, 'flash_authorized': False,
              'provider_loaded': False, 'raw_normalized': False, 'raw_copies': [], 'source': {'path': str(Path(__file__).resolve()), 'sha256': sha(Path(__file__).read_bytes())}}
    try:
        api, checksum = load_apis(inputs)
        raws, finalization_path, proof = validate_capture(capture, inputs, api)
        common = inputs.json(OLD/'tools/prehardware/validator_registry.json')['common']
        result['raw_sha256'] = sha(raws[0])
        result['image_checks'] = image_checks(raws[0], common, checksum)
        image_valid = all(c['status'] == 'PASS' for c in result['image_checks'])
        result['image_qualification'] = 'PASS' if image_valid else 'FAIL'
        result['classification_model_matches_identity'] = all(c['status'] == 'PASS' for c in result['image_checks'] if c['id'] in ('CALID', 'ECUID'))
        result.update(compare_catalogs(raws[0], inputs, common))
        result['association'] = association_review(association, inputs, sha(raws[0]), sha(inputs.read(finalization_path)))
        result['capture_replay'] = proof
        inputs.recheck()
        for index, raw in enumerate(raws):
            path = output/f'raw_pass{index}.bin'
            write_readonly(path, raw)
            result['raw_copies'].append({'path': str(path), 'sha256': sha(raw), 'bytes': len(raw)})
        result['status'] = 'PASS_OFFLINE_INGESTION_ASSOCIATION_PENDING' if image_valid else 'FAIL_IMAGE_CHECKS_CAPTURE_PRESERVED'
    except Exception as error:
        result['error'] = f'{type(error).__name__}: {error}'
    result['input_manifest'] = inputs.manifest()
    write_readonly(output/'INGESTION.json', (json.dumps(result, indent=2)+'\n').encode())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--association', type=Path)
    args = parser.parse_args()
    try:
        result = ingest(args.capture, args.output_dir, args.association)
    except (OSError, ValueError) as error:
        print(json.dumps({'status': 'FAIL', 'error': str(error)}))
        return 3
    print(json.dumps({'status': result['status'], 'report': str(args.output_dir.resolve()/'INGESTION.json'),
                      'current_ROM_identified': False, 'error': result.get('error')}, indent=2))
    return 3 if result['status'].startswith('FAIL') else 2


if __name__ == '__main__':
    raise SystemExit(main())
