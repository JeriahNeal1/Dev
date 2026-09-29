# Structural comparison driver

Run from any directory using the existing ABI-matched CPython:

```powershell
py -3.14 C:\Dev\Astra_A2WC511R\tools\diaphora\compare_exports.py LEFT.sqlite RIGHT.sqlite --output-dir NEW_OUTPUT_DIRECTORY
```

The output directory must not exist. Quote paths containing spaces. For complete
ROM/IDB provenance, add `--left-rom`, `--right-rom`, `--left-idb`, and `--right-idb`
with their actual local paths. Supplied ROMs must match the native export's input
MD5 identity; each artifact also receives a SHA256.

The driver validates closed complete SQLite exports, checks an accompanying
`.export.json` native address-set/hash manifest when present, and compares
disposable copies. It never launches IDA or imports metadata. The full writable
Diaphora tree and ABI-specific vendor directory are resolved explicitly.

`comparison.json` records input/output hashes, package/source versions, typed
options, match/unmatched counts, instruction-byte hash agreement, and a canonical
result hash that omits output paths, timestamps and chooser row numbers. Literal
pools and ownership are outside Diaphora's instruction hash. A score of 1.0 is
never promoted to a semantic or residency claim by this tool.

The profile explicitly ignores function-name identity, disables decompiler,
microcode, pretrained ML and experimental name-based patch shortcuts, and retains
slow structural heuristics. It uses one matching worker. SQL timeout and row
limits are recorded; runtime errors/observed timeout messages cause FAIL.
The project hook explicitly omits only the 'Related compilation unit' pass:
raw ROMs have no genuine source/DWARF CU evidence, and inferred regions can cause
repeated Cartesian scans. The omission is recorded and leaves missed candidates
unknown. Unmatched result addresses are checked against their labeled database
side; the corrected primary/secondary mapping also passes native chooser tests.

Smoke example using the retained native three-function export:

```powershell
py -3.14 C:\Dev\Astra_A2WC511R\tools\diaphora\compare_exports.py C:\Dev\Astra_A2WC511R\work\diaphora\exports\tiny_structural_01.sqlite C:\Dev\Astra_A2WC511R\work\diaphora\exports\tiny_structural_01.sqlite --output-dir C:\Dev\Astra_A2WC511R\work\diaphora\comparisons\MY_NEW_SMOKE_RUN --require-self-identity
```

Expected: three best matches, three identical exported instruction hash/size/
address combinations, zero partial/ambiguous/unmatched entries. Runs
`tiny_self_02` and `tiny_self_03_clean` pass with canonical result SHA256
`5de8a3d935aea6767cbba463b8bb1a2ea4f00740d0638f5e9d204638fa93aff2`.
The latter ran in a clean process with `C:\Windows\Temp` as its working directory.
The empty failed native export is correctly rejected by
`empty_export_negative_01`.

The old tiny_self_01 directory is retained as failed wrapper evidence: matching
itself completed, but result JSON initially failed because native `program.md5sum`
is a SQLite BLOB. The wrapper now explicitly converts the binary/ASCII MD5 form,
and fresh successful runs verify the repair.
