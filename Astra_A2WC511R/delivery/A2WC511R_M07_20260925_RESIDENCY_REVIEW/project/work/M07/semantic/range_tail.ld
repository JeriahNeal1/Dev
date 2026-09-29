SECTIONS { . = 0x1473C; .replacement : { *(.replacement) } /DISCARD/ : { *(.text) *(.data) *(.bss) } }
