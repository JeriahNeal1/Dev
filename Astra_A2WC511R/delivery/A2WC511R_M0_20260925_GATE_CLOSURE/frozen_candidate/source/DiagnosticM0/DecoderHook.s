/* GPL-3.0-or-later. A2WC511R 0x147AC decoder observer wrapper.
 * Linked in a non-flash harness or explicitly UNAPPROVED experimental artifact.
 * Original decoder is a stack-independent leaf; preserve its observable result.
 * No SR/FPU/GBR writes precede original execution. Integer-only C follows it. */
 .section .m0.code,"ax"
 .align 2
 .global _m0_decoder_hook
_m0_decoder_hook:
 sts.l pr,@-r15
 mov.l r0,@-r15
 mov.l .Loriginal,r0
 jsr @r0
 mov.l @r15+,r0
 /* OEM result now exists. Save every GPR except SP, plus SR and MAC state. */
 mov.l r0,@-r15
 mov.l r1,@-r15
 mov.l r2,@-r15
 mov.l r3,@-r15
 mov.l r4,@-r15
 mov.l r5,@-r15
 mov.l r6,@-r15
 mov.l r7,@-r15
 mov.l r8,@-r15
 mov.l r9,@-r15
 mov.l r10,@-r15
 mov.l r11,@-r15
 mov.l r12,@-r15
 mov.l r13,@-r15
 mov.l r14,@-r15
 stc.l sr,@-r15
 sts.l mach,@-r15
 sts.l macl,@-r15
 mov.l .Lstate,r4
 mov.l .Lsample,r0
 jsr @r0
 nop
 lds.l @r15+,macl
 lds.l @r15+,mach
 ldc.l @r15+,sr
 mov.l @r15+,r14
 mov.l @r15+,r13
 mov.l @r15+,r12
 mov.l @r15+,r11
 mov.l @r15+,r10
 mov.l @r15+,r9
 mov.l @r15+,r8
 mov.l @r15+,r7
 mov.l @r15+,r6
 mov.l @r15+,r5
 mov.l @r15+,r4
 mov.l @r15+,r3
 mov.l @r15+,r2
 mov.l @r15+,r1
 mov.l @r15+,r0
 lds.l @r15+,pr
 rts
 nop
 .align 2
.Loriginal: .long 0x000147AC
.Lstate: .long _m0_state
.Lsample: .long _m0_sample_hardware
