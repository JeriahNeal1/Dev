/* Project-owned temporary RAM read kernel. SH-2E, SH7058, big endian.
 * No OEM calls, inherited RAM, libc, FPU, or flash-controller stores.
 * Register contract: r8=next ROM address, r9=pass, r10=identity seen;
 * r11=response mode. tx_frame saves PR in r14; tx_byte/rx_byte are leaves.
 * There are no software stack frames. Private stack is for exception entry.
 */
    .section .entry,"ax"
    .global upload_start
upload_start:
    nop
    nop
    .section .text,"ax"
    .global kernel_entry, rx_poll, halt_fail, halt_complete, halt_exception
kernel_entry:
    mov.l .Lstack,r15
    mov #0xf0,r0
    extu.b r0,r0
    ldc r0,sr
    mov.l .Lvectors,r0
    ldc r0,vbr

    /* Master-suspend DMA before initializing owned working memory. */
    mov.l .Ldmaor,r1
    mov.w @r1,r0
    mov #0,r0
    mov.w r0,@r1
    mov.w @r1,r0
    tst #1,r0
    bt 1f
    bra fatal
    nop
1:
    /* Keyed WDT disable: WTCSR reserved bits are explicitly 0x18. */
    mov.l .Lwtcsr,r1
    mov.b @r1,r0
    mov.l .Lwdt_off,r0
    mov.w r0,@r1
    mov.b @r1,r0
    tst #0x20,r0
    bt 2f
    bra fatal
    nop
2:
    /* Reject ROM emulation and non-default MAT selection, read-only. */
    mov.l .Lramer,r1
    mov.w @r1,r0
    tst #8,r0
    bt 3f
    bra fatal
    nop
3:
    mov.l .Lfmats,r1
    mov.b @r1,r0
    tst r0,r0
    bt 4f
    bra fatal
    nop
4:
    mov.l .Lwork_start,r1
    mov.l .Lwork_end,r2
    mov #0,r0
zero_work:
    mov.l r0,@r1
    add #4,r1
    cmp/eq r1,r2
    bf zero_work
    mov.l .Lguard_value,r0
    mov.l .Lguard_low,r1
    mov.l r0,@r1
    mov.l .Lguard_high,r1
    mov.l r0,@r1
    mov #0,r8
    mov #0,r9
    mov #0,r10
    mov #0,r11

    /* Documented SCI2 and PC2/PC3 mux, Pphi=20MHz -> 62500 baud. */
    mov.l .Lsci,r1
    mov #0,r0
    mov.b r0,@(2,r1)
    mov.b r0,@r1
    mov #0xf2,r0
    mov.b r0,@(6,r1)
    mov #9,r0
    mov.b r0,@(1,r1)
    mov.l .Lpccr,r2
    mov.w @r2,r0
    mov.l .Lpccr_mask,r3
    and r3,r0
    or #0x50,r0
    mov.w r0,@r2
    /* >=4096 instructions >16us even at the SH7058 80MHz ceiling. */
    mov.l .Lsettle_count,r2
settle_wait:
    dt r2
    bf settle_wait
    /* Read-before-clear and discard a stale receive byte if present. */
    mov.b @(4,r1),r0
    and #0xc7,r0
    mov.b r0,@(4,r1)
    mov.b @(4,r1),r0
    tst #0x40,r0
    bt stale_done
    mov.b @(5,r1),r0
    mov.b @(4,r1),r0
    and #0xbf,r0
    mov.b r0,@(4,r1)
stale_done:
    mov #0x30,r0
    mov.b r0,@(2,r1)

packet_start:
    bsr check_guards
    nop
    mov #0,r7
    bsr rx_byte
    nop
    add r0,r7
    xor #0xbe,r0
    tst r0,r0
    bt 5f
    bra fatal
    nop
5:
    bsr rx_byte
    nop
    add r0,r7
    xor #0xef,r0
    tst r0,r0
    bt 6f
    bra fatal
    nop
6:
    bsr rx_byte
    nop
    add r0,r7
    tst r0,r0
    bt 7f
    bra fatal
    nop
7:
    bsr rx_byte
    nop
    add r0,r7
    mov r0,r4
    cmp/eq #1,r0
    bt length_ok
    cmp/eq #8,r0
    bt length_ok
    bra fatal
    nop
length_ok:
    mov.l .Lrx,r5
    mov r4,r6
payload_loop:
    bsr rx_byte
    nop
    add r0,r7
    mov.b r0,@r5
    add #1,r5
    dt r6
    bf payload_loop
    bsr rx_byte
    nop
    extu.b r7,r7
    cmp/eq r0,r7
    bt 8f
    bra fatal
    nop
8:
    mov.l .Lrx,r1
    mov.b @r1,r0
    cmp/eq #1,r0
    bt identity
    cmp/eq #3,r0
    bt raw_read
    bra fatal
    nop
identity:
    mov r4,r0
    cmp/eq #1,r0
    bf fatal
    tst r10,r10
    bf fatal
    mov #1,r10
    mov #0,r11
    bsr tx_frame
    nop
    bra packet_start
    nop
raw_read:
    mov r4,r0
    cmp/eq #8,r0
    bf fatal
    mov r10,r0
    cmp/eq #1,r0
    bf fatal
    mov.b @(1,r1),r0
    extu.b r0,r0
    cmp/eq r0,r9
    bf fatal
    mov #0,r2
    mov r1,r5
    add #2,r5
    mov #4,r6
decode_address:
    shll8 r2
    mov.b @r5+,r0
    extu.b r0,r0
    or r0,r2
    dt r6
    bf decode_address
    cmp/eq r2,r8
    bf fatal
    mov.b @(6,r1),r0
    cmp/eq #2,r0
    bf fatal
    mov.b @(7,r1),r0
    tst r0,r0
    bf fatal
    mov #1,r11
    bsr tx_frame
    nop
    mov.l .Lblock,r0
    add r0,r8
    mov.l .Lrom_end,r0
    cmp/eq r0,r8
    bt pass_done
    bra packet_start
    nop
