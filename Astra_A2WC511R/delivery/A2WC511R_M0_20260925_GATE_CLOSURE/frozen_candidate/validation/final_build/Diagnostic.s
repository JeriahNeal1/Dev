	.file	"Diagnostic.c"
	.text
	.section	.m0.code,"ax",@progbits
	.align 2
	.global	_m0_decode
	.type	_m0_decode, @function
_m0_decode:
	extu.b	r4,r0
	mov	#7,r1
	cmp/hi	r1,r0
	bf.s	.L2
	extu.b	r5,r5
	cmp/eq	#8,r0
	bf.s	.L3
	nop
	rts	
	mov	#0,r0
.L3:
	mov	r5,r0
.L2:
	rts	
	nop
	.size	_m0_decode, .-_m0_decode
	.align 2
	.global	_m0_reasons
	.type	_m0_reasons, @function
_m0_reasons:
	mov	r4,r1
	add	#1,r1
	mov.b	@r1,r1
	extu.b	r1,r1
	mov	r1,r0
	cmp/eq	#17,r0
	bf.s	.L15
	mov	r4,r2
	mov.w	.L26,r7
	bra	.L32
	add	#2,r2
.L15:
	mov.w	.L27,r7
	add	#2,r2
.L32:
	mov.b	@r2,r2
	mov	r2,r0
	cmp/eq	#1,r0
	bt.s	.L6
	mov	#2,r2
	or	r2,r7
.L6:
	mov	r4,r2
	add	#3,r2
	mov.b	@r2,r2
	mov	r2,r0
	tst	#2,r0
	bf.s	.L31
	mov	r4,r2
	mov	#4,r2
	or	r2,r7
	mov	r4,r2
.L31:
	add	#4,r2
	mov.b	@r2,r2
	extu.b	r2,r2
	tst	r2,r2
	bf.s	.L8
	mov	r2,r0
	mov	#8,r3
	bra	.L9
	or	r3,r7
.L8:
	cmp/eq	#2,r0
	bf.s	.L10
	mov	r2,r0
	bra	.L25
	mov	#16,r2
.L10:
	cmp/eq	#1,r0
	bt.s	.L9
	mov	#64,r2
.L25:
	or	r2,r7
.L9:
	mov.b	@r4,r2
	extu.b	r2,r2
	cmp/eq	r1,r2
	bt.s	.L11
	mov	#32,r3
	or	r3,r7
.L11:
	mov	r1,r3
	shlr2	r3
	shlr2	r3
	mov	#8,r2
	cmp/hi	r2,r3
	bt.s	.L12
	mov	#15,r0
	and	r0,r1
	cmp/hi	r2,r1
	bf.s	.L13
	nop
.L12:
	mov.w	.L28,r1
	or	r1,r7
.L13:
	add	#5,r4
	mov.b	@r4,r1
	tst	r1,r1
	bt.s	.L14
	nop
	mov.w	.L29,r1
	or	r1,r7
.L14:
	rts	
	mov	r7,r0
	.align 1
.L26:
	.short	512
.L27:
	.short	513
.L28:
	.short	128
.L29:
	.short	256
	.size	_m0_reasons, .-_m0_reasons
	.align 2
	.global	_m0_init
	.type	_m0_init, @function
_m0_init:
	mov.l	@(4,r4),r2
	mov.l	.L40,r1
	cmp/eq	r1,r2
	bf.s	.L34
	mov	#0,r1
	mov	r4,r1
	add	#30,r1
	mov.b	@r1,r0
	extu.b	r0,r0
	cmp/eq	#1,r0
	bf.s	.L37
	nop
	mov.l	@r4,r1
	mov	#-2,r2
	bra	.L34
	and	r2,r1
.L37:
	mov	#0,r1
.L34:
	mov	r1,r2
	add	#1,r2
	mov.l	r2,@r4
	mov	#4,r3
	mov	#0,r6
	mov	#28,r2
.L35:
	mov	r4,r7
	add	r3,r7
	mov.b	r6,@r7
	dt	r2
	bf.s	.L35
	add	#1,r3
	mov.l	.L40,r2
	mov	#1,r3
	add	#2,r1
	mov.l	r2,@(4,r4)
	mov.w	.L41,r2
	mov.l	r2,@(12,r4)
	mov	r4,r2
	add	#30,r2
	mov.b	r3,@r2
	mov.l	r1,@r4
	rts	
	nop
	.align 1
.L41:
	.short	520
.L42:
	.align 2
