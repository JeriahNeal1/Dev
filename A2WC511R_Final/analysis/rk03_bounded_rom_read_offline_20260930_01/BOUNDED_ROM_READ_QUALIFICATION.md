# RK03_BOUNDED_ROM_READ — sealed offline qualification

RK03_BOUNDED_ROM_READ = PASS OFFLINE ONLY

The new static-fake model passed122/122 checks, including78 fault injections. Two independent clean builds and their canonical manifests are byte-identical. Independent model/runner/build review, independent instruction-evidence review and packaging review passed. Prior native qualification and physical stages were reused rather than rerun or added to the count.

Branch: `rk03/bounded-rom-read-offline`.
Commit: `64da59dc1f4f2fe9e7d11c3443ac34034936c780`.
Model SHA256: `bf240d6c64257aca1952295c8a7bee03be714179124e002cdf45854d599aa0f6`.
Canonical build-manifest SHA256: `1ffadea2fb621b9797a62165db399e658cb5d592363e43b55badec28b44a8628`.
Qualification SHA256: `0ec65a7934e51c1d3afc4dfaeab9b53c6bf7355bd7f5b30a5f6384e3ffc6d44b`.

The only added modeled request is `beef00080300000000000200ba`: pass0, address00000000, length512. The unchanged kernel requires this minimum sequential first block; a smaller or CAL-ID-first request is invalid. The exact523-byte response contains command83, pass0, address00000000,512 data bytes and checksumE7. Full request/reply bytes are pinned in the contract.

Data SHA256: `d3421c81a4380638a8844e34012db592ba6eed35ca5cb8402880b79869e71f01`.
Complete reply SHA256: `796f64cefcd2b81c5c7662b2bdacad828c0a948c55bfdc5d002ac5c8da7f898e`.

Independent SH-2E execution restored the prior post-identity checkpoint and ran only one new fixed read:10,327 instructions,512 consecutive one-byte ROM loads from00000000 through000001FF, exact reply, cursor00000200/pass0, then RX_WAIT. No earlier upload/start/identity instructions were rerun, no flash writes occurred, and the kernel image was unchanged. Simulation does not establish physical timing.

The current.bin bytes remain authoritative, SHA256bf10be6d7c75b4f2ae663b0d57a912e6e9ef7654ccfc985195954596e50427b2. The selected512-byte block also equals stock, so it cannot identify the complete calibration or attest the whole current ROM. No ROM ingestion, Diaphora or historical tune analysis was repeated.

The distributable has no physical provider loader, OpenPort access, address/length/payload input, second read, second start, full-acquisition loop, retry or flash path. It accepts no CLI arguments. After its25th modeled exchange, only cleanup can occur. Earlier draft reporting-order failure and its corrected source history are preserved separately.

## Physical scope already completed

RK03_KERNEL_START_IDENTITY_PHYSICAL = PASS, exactly one invocation, all15 chunkACKs, one start atFFFF3004, exactA2WC511R-RK02 followed byNUL, clean exit. There were zero physical ROM-read or flash requests.

OEM_RETURN_AFTER_KERNEL_START_IDENTITY = PASS: BF2F12515306,120/120 six-variable samples, PASS_CAPTURE_ONLY, clean observer/broker/provider exit. Its evidence and the completed identity session are preserved unchanged.

## Next milestone

Separately qualify RK03_BOUNDED_ROM_READ_PHYSICAL from the proven native identity host. This needs a bounded523-byte streaming receiver, native ABI/deadline/failure tests, two matching native builds, independent review, a fresh certificate/session and later explicit operator authorization. The detailed design is in the committed FUTURE_PHYSICAL_RELEASE_PLAN.md. No additional physical operation was performed or authorized after OEM return in this run.
