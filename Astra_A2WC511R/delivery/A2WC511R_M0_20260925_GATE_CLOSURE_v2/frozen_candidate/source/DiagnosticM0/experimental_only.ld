/* UNAPPROVED allocations, root-authorized static/emulator engineering artifact.
 * ROM FF content and lack of exact pointer matches do NOT prove these are free.
 * This file must not be used to approve or label a firmware release. */
OUTPUT_ARCH(sh)
ENTRY(_m0_decoder_hook)
SECTIONS {
 .m0 0x000E1000 : { *(.m0.code) *(.text) *(.text.*) *(.rodata*) *(.m0.identity) }
 _m0_state = 0xFFFF7400;
 .forbidden 0x71000000 : { *(.data*) *(.bss*) *(COMMON) }
 /DISCARD/ : { *(.comment) *(.note*) }
}
ASSERT(SIZEOF(.forbidden) == 0, "Unexpected global writable state")
ASSERT(SIZEOF(.m0) <= 4096, "Diagnostic code exceeds provisional audit budget")
