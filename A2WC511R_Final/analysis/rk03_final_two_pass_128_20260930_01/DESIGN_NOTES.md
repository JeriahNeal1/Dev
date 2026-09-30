# Final two-pass128 design checkpoint

Derived from the physically successful128 stage; keep new fixed1808-byte kernel808a5523d47de11881bfc2ea06a35278aedb5122ed51e8110f817b3210adb653 and complete24-request upload/start/identity prefix. Fixed compile-time read scheduler indexes0..16383, pass=index/8192, address=(index%8192)*128. Strict next-index dispatch; no user-controlled address/size/pass/kernel. Exactly16408 total transmissions on success.

Validate139-byte BEEF responses against counter-derived pass/address, bodylength134, command83, checksum,128data; retain bounded fragment/status/deadline semantics. Compare each pass1 block immediately against pass0; no retry. Capture two exclusive new raw files, check writes/flush/exact1MiB lengths/fullbyte identity/SHA256. Compare both independently against fixed locked hash-pinned current.bin as separate provenance result; consistent changed ECU bytes may transport-PASS while baseline comparison fails.

Required new tests: full2pass8192block schedule; independent Python address/coverage/frame oracle; changed-current positive; representative first/middle/final malformed/checksum/transport/mismatch; missing/duplicate/reordered frames; filewrite and cleanup failure. All fake only. Preserve completephysicalAPIlogging; fake logs may be losslessly compressed to avoid duplicate large evidence.

Two identical native builds, agent independent review of root implementation, root review of new tests, new releasecertificate and exact once launcher/recovery/finalintegrity controls. Do not execute final acquisition thisrun. Final authorization: PROCEED RK03 FINAL TWO PASS ACQUISITION.
