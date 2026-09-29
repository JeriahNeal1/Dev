OUTPUT_FORMAT("elf32-sh")
OUTPUT_ARCH(sh)
SECTIONS {
  .m07 0x000042A4 : { *(.m07) }
  /DISCARD/ : { *(.data) *(.bss) *(.comment) *(.note*) }
}
ASSERT(SIZEOF(.m07) <= 102, "Does not fit candidate tail; ownership still unproved")
