"""Qualified comments only in the existing stock IDB; no bytes or items edited."""
from pathlib import Path
from hashlib import sha256
import json
import ida_bytes, ida_funcs, idc
root = Path('C:/Dev/Astra_A2WC511R')
out = root/'reports/local/m07_residency/ida'
backup = root/'backups/m07_residency_20260925/A2WC511R_STOCK_ROMRAIDER.bin.i64'
assert backup.is_file() and backup.stat().st_size > 1000000
before = ida_bytes.get_bytes(0, 0x100000)
assert sha256(before).hexdigest() == 'a34c4ce8238bf28bdc18c191bbe73b2179130aa9846e952a6fa332bae442de96'
comments = {
    0x4260: '[M0.7 RESEARCH 2026-09-26] Signed division: original 170 bytes through 0x430A; loop replacement 68 bytes tested separately. Structural 32 DIV1/ROTCL proof under entry/private-stack/noninterleaving contract; extra 4 stack bytes, up to 210 vs 79 instructions in tests. Proposed [42A4,430A) tail is NOT accepted ownership: calculated-entry/internal data-consumer contracts remain open. IDB remains original OEM bytes. Evidence: reports/local/m07_residency/semantic and ownership_review.',
    0x1466E: '[M0.7 RESEARCH 2026-09-26] Original MOV #64,R6 supports bounded nibble switch replacement at [1473C,147AC): 112 original bytes become 52 bytes. All 16 nibble cases/T predicate preserved under enclosing entry contract. Proposed [14770,147AC) tail is NOT accepted ownership. Shared literals preceding1473C remain used by other functions and cannot be reclaimed. No patch applied to IDB. See M07 semantic/ownership reports.',
    0x484B0: '[M0.7 RESEARCH 2026-09-26] Live unknown-command path, NOT dead/free code. Separate adapter experiments exact-match fixed BE/version/page/address frames, select FC/FD response, and reuse unchanged native A8 producer/progress. No persistent project RAM/refill hook. 100-byte one-page or 148-byte split two-page payload remains unapproved residency. Stock dispatcher bytes retained here; original SR.T=0 entry/PR and dead R2/R3 continuation contracts documented separately.'
}
changes = []
for address, text in comments.items():
    assert ida_funcs.get_func(address) is not None
    old = idc.get_cmt(address, 1) or ''
    if text in old:
        continue
    updated = old + ('\n\n' if old else '') + text
    assert idc.set_cmt(address, updated, 1)
    assert idc.get_cmt(address, 1) == updated
    changes.append({'address':address, 'before':old, 'after':updated})
assert ida_bytes.get_bytes(0, 0x100000) == before
result = {'status':'PASS_QUALIFIED_COMMENTS_ONLY', 'backup':str(backup),
    'backup_sha256':sha256(backup.read_bytes()).hexdigest(),
    'ROM_bytes_unchanged_sha256':sha256(before).hexdigest(), 'comments':changes,
    'ownership_claimed':False, 'new_names_or_functions':False}
(out/'M07_METADATA_WRITES.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'comments':len(changes),'rom_sha256':result['ROM_bytes_unchanged_sha256']}))
