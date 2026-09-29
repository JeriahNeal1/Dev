/* RESEARCH fragment entry inside a proven OEM dispatcher context only.
 * PR is already saved by4828C and restored at484C4; no use before that restore.
 * R2/R3 are dead until484BC/C0. Helper's T is a local match predicate.
 */
    .section .m07_main,"ax"
    .align 2
    .global _m07_project_request
_m07_project_request:
    mov.l r1,@-r15
    mov.l r4,@-r15
    mov.l .Lhelper,r3
    jsr @r3
    nop
    mov.l @r15+,r4
    mov.l @r15+,r1
    bf .Loriginal
    mov.b r0,@r12
    shar r0
    neg r0,r0
    add #-2,r0
    mov.b r0,@r11
    mov.b @r14,r0
    bra .Lclear
    or #0x10,r0
.Loriginal:
    mov.b @(1,r14),r0
    or #1,r0
    mov.b r0,@(1,r14)
    mov.b @r14,r0
.Lclear:
    and #0x7F,r0
    mov.b r0,@r14
    clrt
    mov.l .Lreturn,r2
    jmp @r2
    nop
    .align 2
.Lhelper: .long _m07_match
.Lreturn: .long 0x000484BC
    .global _m07_main_end
_m07_main_end:

    .section .m07_match,"ax"
    .align 2
    .global _m07_match
_m07_match:
    mov.b @(3,r13),r0
    cmp/eq #14,r0
    bf .Lsecond
    mov.l .Lpage0,r3
    bra .Lsetup
    mov #18,r4
.Lsecond:
    cmp/eq #8,r0
    bf .Lbad
    mov.l .Lpage1,r3
    mov #12,r4
.Lsetup:
    mov r13,r2
.Lcompare:
    mov.b @r2+,r0
    mov.b @r3+,r1
    cmp/eq r1,r0
    bf .Lbad
    dt r4
    bf .Lcompare
    rts
    mov.b @r3,r0
.Lbad:
    rts
    mov #0,r0
    .align 2
.Lpage0: .long .Lcanonical0
.Lpage1: .long .Lcanonical1
.Lcanonical0:
    .byte 0x80,0x10,0xF0,0x0E,0xBE,0x10
    .byte 0xFF,0x4C,0x75,0xFF,0x4C,0x8D,0xFF,0x4C,0xA1,0xFF,0x4C,0x50
    .byte 5
    .align 2
.Lcanonical1:
    .byte 0x80,0x10,0xF0,0x08,0xBE,0x11
    .byte 0xFF,0x4B,0xC1,0xFF,0x4B,0xC2
    .byte 3
    .align 2
    .global _m07_match_end
_m07_match_end:
