# hook_abi_and_timing

Partial PASS; timing/stack/reentrancy OPEN. Pool11ADC changes000147AC to000E12DC. Caller1193A/1193C/1193E returns11940. OEM decoder executes first. Differential evidence compares GPR/SR/MAC/PR and OEM writes; compiled closure is integer-only. Added stack124 bytes plus8 surrounding saved-PR bytes is not whole-task headroom. RTOS slot9/6580 ->11134 identified. See simulator runs and validation/local/ABI_ALLOCATION_REVIEW.md.
