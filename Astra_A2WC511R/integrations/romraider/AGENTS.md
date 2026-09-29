# RomRaider adapter maintenance

Read ../../docs/ROMRAIDER_API_CONTRACT.md and ../../docs/ROMRAIDER_ACCEPTANCE.md. Do not replace native table encoding with a partial reimplementation, add arbitrary reflection/eval endpoints, bypass native user levels/locks, or silently alter checksums. All mutable model calls run on Swing EDT. Preserve whole-buffer rollback, post-approval stale checks and timeout rejection.

If the installed JAR API differs, record its hash/version, inspect corresponding source or public methods, adapt narrowly and rerun source-contract plus actual disposable-file tests. A test double is not a compatibility proof. Keep test fixtures out of the deployed JAR. No vehicle I/O, flash or live RAM writes.
