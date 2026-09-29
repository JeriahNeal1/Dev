"""Build isolated replacements; never create a full ROM or reuse FF/table space."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import re
import subprocess

PROJECT = Path('C:/Dev/Astra_A2WC511R')
SOURCE = PROJECT / 'work/M07/semantic'
OUTPUT = PROJECT / 'reports/local/m07_residency/semantic'
TOOLS = Path('C:/Program Files (x86)/Renesas/Hew/Tools/KPIT/GNUSH-ELF/v13.01/sh-elf/bin')
CANDIDATES = dict(division=(0x4260, 0x430A), range_tail=(0x1473C, 0x147AC))


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    stock = Path('C:/Dev/SubaruRoms/OEM/A2WC511R.bin').read_bytes()
    manifest = dict(classification='EXPERIMENTAL_SEMANTIC_REPLACEMENTS_NOT_ACCEPTED_RESIDENCY',
                    created_utc=datetime.now(timezone.utc).isoformat(), stock_sha256=sha256(stock).hexdigest(),
                    candidates={}, commands=[])
    def run(args, log):
        result = subprocess.run([str(a) for a in args], capture_output=True, text=True, cwd=SOURCE)
        (OUTPUT / log).write_text(result.stdout + result.stderr, encoding='utf-8')
        manifest['commands'].append(dict(argv=[str(a) for a in args], exit_code=result.returncode, log=log))
        result.check_returncode()
    for name, (start, end) in CANDIDATES.items():
        linker = SOURCE / (name + '.ld')
        linker.write_text('SECTIONS { . = 0x%X; .replacement : { *(.replacement) } /DISCARD/ : { *(.text) *(.data) *(.bss) } }\n' % start)
        obj, elf, binary = (OUTPUT / (name + suffix) for suffix in ('.o', '.elf', '.bin'))
        run([TOOLS / 'sh-elf-as.exe', '-big', '-renesas', '--isa=sh2e', SOURCE / (name + '.s'), '-o', obj], name + '.assemble.log')
        run([TOOLS / 'sh-elf-ld.exe', '-EB', '-T', linker, '-Map', OUTPUT / (name + '.map'), '-o', elf, obj], name + '.link.log')
        run([TOOLS / 'sh-elf-objcopy.exe', '-O', 'binary', '-j', '.replacement', elf, binary], name + '.extract.log')
        run([TOOLS / 'sh-elf-objdump.exe', '-d', '-msh2e', elf], name + '.disassembly.txt')
        disassembly = (OUTPUT / (name + '.disassembly.txt')).read_text()
        linked_start = int(re.search(r'([0-9a-f]+) <replacement_start>:', disassembly)[1], 16)
        if linked_start != start:
            raise AssertionError('Linked section entry alignment differs from requested overlay address')
        code = binary.read_bytes()
        if start + len(code) > end:
            raise AssertionError('Replacement does not fit original object span')
        manifest['candidates'][name] = dict(start=start, original_end_exclusive=end, replacement_end_exclusive=start + len(code),
            bytes_saved=end - start - len(code), source=str(SOURCE / (name + '.s')), binary=str(binary), elf=str(elf),
            expected_before_hex=stock[start:start + len(code)].hex(), replacement_hex=code.hex(),
            source_sha256=sha256((SOURCE / (name + '.s')).read_bytes()).hexdigest(),
            binary_sha256=sha256(code).hexdigest(), elf_sha256=sha256(elf.read_bytes()).hexdigest(),
            reclaimed_tail_status='FAIL_PENDING_COMPLETE_ENTRY_AND_READ_OWNERSHIP_PROOF')
    manifest['core_sha256'] = sha256((Path(__file__).parent / 'sh2e.py').read_bytes()).hexdigest()
    (OUTPUT / 'candidate_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({k: {a: v[a] for a in ('start', 'replacement_end_exclusive', 'bytes_saved')} for k, v in manifest['candidates'].items()}))


if __name__ == '__main__':
    main()