.L40:
	.long	1295008817
	.size	_m0_init, .-_m0_init
	.align 2
	.global	_m0_observe
	.type	_m0_observe, @function
_m0_observe:
	mov.l	r8,@-r15
	mov	r5,r2
	mov.l	r9,@-r15
	add	#1,r2
	mov.l	r10,@-r15
	mov	#15,r10
	mov.l	r11,@-r15
	mov	r4,r8
	mov.l	r12,@-r15
	mov	r5,r9
	sts.l	pr,@-r15
	mov.b	@r2,r0
	mov.l	@r4,r1
	extu.b	r0,r0
	mov.l	@(4,r4),r3
	mov	r0,r11
	mov.l	.L57,r2
	shlr2	r11
	shlr2	r11
	cmp/eq	r2,r3
	bf.s	.L44
	and	r0,r10
	mov	r4,r2
	add	#30,r2
	mov.b	@r2,r0
	extu.b	r0,r0
	cmp/eq	#1,r0
	bt.s	.L61
	mov	#-2,r12
.L44:
	mov.l	.L58,r1
	jsr	@r1
	mov	r8,r4
	mov.l	@r8,r1
	mov	#-2,r12
.L61:
	and	r1,r12
	mov	r12,r1
	add	#1,r1
	mov.l	r1,@r8
	mov.l	@(8,r8),r1
	tst	r1,r1
	bt.s	.L62
	mov	r9,r1
	mov	r8,r1
	mov	r9,r2
	add	#29,r1
	add	#1,r2
	mov.b	@r1,r1
	mov.b	@r2,r2
	extu.b	r1,r1
	extu.b	r2,r2
	cmp/eq	r1,r2
	bt.s	.L62
	mov	r9,r1
	mov.l	@(16,r8),r1
	add	#1,r1
	mov.l	r1,@(16,r8)
	mov	r9,r1
.L62:
	mov.b	@r1+,r3
	mov	r8,r2
	add	#20,r2
	mov.b	r3,@r2
	mov	#7,r3
	mov.b	@r1,r2
	mov	r8,r1
	add	#21,r1
	mov.b	r2,@r1
	mov	r9,r1
	add	#2,r1
	mov.b	@r1,r2
	mov	r8,r1
	add	#22,r1
	mov.b	r2,@r1
	mov	r9,r1
	add	#3,r1
	mov.b	@r1,r2
	mov	r8,r1
	add	#23,r1
	mov.b	r2,@r1
	add	#1,r1
	mov.b	r11,@r1
	add	#1,r1
	mov.b	r10,@r1
	add	#1,r1
	mov.b	@r1,r2
	cmp/hi	r3,r11
	bf.s	.L47
	extu.b	r2,r2
	mov	r11,r0
	cmp/eq	#8,r0
	bt.s	.L47
	mov	#0,r11
	mov	r2,r11
.L47:
	mov.b	r11,@r1
	mov	r8,r1
	add	#27,r1
	mov.b	@r1,r2
	mov	#7,r3
	cmp/hi	r3,r10
	bf.s	.L48
	extu.b	r2,r2
	mov	r10,r0
	cmp/eq	#8,r0
	bf.s	.L50
	nop
	bra	.L48
	mov	#0,r10
.L50:
	mov	r2,r10
.L48:
	mov.b	r10,@r1
	mov	r9,r1
	add	#4,r1
	mov.b	@r1,r2
	mov	r8,r1
	add	#28,r1
	mov.b	r2,@r1
	mov	r9,r1
	add	#5,r1
	mov.l	.L59,r0
	mov	r9,r4
	mov.b	@r1,r2
	mov	r8,r1
	add	#31,r1
	mov.b	r2,@r1
	jsr	@r0
	nop
	mov.l	r0,@(12,r8)
	add	#1,r9
	mov.b	@r9,r2
	mov	r8,r1
	add	#29,r1
	mov.b	r2,@r1
	add	#2,r12
	mov.l	@(8,r8),r1
	add	#1,r1
	mov.l	r1,@(8,r8)
	mov.l	r12,@r8
	lds.l   @r15+,pr
	mov.l   @r15+,r12
	mov.l   @r15+,r11
	mov.l   @r15+,r10
	mov.l   @r15+,r9
	mov.l   @r15+,r8
	rts	
	nop
.L60:
	.align 2
.L57:
	.long	1295008817
.L58:
	.long	_m0_init
.L59:
	.long	_m0_reasons
	.size	_m0_observe, .-_m0_observe
	.ident	"GCC: (GNU) 4.7-GNUSH_v13.01"
