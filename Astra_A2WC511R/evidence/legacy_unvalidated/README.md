# MerpMod A2WC511R starter bundle

This is a **non-flashable porting starter**, not a completed ECU patch.

It contains:
- a reproducible repository setup script;
- an A2WC511R target-config starter;
- a target-header template containing binary-verified and family-derived candidates;
- a linker-script template;
- launch-only design notes;
- validation gates.

The target header intentionally ends in `#error`. Do not remove it until the missing
RAM-hole, timing-hook, and POLF-hook symbols have been found and every candidate has
been verified against the exact ROM and live logger.
