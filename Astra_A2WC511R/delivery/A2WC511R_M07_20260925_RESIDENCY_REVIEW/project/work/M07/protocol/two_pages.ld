OUTPUT_FORMAT("elf32-sh")
OUTPUT_ARCH(sh)
SECTIONS {
  .m07_match 0x000042A4 : { *(.m07_match) }
  .m07_main 0x00014770 : { *(.m07_main) }
  /DISCARD/ : { *(.data) *(.bss) *(.comment) *(.note*) }
}
ASSERT(SIZEOF(.m07_match) <= 102, "Matcher exceeds candidate division tail")
ASSERT(SIZEOF(.m07_main) <= 60, "Adapter exceeds candidate range tail")
