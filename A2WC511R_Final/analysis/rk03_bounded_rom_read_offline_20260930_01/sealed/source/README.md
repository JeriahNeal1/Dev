# RK03_BOUNDED_ROM_READ — offline only

This deterministic static-fake model adds exactly one fixed read to the successful
physical kernel-start/identity transcript. It has no provider loader, OpenPort
interface, device discovery, external payload input, address selector or physical
mode. The distributable accepts no command-line arguments.

The unchanged 1,808-byte kernel remains
`3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581`.
Its identity remains `A2WC511R-RK02\0`.

The minimum valid first read is **512 bytes at `00000000`**, pass 0. The kernel
requires sequential reads and checks length bytes `02 00`; a smaller request or
a first request at the CAL-ID location would fail. This stage reads only
`00000000–000001FF`, then stops. It does not begin a full 1 MiB acquisition.

- Request: `beef00080300000000000200ba` (13 bytes).
- Reply: `beef0206 83 00 00000000`, followed by 512 fixed bytes and checksum `e7`
  (523 bytes total; the full reply is pinned in `contract/CONTRACT.json`).
- Expected data SHA256:
  `d3421c81a4380638a8844e34012db592ba6eed35ca5cb8402880b79869e71f01`.
- Expected reply SHA256:
  `796f64cefcd2b81c5c7662b2bdacad828c0a948c55bfdc5d002ac5c8da7f898e`.

The authoritative source is the previously acquired current.bin, SHA256
`bf10be6d7c75b4f2ae663b0d57a912e6e9ef7654ccfc985195954596e50427b2`.
This particular block also equals verified stock. A successful bounded read can
validate framing, address, length and returned bytes; it cannot identify the
complete current calibration or prove that the whole image is factory stock.

The first 24 transmissions and 91 model actions are derived from the latest
successful physical identity session, including its captured seed/key. Captured
process pointers/timestamps are omitted; 200/100/200 ms waits are virtual. Only
the 25th exchange is synthetic. It is followed immediately by cleanup. Prior
transport and seed-algorithm qualification is reused, not rerun or recounted.

The new model passed **122/122 checks**, including 78 fault injections, CLI/input
exclusions and identical clean builds. A negative test found that the initial
draft set the read-validation flag before checking the complete output record;
the final source validates the output first. The draft and failure are preserved.

The separate SH-2E replay restores the retained post-identity checkpoint and
executes only this new request. It runs 10,327 instructions, observes exactly
512 sequential one-byte ROM loads, emits the exact 523-byte reply, and stops with
cursor `00000200`, pass 0. No earlier upload/start/identity instructions are rerun.
The kernel is waiting for another request at that point; this artifact cannot
send one. Simulation does not establish physical timing or a physical ROM read.

Two clean static-fake zipapps match SHA256
`bf240d6c64257aca1952295c8a7bee03be714179124e002cdf45854d599aa0f6`.
Build manifests match SHA256
`1ffadea2fb621b9797a62165db399e658cb5d592363e43b55badec28b44a8628`.

The physical identity session and passive OEM-return evidence remain unchanged.
No bounded physical read has occurred. The next milestone requires a separate
native physical release and later authorization; see `FUTURE_PHYSICAL_RELEASE_PLAN.md`.
