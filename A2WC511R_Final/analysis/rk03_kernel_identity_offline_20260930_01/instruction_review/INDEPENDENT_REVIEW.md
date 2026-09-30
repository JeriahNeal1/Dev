# Independent offline start and identity review

**PASS — no blocking finding for the bounded offline model.** This review does not qualify or authorize a physical kernel start.

The reviewer checked the root-authored three-source zipapp and its saved qualification without executing it again. Both build artifacts have SHA256 `04d8332493c98e90fa3c537c8ea0bc12926b5a85e37ea8ea9c826ec8e03c34fe`. Their exact archive contents match the reviewed source files. The only external imports in that source closure are Python `json`, `hashlib` and `sys`; provider function names are inert data strings. The command line accepts no arguments.

The model has exactly 24 fixed transmissions: the retained 22-transmission successful upload sequence, one OEM start and one identity request. All 82 normalized prefix actions match the successful physical reference. Every upload ACK is required before start. All 433 saved negative journals match their recorded digests, stop protocol actions at the injected failure, retain only a fixed transmit prefix, and avoid retries. The root's 526 checks and the reviewer's 1,832 read-only assertions passed. Earlier native qualification was reused, not recounted.

The reviewer separately executed a bounded SH-2E instruction replay. The completed upload was reconstructed from retained current-ROM memory writes, including their source provenance; upload instructions were not rerun. The OEM start executed 2,902 instructions and matched the retained stock start suffix exactly for instruction, memory and peripheral events:

| Item | Exact value |
|---|---|
| Start request | `8010f003310101b6` |
| Executed OEM ACK | `80f01003710101f6` |
| Reached entry | `FFFF3004` |
| Identity request | `beef000101af` |
| Executed identity response | `beef000f8141325743353131522d524b3032005f` |
| Identity body | `81` followed by `A2WC511R-RK02` and NUL |

Two separate kernel instances were checked: the retained poisoned-register fixture, then the actual ending OEM general registers, SR, PR, MACH and MACL. Each executed 4,214 startup instructions and 564 identity instructions, with exactly one identity request. Both entered identity PC `FFFF311E`, never entered raw-read PC `FFFF3134`, and performed zero kernel ROM-data reads or flash writes. The shared transmit loop read precisely the 15-byte RAM-resident identity body. The unchanged 1,808-byte image remains SHA256 `3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581`.

VBR `00001F44` is explicitly admitted from the retained boot-entry contract; the per-byte OEM parser replay does not reproduce that earlier setup. The second kernel instance carries the recorded SCR and ready-SSR/watchdog assumptions into its peripheral fixture. Remaining peripheral defaults and abstract instruction-tick scheduling are declared. These are linked model checks, not uninterrupted vehicle execution or silicon timing evidence. Legitimate OEM ROM-constant reads are distinct from the zero ROM-data reads in the kernel identity phase.

The static transcript uses the captured seed/key and resource identifiers as fixed fixtures. Its synthetic start/identity metadata, virtual waits and complete reply fixtures do not qualify native ABI handling, provider behavior, receive fragmentation, wall-clock deadlines, or physical entry. Those gaps remain explicit in the future physical release plan. The kernel itself retains its earlier raw-read capability; this fixed identity-only path never reaches it.

Two failed reviewer attempts are preserved. The first reconstruction omitted source-taint metadata that fixture initialization clears; restoring the recorded write origins produced an exact trace match. The second assertion incorrectly excluded the shared transmit loop; it was replaced with checks of the exact identity-body read addresses while preserving the raw-read exclusions. Neither failure required a kernel, simulator, model, or historical-evidence change.

The final machine-readable review is `INDEPENDENT_REVIEW.json`, SHA256 `b431059c8bf5bfd910d67e82c48b42e540ba10391897569db072c02ac5cbbe2f`. The passing instruction report is `replay_20260930T054149444398Z/INSTRUCTION_REPLAY.json`, SHA256 `300de29c90b7f79b7bc845859232bcc75f08ce3a311f749f0851e01f7bca0ffa`. Both include exact input and output pins. No provider, physical client, native vehicle executable, or acquisition request was invoked.
