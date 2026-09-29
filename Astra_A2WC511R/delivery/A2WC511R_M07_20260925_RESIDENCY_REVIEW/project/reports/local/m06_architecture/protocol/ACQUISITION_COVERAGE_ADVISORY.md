# Superseding acquisition advisory: full-image attestation withdrawn

**COLLECTOR_FULL_IMAGE_ATTESTATION: FAIL. Do not use the previous 80-minute
two-pass SSM procedure to identify the complete current ROM.** This advisory
supersedes the image-attestation claim in
`reports/local/gate_closure/calibration/ONE_CONNECTION_READ_ONLY_ACQUISITION.md`.
The frozen package and sealed collector remain unchanged as historical evidence.
No physical acquisition was performed or is requested now.

Actual OEM execution now proves that a valid A0 reply can contain substituted
FF bytes rather than the addressed flash contents. A transport checksum verifies
the reply's transmission; two equal hashes verify repeatability. Neither proves
which physical flash bytes were read. An all-FF result in these regions is not
an explicit rejected or malformed response, so the old abort checks miss it.

## Exact byte-coverage failure

`../rom_reclamation/verify_native_read_boundaries.json` records 72 actual OEM
classifier/getter contracts, described in `NATIVE_ROM_READ_COUNTEREXAMPLE.md`:

| ROM range | Native A0 result under tested security states 00 and 04 |
| --- | --- |
| `[000000,002000)` | FF substitution |
| `[002000,0C0034)` | Actual bytes only when FFFF64B8 bit04 is clear |
| `[0C0034,0FFB80)` | Actual bytes under both tested states |
| `[0FFB80,100000)` | FF substitution |

The first and last masked spans total 9,344 address positions. The unchanged
collector checks BF ECUID, a pilot CALID at 2000, CALID consistency in both
images, valid frames, lengths, and equality of two full response-image hashes.
It does not establish read coverage or validate the returned vector/boot region
against an independently trusted current image. The pilot sits outside the two
always-masked spans and therefore cannot detect them.

`collector_admission_counterexample.json` records an actual run of the unchanged
sealed collector against an explicitly synthetic virtual endpoint. The endpoint
returns the baseline ROM with the two masked spans substituted by FF. ECUID and
CALID remain correct. The two views are identical, but 8,587 bytes differ from
the real baseline. The collector still reports `PASS_READ_ACQUISITION_ONLY`
after 9,002 requests. All 107 sealed runtime artifact hashes were checked first.
No provider was loaded, no ECU executed this synthetic endpoint, and no sealed
source, class, manifest, launcher, or original ROM was changed.

The synthetic test proves the collector's admission weakness. The separate
actual OEM instruction tests prove the relevant masking behavior. Their evidence
boundaries are distinct; no simulated data is labeled current ECU telemetry.

Ordinary A8 does not automatically solve this problem. With control 0, addresses
below 190 select indexed getter handlers rather than those physical ROM bytes.
Direct-address A8 paths use the same classifier. Readable handler output must
not be relabeled as byte coverage of a flash address.

## Required correction before any future full-image acquisition

The current prepared collector must not confer current-ROM identity. A corrected
entry must fail closed until its exact command, current firmware implementation,
security state and every requested address range have an independently reviewed
physical-byte coverage contract. Equality, CALID, frame checksums, or a plausible
engine-calibration checksum are insufficient substitutes. No automatic kernel,
write, reset, alternate-command, or provider fallback is authorized.

A future passive capability preflight should be short. Identify the module,
read the pilot CALID, and inspect small windows at the boot-vector region and
around 1FF8/2000/C0034/FFB78/FFB80. Compare them only with independently trusted
expectations and the reviewed service semantics. An FF reply or handler-derived
value is inconclusive about the underlying flash contents; this stock service's
known substituted ranges are already sufficient to block complete attestation.
Do not proceed to an 80-minute read merely because those short requests receive
well-formed replies. A supported full-image route remains a separate engineering
choice, with any physical actions deferred to the user.

If no existing passive service can expose every required byte, the missing
physical datum remains a trustworthy current full image acquired through a
separately reviewed method. ECUFlash's historical Read uploaded a RAM kernel;
it cannot silently replace a procedure requiring no commanded ECU-memory write.
No such alternate operation is implemented or invoked here.

## Six diagnostic channels remain sufficient

The sealed collector's public RAM array is exactly
`FF4C75, FF4C8D, FF4CA1, FF4C50, FF4BC1, FF4BC2`. The RAW4 page 0 addresses are
the first four; page 1 uses the last two plus the existing snapshot at FF4C8D.
The fourth page-1 byte is derived locally from those three values. There are no
additional raw channels required by either the ECU prototype or host facade.
Both facade A8 requests fall within the sealed read gate's existing whitelist;
the project BE command itself remains correctly forbidden there.

Existing initial/final bursts and host phase/timestamps can retain these raw
observations, but normal traces still do not establish freshness, fault behavior,
physical gear or atomic six-byte coherence. The newly identified blocker concerns
full-ROM coverage, not an absent seventh channel. The offline host facade and
compiled replay remain usable without attaching a physical backend.
