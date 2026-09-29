# Target-specific static closure

The remaining global ownership gate is **FAIL**, with narrower known domains.
This report interprets `TARGET_DOMAIN_CLOSURE.json` and the pinned instruction
slices in `TARGET_CALLER_WINDOWS.txt`; it adds no concrete simulator scenarios.

The 33 PC-relative DDF4 call/jump slices use selectors 0/1/2 and constant descriptor
indices. For those exact local argument contracts, DE3E callbacks reduce to
`129D4`, `129DA` and `129E0`, outside both candidate objects. Other descriptor
types bypass that callback. This is not proof that every incoming DDF4 path has
one of those argument definitions, nor a transitive proof of the other handler.

The fixed transition at 471BE reads ROM[1004]=125C. Visible boot target assignments
at the 700 path include 868, ROM[1000]=1150 and ROM[FFFF8]=F60C. These local values
are outside the candidate ranges; reset, callee and hardware behavior are not
universally inferred from them.

An explicit boot protocol path remains open: handler 978 calls the byte assembler
12C and stores its four-byte result at FFFFBFA0 at 99A. Dispatch 900 reaches B4,
which loads that word into R4 and transfers through 40/42 (`JMP @R4`). The observed
header/type checks do not whitelist the assembled target. Unconstrained caller
bytes cover all 32-bit words, including aligned addresses in the candidate tails.
This is an external execution-command boundary, not evidence that ordinary task
operation enters those interiors. Excluding it requires an explicit admissible
operating/entry contract, which this run has not silently imposed.

The RTOS 3980 direct-target exclusion remains valid: all 65,536 state/index byte
pairs yield 127 aligned source words and no direct target inside either object.
Its superset includes ROM[4AA4]=40, so it can transitively reach the R4 trampoline
without a valid-context restriction. A one-hop exclusion is not a transitive
control-flow proof. Misaligned loads retain their architectural exception status.

Unknown calculated callers, context validity, interrupt/exception behavior,
internal code-as-data readers and flash mutation remain outside these slices.
The analysis does not authorize reclaiming a tail or replacing those domains
with a favorable finite sample set.

Reproduction from `C:\Dev\A2WC511R_Sim`:

```powershell
py -3 -B m07_target_domain_closure.py
```

The script verifies exact input bytes and records the stock ROM and source
hashes. Its final `FAIL` is the intended global gate result; local contract
exclusions are recorded separately.
