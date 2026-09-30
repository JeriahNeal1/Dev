# RK03 bounded physical read release — qualified, awaiting human gates

Native qualification: 1,116/1,116 PASS (538 positive, 578 negative), reusing sealed prior evidence without rerunning its qualification. All522 response splits, all512 corruption positions and simultaneous512 mismatches covered. Two clean native builds are byte-identical. Launcher36, recovery14 and result-validator54 checks PASS. Root fixture/journal audit5582 and independent native/control review6879 checks PASS.

Branch: `rk03/bounded-rom-read-physical`; commit: `96f6c49030b2d1c694e388ba6a1925d62d83b56a`.
Executable SHA256: `5a66a0848601c8564a6896ddabbc35af453179c68c79ec871bee6d73e120bfb9`.
Certificate SHA256: `15ba34b4d14c17e104fe28163faf7afe6b3c11b067ecf15a3bc97f8af8b253d1`.
Kernel SHA256: `3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581`.

The retained24-exchange upload/start/identity prefix is followed by exactly one request `beef00080300000000000200ba`: pass0, address00000000, length512. The523-byte response must have the fixed framing, pass/address/length, additive checksum and exact current.bin data. Expected data SHA256: `d3421c81a4380638a8844e34012db592ba6eed35ca5cb8402880b79869e71f01`.

Structural boundary: request/exchange admit only stages0..24; stage24 requires validated identity; only one call reaches it; after its validated reply, only cleanup is reachable. Physical CLI accepts no address, length or payload. There is no second read, second start, flash operation or retry path. A complete data mismatch records every changed position before terminal failure/cleanup. Original2000ms response deadline is retained.

Physical invocation count:0. Fresh human states IGNITION OFF then TEST MODE ON and exact token `PROCEED RK03 BOUNDED ROM READ` are still required. No prior authorization applies.

After the single run, request IGNITION OFF then NORMAL MODE ON and run the pinned passive BF/A8 OEM-return check. If bounded read and OEM return pass, continue IN THIS RUN with OFFLINE qualification of the final `RK03_FULL_ROM_TWO_PASS_PHYSICAL` release. Never execute the final full acquisition in this run. The final release is not yet built or qualified.

Only operator-managed simplified states are allowed. No component/voltage sub-gates.