pass_done:
    mov #0,r8
    add #1,r9
    mov r9,r0
    cmp/eq #2,r0
    bt complete
    bra packet_start
    nop
complete:
    bsr check_guards
    nop
    mov.l .Lsci,r1
    mov.l .Ltx_budget,r3
tx_drain:
    mov.b @(4,r1),r0
    tst #4,r0
    bf tx_drained
    dt r3
    bf tx_drain
    bra fatal
    nop
tx_drained:
    mov #0,r0
    mov.b r0,@(2,r1)
halt_complete:
    bra halt_complete
    nop

fatal:
    mov.l .Lsci,r1
    mov #0,r0
    mov.b r0,@(2,r1)
halt_fail:
    bra halt_fail
    nop

check_guards:
    mov.l .Lguard_value,r0
    mov.l .Lguard_low,r1
    mov.l @r1,r2
    cmp/eq r0,r2
    bf fatal
    mov.l .Lguard_high,r1
    mov.l @r1,r2
    cmp/eq r0,r2
    bf fatal
    rts
    nop

/* RX leaf: returns byte in r0; clobbers only r1..r3 and SR.T. */
rx_byte:
    mov.l .Lsci,r1
rx_poll:
    mov.b @(4,r1),r0
    mov r0,r2
    tst #0x38,r0
    bf fatal
    tst #0x40,r0
    bt rx_poll
    mov.b @(5,r1),r0
    extu.b r0,r3
    mov r2,r0
    and #0xbf,r0
    mov.b r0,@(4,r1)
    rts
    mov r3,r0

/* TX leaf: argument r4; preserves r4..r14, adds byte to r7. */
tx_byte:
    mov.l .Lsci,r1
    mov.l .Ltx_budget,r3
tx_poll:
    mov.b @(4,r1),r0
    tst #0x80,r0
    bf tx_ready
    dt r3
    bf tx_poll
    bra fatal
    nop
tx_ready:
    mov r4,r0
    mov.b r0,@(3,r1)
    mov.b @(4,r1),r0
    and #0x7f,r0
    mov.b r0,@(4,r1)
    extu.b r4,r0
    add r0,r7
    rts
    nop

/* r11 selects fixed identity or fixed raw block. No caller supplied range. */
tx_frame:
    sts pr,r14
    mov #0,r7
    mov #15,r6
    tst r11,r11
    bt tx_length_ready
    mov.l .Lraw_length,r6
tx_length_ready:
    mov #0xbe,r4
    bsr tx_byte
    nop
    mov #0xef,r4
    bsr tx_byte
    nop
    mov r6,r4
    shlr8 r4
    bsr tx_byte
    nop
    mov r6,r4
    bsr tx_byte
    nop
    tst r11,r11
    bf tx_raw
    mov.l .Lidentity,r5
    bra tx_data
    nop
tx_raw:
    mov #0x83,r4
    bsr tx_byte
    nop
    mov r9,r4
    bsr tx_byte
    nop
    mov r8,r13
    mov #4,r6
tx_address:
    mov r13,r4
    shlr16 r4
    shlr8 r4
    bsr tx_byte
    nop
    shll8 r13
    dt r6
    bf tx_address
    mov r8,r5
    mov.l .Lblock,r6
tx_data:
    mov.b @r5+,r4
    bsr tx_byte
    nop
    dt r6
    bf tx_data
    mov r7,r4
    bsr tx_byte
    nop
    lds r14,pr
    rts
    nop

/* No attempt to resume the overwritten OEM runtime. */
    .global exception_handler
exception_handler:
    mov.l .Lstack,r15
    mov.l .Lsci,r1
    mov #0,r0
    mov.b r0,@(2,r1)
halt_exception:
    bra halt_exception
    nop
    .global code_end
code_end:

    /* Same assembler section is required for SH PC-relative relocations. */
    .balign 4
    .global const_pool_start
const_pool_start:
.Lstack:       .long stack_top
.Lvectors:     .long vector_table
.Ldmaor:       .long 0xffffecb0
.Lwtcsr:       .long 0xffffec10
.Lramer:       .long 0xffffec26
.Lfmats:       .long 0xffffe805
.Lwork_start:  .long work_start
.Lwork_end:    .long work_end
.Lguard_value: .long 0x6b31b4c2
.Lguard_low:   .long guard_low
.Lguard_high:  .long guard_high
.Lsci:         .long 0xfffff010
.Lpccr:        .long 0xfffff73c
.Lrx:          .long rx_buffer
.Lrom_end:     .long 0x00100000
.Lidentity:    .long identity_body
.Ltx_budget:   .long 65536
.Lwdt_off:     .long 0xa518
.Lpccr_mask:   .long 0x0155
.Lsettle_count:.long 2048
.Lblock:       .long 512
.Lraw_length:  .long 518
identity_body:
    .byte 0x81
    .asciz "A2WC511R-RK01"
    .balign 4

    .section .vectors,"a"
    .global vector_table
vector_table:
    .rept 256
    .long exception_handler
    .endr

    .section .integrity,"a"
    .global upload_checksum_word
upload_checksum_word:
    .long loader_checksum /* link sets this non-executable word to sum5AA5 */

    .section .bss,"aw",@nobits
    .balign 4
    .global work_start, work_end, rx_buffer, guard_low, guard_high, stack_low, stack_top
work_start:
rx_buffer:
    .space 8
guard_low:
    .space 4
stack_low:
    .space 16
stack_top:
guard_high:
    .space 4
work_end:
