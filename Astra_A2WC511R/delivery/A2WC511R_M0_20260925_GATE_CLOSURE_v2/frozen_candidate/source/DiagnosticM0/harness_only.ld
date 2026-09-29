/* Synthetic addresses deliberately outside 1 MiB ECU flash and real ECU RAM.
 * For callable execution/allocation sizing only. NEVER flatten into a ROM.
 * No OEM hook word, boot vector, checksum or target definition is emitted. */
OUTPUT_ARCH(sh)
ENTRY(_m0_decoder_hook)
SECTIONS {
 .m0 0x07001000 : { *(.m0.code) *(.text) *(.text.*) *(.rodata*) *(.m0.identity) }
 _m0_state = 0x70000000;
 .forbidden 0x71000000 : { *(.data*) *(.bss*) *(COMMON) }
 /DISCARD/ : { *(.comment) *(.note*) }
}
ASSERT(SIZEOF(.forbidden) == 0, "Unexpected global writable state")
ASSERT(SIZEOF(.m0) <= 4096, "Diagnostic code exceeds provisional audit budget")
