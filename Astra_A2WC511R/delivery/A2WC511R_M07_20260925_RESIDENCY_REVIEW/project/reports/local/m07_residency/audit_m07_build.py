"""Fresh M0.7 reconstruction, exact inverse and native checksum comparison.

Research-only outputs. No device API or modification of any build input.
"""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import argparse, json, struct, subprocess, sys
sys.dont_write_bytecode = True
ROOT = Path('C:/Dev/Astra_A2WC511R')
REPORT = ROOT / 'reports/local/m07_residency'
TOOLS = Path('C:/Program Files (x86)/Renesas/Hew/Tools/KPIT/GNUSH-ELF/v13.01/sh-elf/bin')
sys.path.insert(0, str(ROOT / 'reports/local/interfaces'))
from checksum_audit import correction, records, BASELINE, BASELINE_SHA

def digest(path):
    return sha256(path.read_bytes()).hexdigest()

def ranges(addresses):
    result = []
    for address in addresses:
        if result and result[-1][1] == address:
            result[-1][1] = address + 1
        else:
            result.append([address, address + 1])
    return result

def elf_semantics(data):
    """Compare every section and symbol, allowing only STT_FILE path changes."""
    header = struct.unpack_from('>16sHHIIIIIHHHHHH', data)
    assert header[0][:6] == b'\x7fELF\x01\x02'
    phoff, shoff, phsize, phnum, shsize, shnum, shstr = header[5], header[6], header[9], header[10], header[11], header[12], header[13]
    sections = [struct.unpack_from('>10I', data, shoff+i*shsize) for i in range(shnum)]
    def section(i):
        h = sections[i]
        return data[h[4]:h[4]+h[5]]
    def string(blob, offset):
        return blob[offset:blob.index(b'\0', offset)].decode('ascii')
    names = section(shstr)
    result, file_symbols = [], []
    for i,h in enumerate(sections):
        name = string(names,h[0])
        # Nonloaded symbol/string metadata is represented structurally below.
        if h[1] == 2:
            symbols = []
            for pos in range(0,h[5],h[9]):
                s = struct.unpack_from('>IIIBBH', section(i), pos)
                symbol_name = string(section(h[6]),s[0])
                if s[3] & 15 == 4:
                    file_symbols.append(symbol_name)
                    symbol_name = '<STT_FILE>'
                symbols.append((symbol_name,*s[1:]))
            result.append((name,h[1:4],h[6:],symbols))
        elif name == '.strtab':
            assert not h[2] & 2
        else:
            result.append((name,h[1:],section(i).hex()))
    return (header,data[phoff:phoff+phsize*phnum].hex(),result),file_symbols

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=REPORT / 'build_audit_01')
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    commands = []
    def run(label, argv):
        argv = [str(x) for x in argv]
        result = subprocess.run(argv, capture_output=True, text=True, timeout=60)
        (out / (label + '.log')).write_text(json.dumps(argv) + '\n' + result.stdout + '\n' + result.stderr, encoding='utf-8')
        commands.append({'argv': argv, 'exit_code': result.returncode})
        if result.returncode:
            raise RuntimeError(label)
    repeated = {}
    specs = [
        ('division', 'semantic', [('.replacement', 'division.bin')], REPORT/'semantic', 'division.elf'),
        ('range_tail', 'semantic', [('.replacement', 'range_tail.bin')], REPORT/'semantic', 'range_tail.elf'),
        ('one_page', 'protocol', [('.m07', 'payload.bin')], REPORT/'protocol/one_page_01', 'payload.elf'),
        ('two_pages', 'protocol', [('.m07_match', 'match.bin'), ('.m07_main', 'main.bin')], REPORT/'protocol/two_pages_01', 'payload.elf')]
    for name, source_dir, sections, original, original_elf in specs:
        target = out / name
        target.mkdir()
        source = ROOT / 'work/M07' / source_dir / name
        obj, elf = target/'repeat.o', target/original_elf
        run(name+'_assemble', [TOOLS/'sh-elf-as.exe', '-big', '-renesas', '--isa=sh2e', source.with_suffix('.s'), '-o', obj])
        run(name+'_link', [TOOLS/'sh-elf-ld.exe', '-EB', '-T', source.with_suffix('.ld'), obj, '-o', elf])
        pairs = [(elf, original/original_elf)]
        for section, filename in sections:
            run(name+'_extract_'+filename, [TOOLS/'sh-elf-objcopy.exe', '-O', 'binary', '-j', section, elf, target/filename])
            pairs.append((target/filename, original/filename))
        comparisons = {}
        for repeat, old in pairs:
            exact = repeat.read_bytes() == old.read_bytes()
            detail = {'repeat_sha256':digest(repeat), 'original_sha256':digest(old), 'byte_identical':exact}
            if not exact:
                assert repeat.suffix == '.elf', ('Functional repeat differs', name, old)
                new_semantics,new_files = elf_semantics(repeat.read_bytes())
                old_semantics,old_files = elf_semantics(old.read_bytes())
                assert new_semantics == old_semantics, ('ELF semantics differ',name)
                for label,p in [('old',old),('repeat',repeat)]:
                    run(name+'_'+label+'_strip_file_metadata', [TOOLS/'sh-elf-objcopy.exe','--strip-debug',p,target/(label+'.without_file_metadata.elf')])
                    run(name+'_'+label+'_elf_inspect', [TOOLS/'sh-elf-readelf.exe','-Wa',p])
                assert (target/'old.without_file_metadata.elf').read_bytes() == (target/'repeat.without_file_metadata.elf').read_bytes()
                detail.update({'difference':'STT_FILE absolute object path and dependent string-table metadata only',
                    'old_FILE_symbols':old_files,'new_FILE_symbols':new_files,'all_other_ELF_sections_symbols_and_program_headers_equal':True,
                    'normalized_elf_sha256':digest(target/'repeat.without_file_metadata.elf')})
            comparisons[repeat.name] = detail
        repeated[name] = comparisons
    stock = BASELINE.read_bytes()
    assert digest(BASELINE) == BASELINE_SHA
    profiles = {}
    cp = ';'.join([str(ROOT/'work/romraider_acceptance/classes'), str(ROOT/'integrations/romraider/dist/romraider-bridge.jar'), 'C:/Program Files/RomRaider/RomRaider.jar', 'C:/Program Files/RomRaider/lib/*'])
    for profile in ('one_page', 'two_pages'):
        evidence = REPORT / 'protocol/execution_01'
        raw_path = evidence/(profile+'.RESEARCH_NOT_RESIDENCY_PROVEN.raw.bin')
        raw = raw_path.read_bytes()
        manifest = json.loads((evidence/(profile+'_overlay.json')).read_text())
        assert digest(raw_path) == manifest['rom_sha256']
        reconstructed, restored = bytearray(stock), bytearray(raw)
        spans = []
        for fragment in manifest['fragments']:
            start = fragment['address']
            before, after = bytes.fromhex(fragment['before_hex']), bytes.fromhex(fragment['after_hex'])
            assert len(before) == len(after)
            end = start+len(after)
            assert all(end <= a or start >= b for a, b in spans)
            assert stock[start:end] == before and raw[start:end] == after
            reconstructed[start:end] = after
            restored[start:end] = before
            spans.append((start, end))
        assert reconstructed == raw and restored == stock
        fixed = correction(raw)
        fixed_path = out/(profile+'.RESEARCH_NOT_RESIDENCY_PROVEN.checksum_corrected.bin')
        fixed_path.write_bytes(fixed)
        checksum_changed = [i for i,(a,b) in enumerate(zip(raw,fixed)) if a != b]
        assert all(any(r['descriptor_offset']+8 <= i < r['descriptor_offset']+12 for r in records(raw)) for i in checksum_changed)
        checksum_inverse = bytearray(fixed)
        for i in checksum_changed:
            checksum_inverse[i] = stock[i]
        for f in manifest['fragments']:
            before = bytes.fromhex(f['before_hex'])
            checksum_inverse[f['address']:f['address']+len(before)] = before
        assert checksum_inverse == stock
        protected = [(0,0x2000), (0x11AD8,0x11AE0), (0x4F310,0x4F950), (0xE1000,0xE1364), (0xFFC4C,0xFFC50)]
        assert all(stock[a:b] == raw[a:b] == fixed[a:b] for a,b in protected)
        if profile == 'one_page':
            assert stock[0x1466E:0x147AC] == raw[0x1466E:0x147AC]
        native = out/(profile+'.native_checksum.json')
        run(profile+'_native_checksum', ['java', '-Djava.awt.headless=true', '-cp', cp, 'rombridge.NativeChecksumCheck', raw_path, fixed_path, native])
        changes = [i for i,(a,b) in enumerate(zip(stock, raw)) if a != b]
        profiles[profile] = {'status':'PASS_BINARY_AUDIT_ONLY', 'raw_sha256':digest(raw_path),
            'corrected_sha256':digest(fixed_path), 'raw_changed_bytes':len(changes),
            'raw_changed_ranges':ranges(changes), 'overlay_spans':spans,
            'checksum_changed_addresses':checksum_changed, 'checksum_rows':records(fixed),
            'raw_and_corrected_inverse_exact':True, 'protected_spans_unchanged':protected,
            'native_checksum_report_sha256':digest(native), 'residency_status':'FAIL', 'flash_ready':False}
    preserved = []
    for root, manifest_path in [(ROOT, REPORT/'M06_FROZEN_MANIFEST.json'),
        (ROOT/'delivery/A2WC511R_M0_20260925_GATE_CLOSURE_v2', ROOT/'delivery/A2WC511R_M0_20260925_GATE_CLOSURE_v2/SHA256SUMS.json')]:
        files = json.loads(manifest_path.read_text())['files']
        for relative, expected in files.items():
            assert digest(root/relative) == expected, ('Frozen artifact changed', relative)
        preserved.append({'manifest':str(manifest_path), 'sha256':digest(manifest_path), 'verified_files':len(files)})
    result = {'status':'PASS', 'classification':'UNAPPROVED_RESEARCH_BINARY_AUDIT',
        'created_utc':datetime.now(timezone.utc).isoformat(), 'stock_sha256':BASELINE_SHA,
        'repeat_artifacts':repeated, 'profiles':profiles, 'frozen_artifacts':preserved,
        'commands':commands, 'tools':{p.name:digest(p) for p in [TOOLS/'sh-elf-as.exe', TOOLS/'sh-elf-ld.exe', TOOLS/'sh-elf-objcopy.exe']},
        'no_hardware_or_provider_access':True, 'no_ownership_or_silicon_claim':True}
    (out/'BUILD_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'repeated_artifact_groups':len(repeated),
        'profiles':{k:{key:v[key] for key in ('raw_sha256','corrected_sha256','raw_changed_bytes','residency_status')} for k,v in profiles.items()},'preserved':preserved}))
if __name__ == '__main__':
    main()
