OUTPUT_ARCH(sh)
ENTRY(kernel_entry)
MEMORY { TAKEOVER (rwx) : ORIGIN = 0xFFFF3000, LENGTH = 0x2000 }
SECTIONS {
  .entry 0xFFFF3000 : { KEEP(*(.entry)) } > TAKEOVER
  .text : { *(.text) } > TAKEOVER
  .rodata ALIGN(4) : { *(.rodata) } > TAKEOVER
  .vectors ALIGN(4) : { *(.vectors) } > TAKEOVER
  .integrity ALIGN(4) : { *(.integrity) } > TAKEOVER
  upload_end = .;
  .bss ALIGN(4) (NOLOAD) : { *(.bss) } > TAKEOVER
  takeover_end = .;
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
ASSERT(kernel_entry == 0xFFFF3004, "Stock loader fixed entry contract")
ASSERT(SIZEOF(.entry) == 4, "Fixed entry header")
ASSERT((upload_end & 3) == 0, "Loader longword checksum alignment")
ASSERT(SIZEOF(.text) < 940, "PC-relative literal reach conservative limit")
ASSERT(takeover_end <= 0xFFFF5000, "Bounded stock upload/private RAM window")
ASSERT(SIZEOF(.vectors) == 1024, "Complete private vector table")
ASSERT(stack_top - stack_low == 16, "Declared private exception stack")
ASSERT(ADDR(.bss) >= upload_end, "No writable overlap with uploaded object")
