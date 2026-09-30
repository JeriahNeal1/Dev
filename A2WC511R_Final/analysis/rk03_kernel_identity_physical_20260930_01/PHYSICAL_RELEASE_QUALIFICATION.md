# RK03 physical kernel start and identity: qualified, not executed

Branch `rk03/kernel-start-identity-physical`; commit `a8cb760b09e6219ae640419ddb030af2037a432e`.

386/386 native offline cases passed, with36 launcher,14 recovery and46 result-validator checks. Independent reviews passed. No hardware was opened.

Executable SHA256: `623dc766ca69a97b16f7beabc9acb909a1225eabb8a21c40fe8379b4f72b593f`.
Certificate SHA256: `19dc92d085a5721d7af280fc8fabf32a22919a9a370ec19e8052c8d6f8cf9cf8`.
Both canonical build manifests SHA256: `ec8d63c9d471e2377fd4a319601a19e639ec5ce4a26f5133231e63ad1d7eb80f`.
Unchanged1808-byte kernel SHA256: `3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581`.

Maximum sequence: retained transport/session setup and15 fixed upload chunks, one start atFFFF3004, exact startACK, stop OEM filter,62500-baud SET, fixedBEEF filter, one approved identity query, exactA2WC511R-RK02 withNUL, cleanup.24 transmissions maximum.

No ROM-read, flash, arbitrary memory access/input, second start or retry path is present in this host. The fixed identity query is expressly authorized but physical execution is not yet authorized.

Next human state: IGNITION OFF. Then TEST MODE ON. Before the exact new software authorization token, display release pins and check competing clients.

After one physical invocation, require IGNITION OFF then NORMAL MODE ON and passive BF/A8 OEM return. Only after identityPASS and OEM-returnPASS may RK03_BOUNDED_ROM_READ be prepared offline.
