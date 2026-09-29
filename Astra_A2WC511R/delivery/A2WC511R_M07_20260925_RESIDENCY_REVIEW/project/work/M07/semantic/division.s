! M0.7 experimental semantic compression of OEM signed divide4260.
! R2/R3 save locations preserved; one additional private R4 stack slot.
! The six-instruction loop restores DIV1's T via MOVT/SHAR, without LDC.
.section .replacement,"ax"
.global replacement_start, replacement_end
replacement_start:
    tst r0,r0
    mov.l r2,@-r15
    bt .Lzero
    mov.l r3,@-r15
    mov.l r4,@-r15
    mov #0,r2
    div0s r2,r1
    subc r3,r3
    subc r2,r1
    div0s r0,r3
    mov #32,r2
.Lloop:
    rotcl r1
    div1 r0,r3
    movt r4
    dt r2
    bf/s .Lloop
    shar r4
    rotcl r1
    addc r2,r1
    mov r1,r0
    mov.l @r15+,r4
    mov.l @r15+,r3
    rts
    mov.l @r15+,r2
.Lzero:
    mov.l .Lerror_address,r1
    mov.l .Lerror_value,r2
    mov #0,r0
    mov.l r2,@r1
    rts
    mov.l @r15+,r2
    .align 2
.Lerror_address:
    .long 0xFFFF130C
.Lerror_value:
    .long 0x0000044E
replacement_end:
