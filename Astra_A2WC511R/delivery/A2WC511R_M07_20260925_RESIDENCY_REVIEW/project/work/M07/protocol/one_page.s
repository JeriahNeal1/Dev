/* RESEARCH: exact raw-six request, native A8 producer, no new refill code.
 * Entry is OEM unknown-command484B0 after its command comparisons (T=0).
 * Preserve R1/R4/PR and every nonvolatile register. R2/R3 are overwritten by
 * the unchanged484BC continuation before use. No FPU or interrupt masking.
 */
    .section .m07,"ax"
    .align 2
    .global _m07_project_request
_m07_project_request:
    mov.l r1,@-r15
    mov.l r4,@-r15
    mov r13,r2
    mov.l .Lrequest,r3
    mov #6,r4
.Lcompare:
    mov.l @r2+,r0
    mov.l @r3+,r1
    cmp/eq r1,r0
    bf .Loriginal
    dt r4
    bf .Lcompare
    mov.l @r15+,r4
    mov.l @r15+,r1
    mov #7,r0
    mov.b r0,@r12
    mov #-4,r0
    mov.b r0,@r11
    mov.b @r14,r0
    or #0x10,r0
    mov.b r0,@r14
    bra .Lcommon
    clrt
.Loriginal:
    mov.l @r15+,r4
    mov.l @r15+,r1
    mov.b @(1,r14),r0
    or #1,r0
    mov.b r0,@(1,r14)
.Lcommon:
    mov.b @r14,r0
    and #0x7F,r0
    mov.b r0,@r14
    mov.l .Lreturn,r2
    jmp @r2
    nop
    .align 2
.Lrequest: .long .Lcanonical
.Lreturn: .long 0x000484BC
.Lcanonical:
    .long 0x8010F014,0xBE10FF4C,0x75FF4C8D
    .long 0xFF4CA1FF,0x4C50FF4B,0xC1FF4BC2
    .global _m07_payload_end
_m07_payload_end:
