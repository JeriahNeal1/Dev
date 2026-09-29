! M0.7 experimental replacement for exact1466E function's1473C switch tail.
! Original1473A mov#15,r0 remains byte-identical before this aligned entry.
! All GPR outputs and SR.T match original for every low nibble; no new stack.
.section .replacement,"ax"
.global replacement_start, replacement_end
replacement_start:
    mov.w .Lhigh,r7
    and r5,r0
    mov #8,r3
    cmp/hs r0,r3
    bt .Ltranslate
    cmp/eq #15,r0
.Ltranslate:
    mov.l .Ltable_address,r4
    mov.b @(r0,r4),r4
    extu.b r4,r4
    mov.l .Ldestination,r3
    rts
    mov.b r4,@r3
    .align 2
.Ltable_address:
    .long .Ltable
.Ldestination:
    .long 0xFFFF4BC0
.Lhigh:
    .word 128
.Ltable:
    .byte 0,1,2,4,8,16,32,64,128,128,128,128,128,128,128,15
replacement_end:
