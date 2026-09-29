	.file	"Bindings.c"
	.text
	.section	.m0.code,"ax",@progbits
	.align 2
	.global	_m0_sample_hardware
	.type	_m0_sample_hardware, @function
_m0_sample_hardware:
	mov.l	r8,@-r15
	mov.l	r9,@-r15
	mov.l	r10,@-r15
	mov.l	.L6,r7
	sts.l	pr,@-r15
	mov.b	@r7,r1
	add	#-8,r15
	mov.l	.L7,r3
	extu.b	r1,r8
	mov.b	r1,@r15
	mov	r15,r2
	mov.b	@r3,r1
	add	#1,r2
	mov.b	r1,@r2
	extu.b	r1,r9
	mov.l	.L8,r2
	mov	r15,r6
	add	#2,r6
	mov.b	@r2,r1
	mov	r15,r10
	mov.b	r1,@r6
	extu.b	r1,r0
	mov.l	.L9,r1
	add	#3,r10
	mov.b	@r1,r6
	mov.b	r6,@r10
	extu.b	r6,r5
	mov.b	@r7,r7
	mov.b	@r3,r3
	extu.b	r7,r7
	mov.b	@r2,r2
	cmp/eq	r7,r8
	mov.b	@r1,r1
	extu.b	r3,r3
	extu.b	r2,r2
	bf.s	.L5
	extu.b	r1,r1
	cmp/eq	r3,r9
	bf.s	.L5
	cmp/eq	r2,r0
	bf.s	.L5
	cmp/eq	r1,r5
	mov	#-1,r1
	negc	r1,r1
	bra	.L2
	extu.b	r1,r1
.L5:
	mov	#1,r1
.L2:
	mov	r15,r2
	add	#5,r2
	mov.b	r1,@r2
	mov	#0,r1
	add	#-1,r2
	mov.b	r1,@r2
	add	#2,r2
	mov.b	r1,@r2
	add	#1,r2
	mov.b	r1,@r2
	mov.l	.L10,r1
	jsr	@r1
	mov	r15,r5
	add	#8,r15
	lds.l   @r15+,pr
	mov.l   @r15+,r10
	mov.l   @r15+,r9
	mov.l   @r15+,r8
	rts	
	nop
.L11:
	.align 2
.L6:
	.long	-45963
.L7:
	.long	-45939
.L8:
	.long	-45919
.L9:
	.long	-46000
.L10:
	.long	_m0_observe
	.size	_m0_sample_hardware, .-_m0_sample_hardware
	.ident	"GCC: (GNU) 4.7-GNUSH_v13.01"
