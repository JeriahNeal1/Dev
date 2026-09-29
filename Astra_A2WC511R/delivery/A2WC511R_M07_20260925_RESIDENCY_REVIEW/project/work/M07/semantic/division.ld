SECTIONS { . = 0x4260; .replacement : { *(.replacement) } /DISCARD/ : { *(.text) *(.data) *(.bss) } }
