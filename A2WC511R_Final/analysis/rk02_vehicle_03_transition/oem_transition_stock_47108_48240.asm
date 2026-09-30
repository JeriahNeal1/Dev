
C:\Dev\SubaruRoms\OEM\A2WC511R.bin:     file format binary


Disassembly of section .data:

00047108 <.data+0x47108>:
   47108:	d4 3f       	mov.l	0x47208,r4	! ffff649c
   4710a:	60 40       	mov.b	@r4,r0
   4710c:	d2 40       	mov.l	0x47210,r2	! ffff6498
   4710e:	c9 fe       	and	#-2,r0
   47110:	d3 40       	mov.l	0x47214,r3	! ffff63e6
   47112:	24 00       	mov.b	r0,@r4
   47114:	d4 3d       	mov.l	0x4720c,r4	! ffff63e0
   47116:	84 41       	mov.b	@(1,r4),r0
   47118:	d1 3f       	mov.l	0x47218,r1	! ffff63e7
   4711a:	c9 df       	and	#-33,r0
   4711c:	80 41       	mov.b	r0,@(1,r4)
   4711e:	84 41       	mov.b	@(1,r4),r0
   47120:	c9 bf       	and	#-65,r0
   47122:	80 41       	mov.b	r0,@(1,r4)
   47124:	e4 00       	mov	#0,r4
   47126:	22 41       	mov.w	r4,@r2
   47128:	23 40       	mov.b	r4,@r3
   4712a:	21 40       	mov.b	r4,@r1
   4712c:	d2 3b       	mov.l	0x4721c,r2	! ffff63e8
   4712e:	00 0b       	rts	
   47130:	22 40       	mov.b	r4,@r2
   47132:	2f e6       	mov.l	r14,@-r15
   47134:	4f 22       	sts.l	pr,@-r15
   47136:	d4 3a       	mov.l	0x47220,r4	! ffff6408
   47138:	92 5f       	mov.w	0x471fa,r2	! 80
   4713a:	63 40       	mov.b	@r4,r3
   4713c:	63 3c       	extu.b	r3,r3
   4713e:	33 20       	cmp/eq	r2,r3
   47140:	8f 19       	bf.s	0x47176
   47142:	ee 00       	mov	#0,r14
   47144:	84 41       	mov.b	@(1,r4),r0
   47146:	60 0c       	extu.b	r0,r0
   47148:	88 10       	cmp/eq	#16,r0
   4714a:	8d 05       	bt.s	0x47158
   4714c:	00 09       	nop	
   4714e:	84 41       	mov.b	@(1,r4),r0
   47150:	60 0c       	extu.b	r0,r0
   47152:	88 12       	cmp/eq	#18,r0
   47154:	8f 0f       	bf.s	0x47176
   47156:	00 09       	nop	
   47158:	84 42       	mov.b	@(2,r4),r0
   4715a:	60 0c       	extu.b	r0,r0
   4715c:	93 4e       	mov.w	0x471fc,r3	! f0
   4715e:	30 30       	cmp/eq	r3,r0
   47160:	8f 09       	bf.s	0x47176
   47162:	00 09       	nop	
   47164:	b2 bc       	bsr	0x476e0
   47166:	00 09       	nop	
   47168:	60 0c       	extu.b	r0,r0
   4716a:	20 08       	tst	r0,r0
   4716c:	8f 03       	bf.s	0x47176
   4716e:	00 09       	nop	
   47170:	b0 f4       	bsr	0x4735c
   47172:	00 09       	nop	
   47174:	ee 01       	mov	#1,r14
   47176:	60 e3       	mov	r14,r0
   47178:	4f 26       	lds.l	@r15+,pr
   4717a:	00 0b       	rts	
   4717c:	6e f6       	mov.l	@r15+,r14
   4717e:	4f 22       	sts.l	pr,@-r15
   47180:	d0 22       	mov.l	0x4720c,r0	! ffff63e0
   47182:	60 00       	mov.b	@r0,r0
   47184:	c8 10       	tst	#16,r0
   47186:	00 29       	movt	r0
   47188:	70 ff       	add	#-1,r0
   4718a:	60 0b       	neg	r0,r0
   4718c:	88 01       	cmp/eq	#1,r0
   4718e:	8f 18       	bf.s	0x471c2
   47190:	00 09       	nop	
   47192:	d3 21       	mov.l	0x47218,r3	! ffff63e7
   47194:	91 33       	mov.w	0x471fe,r1	! bfe4
   47196:	62 30       	mov.b	@r3,r2
   47198:	21 20       	mov.b	r2,@r1
   4719a:	d2 22       	mov.l	0x47224,r2	! 47afc
   4719c:	42 0b       	jsr	@r2
   4719e:	00 09       	nop	
   471a0:	95 2e       	mov.w	0x47200,r5	! f014
   471a2:	e4 04       	mov	#4,r4
   471a4:	62 50       	mov.b	@r5,r2
   471a6:	62 2c       	extu.b	r2,r2
   471a8:	22 48       	tst	r4,r2
   471aa:	8d fb       	bt.s	0x471a4
   471ac:	00 09       	nop	
   471ae:	00 02       	stc	sr,r0
   471b0:	91 27       	mov.w	0x47202,r1	! ff0f
   471b2:	20 19       	and	r1,r0
   471b4:	cb f0       	or	#-16,r0
   471b6:	40 0e       	ldc	r0,sr
   471b8:	93 24       	mov.w	0x47204,r3	! 1004
   471ba:	64 32       	mov.l	@r3,r4
   471bc:	d2 1a       	mov.l	0x47228,r2	! 40
   471be:	42 2b       	jmp	@r2
   471c0:	4f 26       	lds.l	@r15+,pr
   471c2:	4f 26       	lds.l	@r15+,pr
   471c4:	00 0b       	rts	
   471c6:	00 09       	nop	
   471c8:	2f e6       	mov.l	r14,@-r15
   471ca:	e4 00       	mov	#0,r4
   471cc:	d0 0f       	mov.l	0x4720c,r0	! ffff63e0
   471ce:	4f 22       	sts.l	pr,@-r15
   471d0:	60 00       	mov.b	@r0,r0
   471d2:	c8 08       	tst	#8,r0
   471d4:	00 29       	movt	r0
   471d6:	70 ff       	add	#-1,r0
   471d8:	60 0b       	neg	r0,r0
   471da:	88 01       	cmp/eq	#1,r0
   471dc:	8f 09       	bf.s	0x471f2
   471de:	6e 43       	mov	r4,r14
   471e0:	d5 12       	mov.l	0x4722c,r5	! ffff63fb
   471e2:	e3 04       	mov	#4,r3
   471e4:	62 50       	mov.b	@r5,r2
   471e6:	62 2c       	extu.b	r2,r2
   471e8:	32 37       	cmp/gt	r3,r2
   471ea:	8f 02       	bf.s	0x471f2
   471ec:	ee 01       	mov	#1,r14
   471ee:	b0 4e       	bsr	0x4728e
   471f0:	25 40       	mov.b	r4,@r5
   471f2:	60 e3       	mov	r14,r0
   471f4:	4f 26       	lds.l	@r15+,pr
   471f6:	00 0b       	rts	
   471f8:	6e f6       	mov.l	@r15+,r14
   471fa:	00 80       	.word 0x0080
   471fc:	00 f0       	.word 0x00f0
   471fe:	bf e4       	bsr	0x471ca
   47200:	f0 14       	fcmp/eq	fr1,fr0
   47202:	ff 0f       	.word 0xff0f
   47204:	10 04       	mov.l	r0,@(16,r0)
   47206:	ff ff       	.word 0xffff
   47208:	ff ff       	.word 0xffff
   4720a:	64 9c       	extu.b	r9,r4
   4720c:	ff ff       	.word 0xffff
   4720e:	63 e0       	mov.b	@r14,r3
   47210:	ff ff       	.word 0xffff
   47212:	64 98       	swap.b	r9,r4
   47214:	ff ff       	.word 0xffff
   47216:	63 e6       	mov.l	@r14+,r3
   47218:	ff ff       	.word 0xffff
   4721a:	63 e7       	not	r14,r3
   4721c:	ff ff       	.word 0xffff
   4721e:	63 e8       	swap.b	r14,r3
   47220:	ff ff       	.word 0xffff
   47222:	64 08       	swap.b	r0,r4
   47224:	00 04       	mov.b	r0,@(r0,r0)
   47226:	7a fc       	add	#-4,r10
   47228:	00 00       	.word 0x0000
   4722a:	00 40       	.word 0x0040
   4722c:	ff ff       	.word 0xffff
   4722e:	63 fb       	neg	r15,r3
   47230:	d2 3d       	mov.l	0x47328,r2	! ffff63f0
   47232:	63 20       	mov.b	@r2,r3
   47234:	23 38       	tst	r3,r3
   47236:	8f 04       	bf.s	0x47242
   47238:	00 09       	nop	
   4723a:	94 74       	mov.w	0x47326,r4	! f012
   4723c:	60 40       	mov.b	@r4,r0
   4723e:	c9 5b       	and	#91,r0
   47240:	24 00       	mov.b	r0,@r4
   47242:	e4 00       	mov	#0,r4
   47244:	d3 39       	mov.l	0x4732c,r3	! ffff63fa
   47246:	23 40       	mov.b	r4,@r3
   47248:	d2 39       	mov.l	0x47330,r2	! ffff63fb
   4724a:	22 40       	mov.b	r4,@r2
   4724c:	d1 39       	mov.l	0x47334,r1	! ffff63fc
   4724e:	21 40       	mov.b	r4,@r1
   47250:	d3 39       	mov.l	0x47338,r3	! ffff6403
   47252:	23 40       	mov.b	r4,@r3
   47254:	d2 39       	mov.l	0x4733c,r2	! ffff6404
   47256:	22 40       	mov.b	r4,@r2
   47258:	d1 39       	mov.l	0x47340,r1	! ffff6402
   4725a:	21 40       	mov.b	r4,@r1
   4725c:	d3 39       	mov.l	0x47344,r3	! ffff63e5
   4725e:	23 40       	mov.b	r4,@r3
   47260:	d2 39       	mov.l	0x47348,r2	! ffff63e6
   47262:	22 40       	mov.b	r4,@r2
   47264:	d5 39       	mov.l	0x4734c,r5	! ffff649a
   47266:	60 50       	mov.b	@r5,r0
   47268:	d2 39       	mov.l	0x47350,r2	! ffff63fd
   4726a:	c9 bf       	and	#-65,r0
   4726c:	25 00       	mov.b	r0,@r5
   4726e:	60 50       	mov.b	@r5,r0
   47270:	c9 df       	and	#-33,r0
   47272:	25 00       	mov.b	r0,@r5
   47274:	60 50       	mov.b	@r5,r0
   47276:	c9 7f       	and	#127,r0
   47278:	25 00       	mov.b	r0,@r5
   4727a:	84 51       	mov.b	@(1,r5),r0
   4727c:	c9 fd       	and	#-3,r0
   4727e:	80 51       	mov.b	r0,@(1,r5)
   47280:	22 40       	mov.b	r4,@r2
   47282:	d3 34       	mov.l	0x47354,r3	! ffff63fe
   47284:	23 40       	mov.b	r4,@r3
   47286:	84 51       	mov.b	@(1,r5),r0
   47288:	c9 fb       	and	#-5,r0
   4728a:	00 0b       	rts	
   4728c:	80 51       	mov.b	r0,@(1,r5)
   4728e:	d4 32       	mov.l	0x47358,r4	! ffff63e0
   47290:	60 43       	mov	r4,r0
   47292:	60 00       	mov.b	@r0,r0
   47294:	c9 01       	and	#1,r0
   47296:	60 0d       	extu.w	r0,r0
   47298:	20 08       	tst	r0,r0
   4729a:	8f 2c       	bf.s	0x472f6
   4729c:	00 09       	nop	
   4729e:	60 43       	mov	r4,r0
   472a0:	60 00       	mov.b	@r0,r0
   472a2:	c8 02       	tst	#2,r0
   472a4:	00 29       	movt	r0
   472a6:	70 ff       	add	#-1,r0
   472a8:	60 0b       	neg	r0,r0
   472aa:	88 01       	cmp/eq	#1,r0
   472ac:	8f 02       	bf.s	0x472b4
   472ae:	00 09       	nop	
   472b0:	a2 95       	bra	0x477de
   472b2:	00 09       	nop	
   472b4:	60 43       	mov	r4,r0
   472b6:	60 00       	mov.b	@r0,r0
   472b8:	c8 04       	tst	#4,r0
   472ba:	00 29       	movt	r0
   472bc:	70 ff       	add	#-1,r0
   472be:	60 0b       	neg	r0,r0
   472c0:	88 01       	cmp/eq	#1,r0
   472c2:	8f 02       	bf.s	0x472ca
   472c4:	00 09       	nop	
   472c6:	a2 99       	bra	0x477fc
   472c8:	00 09       	nop	
   472ca:	60 43       	mov	r4,r0
   472cc:	60 00       	mov.b	@r0,r0
   472ce:	c8 08       	tst	#8,r0
   472d0:	00 29       	movt	r0
   472d2:	70 ff       	add	#-1,r0
   472d4:	60 0b       	neg	r0,r0
   472d6:	88 01       	cmp/eq	#1,r0
   472d8:	8f 02       	bf.s	0x472e0
   472da:	00 09       	nop	
   472dc:	a2 a5       	bra	0x4782a
   472de:	00 09       	nop	
   472e0:	60 43       	mov	r4,r0
   472e2:	60 00       	mov.b	@r0,r0
   472e4:	c8 10       	tst	#16,r0
   472e6:	00 29       	movt	r0
   472e8:	70 ff       	add	#-1,r0
   472ea:	60 0b       	neg	r0,r0
   472ec:	88 01       	cmp/eq	#1,r0
   472ee:	8f 04       	bf.s	0x472fa
   472f0:	00 09       	nop	
   472f2:	a3 0d       	bra	0x47910
   472f4:	00 09       	nop	
   472f6:	a3 0f       	bra	0x47918
   472f8:	00 09       	nop	
   472fa:	00 0b       	rts	
   472fc:	00 09       	nop	
   472fe:	d4 16       	mov.l	0x47358,r4	! ffff63e0
   47300:	60 40       	mov.b	@r4,r0
   47302:	c9 fd       	and	#-3,r0
   47304:	24 00       	mov.b	r0,@r4
   47306:	60 40       	mov.b	@r4,r0
   47308:	c9 fb       	and	#-5,r0
   4730a:	24 00       	mov.b	r0,@r4
   4730c:	60 40       	mov.b	@r4,r0
   4730e:	c9 f7       	and	#-9,r0
   47310:	24 00       	mov.b	r0,@r4
   47312:	60 40       	mov.b	@r4,r0
   47314:	c9 ef       	and	#-17,r0
   47316:	24 00       	mov.b	r0,@r4
   47318:	60 40       	mov.b	@r4,r0
   4731a:	c9 df       	and	#-33,r0
   4731c:	24 00       	mov.b	r0,@r4
   4731e:	60 40       	mov.b	@r4,r0
   47320:	c9 bf       	and	#-65,r0
   47322:	00 0b       	rts	
   47324:	24 00       	mov.b	r0,@r4
   47326:	f0 12       	fmul	fr1,fr0
   47328:	ff ff       	.word 0xffff
   4732a:	63 f0       	mov.b	@r15,r3
   4732c:	ff ff       	.word 0xffff
   4732e:	63 fa       	negc	r15,r3
   47330:	ff ff       	.word 0xffff
   47332:	63 fb       	neg	r15,r3
   47334:	ff ff       	.word 0xffff
   47336:	63 fc       	extu.b	r15,r3
   47338:	ff ff       	.word 0xffff
   4733a:	64 03       	mov	r0,r4
   4733c:	ff ff       	.word 0xffff
   4733e:	64 04       	mov.b	@r0+,r4
   47340:	ff ff       	.word 0xffff
   47342:	64 02       	mov.l	@r0,r4
   47344:	ff ff       	.word 0xffff
   47346:	63 e5       	mov.w	@r14+,r3
   47348:	ff ff       	.word 0xffff
   4734a:	63 e6       	mov.l	@r14+,r3
   4734c:	ff ff       	.word 0xffff
   4734e:	64 9a       	negc	r9,r4
   47350:	ff ff       	.word 0xffff
   47352:	63 fd       	extu.w	r15,r3
   47354:	ff ff       	.word 0xffff
   47356:	63 fe       	exts.b	r15,r3
   47358:	ff ff       	.word 0xffff
   4735a:	63 e0       	mov.b	@r14,r3
   4735c:	d4 45       	mov.l	0x47474,r4	! ffff6492
   4735e:	93 83       	mov.w	0x47468,r3	! 80
   47360:	90 83       	mov.w	0x4746a,r0	! f0
   47362:	24 30       	mov.b	r3,@r4
   47364:	80 41       	mov.b	r0,@(1,r4)
   47366:	d3 44       	mov.l	0x47478,r3	! ffff63e5
   47368:	d2 44       	mov.l	0x4747c,r2	! ffff6405
   4736a:	60 30       	mov.b	@r3,r0
   4736c:	d1 44       	mov.l	0x47480,r1	! ffff6401
   4736e:	80 42       	mov.b	r0,@(2,r4)
   47370:	60 20       	mov.b	@r2,r0
   47372:	80 43       	mov.b	r0,@(3,r4)
   47374:	60 10       	mov.b	@r1,r0
   47376:	80 44       	mov.b	r0,@(4,r4)
   47378:	d0 42       	mov.l	0x47484,r0	! ffff63e0
   4737a:	60 00       	mov.b	@r0,r0
   4737c:	c9 01       	and	#1,r0
   4737e:	88 01       	cmp/eq	#1,r0
   47380:	8f 04       	bf.s	0x4738c
   47382:	00 09       	nop	
   47384:	d2 40       	mov.l	0x47488,r2	! ffff63e2
   47386:	d3 41       	mov.l	0x4748c,r3	! ffff640c
   47388:	61 30       	mov.b	@r3,r1
   4738a:	22 10       	mov.b	r1,@r2
   4738c:	95 6e       	mov.w	0x4746c,r5	! f012
   4738e:	60 50       	mov.b	@r5,r0
   47390:	c9 5b       	and	#91,r0
   47392:	cb 20       	or	#32,r0
   47394:	25 00       	mov.b	r0,@r5
   47396:	65 43       	mov	r4,r5
   47398:	d2 3d       	mov.l	0x47490,r2	! ffff63fc
   4739a:	63 50       	mov.b	@r5,r3
   4739c:	d0 3d       	mov.l	0x47494,r0	! ffff63f9
   4739e:	22 30       	mov.b	r3,@r2
   473a0:	61 50       	mov.b	@r5,r1
   473a2:	20 10       	mov.b	r1,@r0
   473a4:	d4 3c       	mov.l	0x47498,r4	! ffff63fa
   473a6:	63 40       	mov.b	@r4,r3
   473a8:	73 01       	add	#1,r3
   473aa:	24 30       	mov.b	r3,@r4
   473ac:	d4 3b       	mov.l	0x4749c,r4	! ffff63fb
   473ae:	61 40       	mov.b	@r4,r1
   473b0:	71 01       	add	#1,r1
   473b2:	24 10       	mov.b	r1,@r4
   473b4:	d4 3a       	mov.l	0x474a0,r4	! ffff649a
   473b6:	60 40       	mov.b	@r4,r0
   473b8:	cb 40       	or	#64,r0
   473ba:	24 00       	mov.b	r0,@r4
   473bc:	60 40       	mov.b	@r4,r0
   473be:	cb 20       	or	#32,r0
   473c0:	00 0b       	rts	
   473c2:	24 00       	mov.b	r0,@r4
   473c4:	d7 2e       	mov.l	0x47480,r7	! ffff6401
   473c6:	e4 01       	mov	#1,r4
   473c8:	d5 2c       	mov.l	0x4747c,r5	! ffff6405
   473ca:	d0 36       	mov.l	0x474a4,r0	! ffff640b
   473cc:	60 00       	mov.b	@r0,r0
   473ce:	60 0c       	extu.b	r0,r0
   473d0:	88 01       	cmp/eq	#1,r0
   473d2:	8d 07       	bt.s	0x473e4
   473d4:	e6 03       	mov	#3,r6
   473d6:	e2 7f       	mov	#127,r2
   473d8:	d3 33       	mov.l	0x474a8,r3	! ffff63e3
   473da:	25 60       	mov.b	r6,@r5
   473dc:	27 20       	mov.b	r2,@r7
   473de:	e2 10       	mov	#16,r2
   473e0:	a0 04       	bra	0x473ec
   473e2:	23 20       	mov.b	r2,@r3
   473e4:	25 60       	mov.b	r6,@r5
   473e6:	e4 00       	mov	#0,r4
   473e8:	93 41       	mov.w	0x4746e,r3	! c1
   473ea:	27 30       	mov.b	r3,@r7
   473ec:	00 0b       	rts	
   473ee:	60 43       	mov	r4,r0
   473f0:	d7 22       	mov.l	0x4747c,r7	! ffff6405
   473f2:	d6 23       	mov.l	0x47480,r6	! ffff6401
   473f4:	d4 2d       	mov.l	0x474ac,r4	! ffff6408
   473f6:	84 43       	mov.b	@(3,r4),r0
   473f8:	60 0c       	extu.b	r0,r0
   473fa:	88 02       	cmp/eq	#2,r0
   473fc:	8f 0d       	bf.s	0x4741a
   473fe:	e5 01       	mov	#1,r5
   47400:	d0 2b       	mov.l	0x474b0,r0	! ffff63e1
   47402:	60 00       	mov.b	@r0,r0
   47404:	c8 20       	tst	#32,r0
   47406:	00 29       	movt	r0
   47408:	70 ff       	add	#-1,r0
   4740a:	60 0b       	neg	r0,r0
   4740c:	88 01       	cmp/eq	#1,r0
   4740e:	8f 04       	bf.s	0x4741a
   47410:	00 09       	nop	
   47412:	84 45       	mov.b	@(5,r4),r0
   47414:	20 08       	tst	r0,r0
   47416:	8d 08       	bt.s	0x4742a
   47418:	00 09       	nop	
   4741a:	e2 03       	mov	#3,r2
   4741c:	27 20       	mov.b	r2,@r7
   4741e:	e3 7f       	mov	#127,r3
   47420:	d2 21       	mov.l	0x474a8,r2	! ffff63e3
   47422:	26 30       	mov.b	r3,@r6
   47424:	e3 10       	mov	#16,r3
   47426:	a0 05       	bra	0x47434
   47428:	22 30       	mov.b	r3,@r2
   4742a:	e2 07       	mov	#7,r2
   4742c:	93 20       	mov.w	0x47470,r3	! c3
   4742e:	e5 00       	mov	#0,r5
   47430:	27 20       	mov.b	r2,@r7
   47432:	26 30       	mov.b	r3,@r6
   47434:	00 0b       	rts	
   47436:	60 53       	mov	r5,r0
   47438:	2f e6       	mov.l	r14,@-r15
   4743a:	2f d6       	mov.l	r13,@-r15
   4743c:	2f c6       	mov.l	r12,@-r15
   4743e:	2f b6       	mov.l	r11,@-r15
   47440:	2f a6       	mov.l	r10,@-r15
   47442:	2f 96       	mov.l	r9,@-r15
   47444:	2f 86       	mov.l	r8,@-r15
   47446:	e8 01       	mov	#1,r8
   47448:	da 17       	mov.l	0x474a8,r10	! ffff63e3
   4744a:	4f 22       	sts.l	pr,@-r15
   4744c:	dd 0c       	mov.l	0x47480,r13	! ffff6401
   4744e:	de 0b       	mov.l	0x4747c,r14	! ffff6405
   47450:	d2 18       	mov.l	0x474b4,r2	! ffff6498
   47452:	63 21       	mov.w	@r2,r3
   47454:	63 3d       	extu.w	r3,r3
   47456:	43 15       	cmp/pl	r3
   47458:	8f 2e       	bf.s	0x474b8
   4745a:	eb 03       	mov	#3,r11
   4745c:	2e b0       	mov.b	r11,@r14
   4745e:	e1 7f       	mov	#127,r1
   47460:	2d 10       	mov.b	r1,@r13
   47462:	e3 37       	mov	#55,r3
   47464:	a0 d3       	bra	0x4760e
   47466:	2a 30       	mov.b	r3,@r10
   47468:	00 80       	.word 0x0080
   4746a:	00 f0       	.word 0x00f0
   4746c:	f0 12       	fmul	fr1,fr0
   4746e:	00 c1       	.word 0x00c1
   47470:	00 c3       	.word 0x00c3
   47472:	ff ff       	.word 0xffff
   47474:	ff ff       	.word 0xffff
   47476:	64 92       	mov.l	@r9,r4
   47478:	ff ff       	.word 0xffff
   4747a:	63 e5       	mov.w	@r14+,r3
   4747c:	ff ff       	.word 0xffff
   4747e:	64 05       	mov.w	@r0+,r4
   47480:	ff ff       	.word 0xffff
   47482:	64 01       	mov.w	@r0,r4
   47484:	ff ff       	.word 0xffff
   47486:	63 e0       	mov.b	@r14,r3
   47488:	ff ff       	.word 0xffff
   4748a:	63 e2       	mov.l	@r14,r3
   4748c:	ff ff       	.word 0xffff
   4748e:	64 0c       	extu.b	r0,r4
   47490:	ff ff       	.word 0xffff
   47492:	63 fc       	extu.b	r15,r3
   47494:	ff ff       	.word 0xffff
   47496:	63 f9       	swap.w	r15,r3
   47498:	ff ff       	.word 0xffff
   4749a:	63 fa       	negc	r15,r3
   4749c:	ff ff       	.word 0xffff
   4749e:	63 fb       	neg	r15,r3
   474a0:	ff ff       	.word 0xffff
   474a2:	64 9a       	negc	r9,r4
   474a4:	ff ff       	.word 0xffff
   474a6:	64 0b       	neg	r0,r4
   474a8:	ff ff       	.word 0xffff
   474aa:	63 e3       	mov	r14,r3
   474ac:	ff ff       	.word 0xffff
   474ae:	64 08       	swap.b	r0,r4
   474b0:	ff ff       	.word 0xffff
   474b2:	63 e1       	mov.w	@r14,r3
   474b4:	ff ff       	.word 0xffff
   474b6:	64 98       	swap.b	r9,r4
   474b8:	d9 3e       	mov.l	0x475b4,r9	! ffff63e0
   474ba:	60 93       	mov	r9,r0
   474bc:	84 01       	mov.b	@(1,r0),r0
   474be:	c8 40       	tst	#64,r0
   474c0:	06 29       	movt	r6
   474c2:	76 ff       	add	#-1,r6
   474c4:	66 6b       	neg	r6,r6
   474c6:	60 6d       	extu.w	r6,r0
   474c8:	88 01       	cmp/eq	#1,r0
   474ca:	8f 0c       	bf.s	0x474e6
   474cc:	e5 10       	mov	#16,r5
   474ce:	d0 3a       	mov.l	0x475b8,r0	! ffff640b
   474d0:	60 00       	mov.b	@r0,r0
   474d2:	60 0c       	extu.b	r0,r0
   474d4:	88 02       	cmp/eq	#2,r0
   474d6:	8d 06       	bt.s	0x474e6
   474d8:	00 09       	nop	
   474da:	d0 37       	mov.l	0x475b8,r0	! ffff640b
   474dc:	60 00       	mov.b	@r0,r0
   474de:	60 0c       	extu.b	r0,r0
   474e0:	88 06       	cmp/eq	#6,r0
   474e2:	8f 41       	bf.s	0x47568
   474e4:	00 09       	nop	
   474e6:	e7 06       	mov	#6,r7
   474e8:	d0 34       	mov.l	0x475bc,r0	! ffff649c
   474ea:	60 00       	mov.b	@r0,r0
   474ec:	c9 01       	and	#1,r0
   474ee:	88 01       	cmp/eq	#1,r0
   474f0:	8f 0c       	bf.s	0x4750c
   474f2:	ec 00       	mov	#0,r12
   474f4:	66 6d       	extu.w	r6,r6
   474f6:	26 68       	tst	r6,r6
   474f8:	8f 02       	bf.s	0x47500
   474fa:	e2 67       	mov	#103,r2
   474fc:	a0 01       	bra	0x47502
   474fe:	2e 70       	mov.b	r7,@r14
   47500:	2e b0       	mov.b	r11,@r14
   47502:	68 c3       	mov	r12,r8
   47504:	d3 2e       	mov.l	0x475c0,r3	! ffff63e8
   47506:	2d 20       	mov.b	r2,@r13
   47508:	a0 81       	bra	0x4760e
   4750a:	23 80       	mov.b	r8,@r3
   4750c:	61 6d       	extu.w	r6,r1
   4750e:	21 18       	tst	r1,r1
   47510:	8f 06       	bf.s	0x47520
   47512:	00 09       	nop	
   47514:	d0 28       	mov.l	0x475b8,r0	! ffff640b
   47516:	60 00       	mov.b	@r0,r0
   47518:	60 0c       	extu.b	r0,r0
   4751a:	88 02       	cmp/eq	#2,r0
   4751c:	8f 24       	bf.s	0x47568
   4751e:	00 09       	nop	
   47520:	d4 28       	mov.l	0x475c4,r4	! ffff640d
   47522:	66 6d       	extu.w	r6,r6
   47524:	26 68       	tst	r6,r6
   47526:	8f 0f       	bf.s	0x47548
   47528:	00 09       	nop	
   4752a:	60 40       	mov.b	@r4,r0
   4752c:	60 0c       	extu.b	r0,r0
   4752e:	88 01       	cmp/eq	#1,r0
   47530:	8f 04       	bf.s	0x4753c
   47532:	00 09       	nop	
   47534:	2e 70       	mov.b	r7,@r14
   47536:	e2 67       	mov	#103,r2
   47538:	a0 11       	bra	0x4755e
   4753a:	2d 20       	mov.b	r2,@r13
   4753c:	2e b0       	mov.b	r11,@r14
   4753e:	e2 7f       	mov	#127,r2
   47540:	2d 20       	mov.b	r2,@r13
   47542:	88 02       	cmp/eq	#2,r0
   47544:	a0 63       	bra	0x4760e
   47546:	2a 50       	mov.b	r5,@r10
   47548:	60 40       	mov.b	@r4,r0
   4754a:	60 0c       	extu.b	r0,r0
   4754c:	88 01       	cmp/eq	#1,r0
   4754e:	8f 08       	bf.s	0x47562
   47550:	00 09       	nop	
   47552:	e2 67       	mov	#103,r2
   47554:	2e 70       	mov.b	r7,@r14
   47556:	2d 20       	mov.b	r2,@r13
   47558:	84 91       	mov.b	@(1,r9),r0
   4755a:	c9 bf       	and	#-65,r0
   4755c:	80 91       	mov.b	r0,@(1,r9)
   4755e:	a0 56       	bra	0x4760e
   47560:	68 c3       	mov	r12,r8
   47562:	88 02       	cmp/eq	#2,r0
   47564:	8d 05       	bt.s	0x47572
   47566:	00 09       	nop	
   47568:	2e b0       	mov.b	r11,@r14
   4756a:	e2 7f       	mov	#127,r2
   4756c:	2d 20       	mov.b	r2,@r13
   4756e:	a0 4e       	bra	0x4760e
   47570:	2a 50       	mov.b	r5,@r10
   47572:	b1 fd       	bsr	0x47970
   47574:	00 09       	nop	
   47576:	60 0c       	extu.b	r0,r0
   47578:	20 08       	tst	r0,r0
   4757a:	8d 29       	bt.s	0x475d0
   4757c:	00 09       	nop	
   4757e:	e2 7f       	mov	#127,r2
   47580:	2e b0       	mov.b	r11,@r14
   47582:	e3 35       	mov	#53,r3
   47584:	2d 20       	mov.b	r2,@r13
   47586:	2a 30       	mov.b	r3,@r10
   47588:	d2 0d       	mov.l	0x475c0,r2	! ffff63e8
   4758a:	e3 02       	mov	#2,r3
   4758c:	61 20       	mov.b	@r2,r1
   4758e:	71 01       	add	#1,r1
   47590:	22 10       	mov.b	r1,@r2
   47592:	61 1c       	extu.b	r1,r1
   47594:	31 33       	cmp/ge	r3,r1
   47596:	8f 3a       	bf.s	0x4760e
   47598:	00 09       	nop	
   4759a:	91 09       	mov.w	0x475b0,r1	! 2710
   4759c:	d2 0a       	mov.l	0x475c8,r2	! ffff6498
   4759e:	22 11       	mov.w	r1,@r2
   475a0:	d3 07       	mov.l	0x475c0,r3	! ffff63e8
   475a2:	23 c0       	mov.b	r12,@r3
   475a4:	d1 09       	mov.l	0x475cc,r1	! ffff63e6
   475a6:	21 c0       	mov.b	r12,@r1
   475a8:	84 91       	mov.b	@(1,r9),r0
   475aa:	c9 bf       	and	#-65,r0
   475ac:	a0 2f       	bra	0x4760e
   475ae:	80 91       	mov.b	r0,@(1,r9)
   475b0:	27 10       	mov.b	r1,@r7
   475b2:	ff ff       	.word 0xffff
   475b4:	ff ff       	.word 0xffff
   475b6:	63 e0       	mov.b	@r14,r3
   475b8:	ff ff       	.word 0xffff
   475ba:	64 0b       	neg	r0,r4
   475bc:	ff ff       	.word 0xffff
   475be:	64 9c       	extu.b	r9,r4
   475c0:	ff ff       	.word 0xffff
   475c2:	63 e8       	swap.b	r14,r3
   475c4:	ff ff       	.word 0xffff
   475c6:	64 0d       	extu.w	r0,r4
   475c8:	ff ff       	.word 0xffff
   475ca:	64 98       	swap.b	r9,r4
   475cc:	ff ff       	.word 0xffff
   475ce:	63 e6       	mov.l	@r14+,r3
   475d0:	60 93       	mov	r9,r0
   475d2:	84 01       	mov.b	@(1,r0),r0
   475d4:	c8 20       	tst	#32,r0
   475d6:	00 29       	movt	r0
   475d8:	70 ff       	add	#-1,r0
   475da:	60 0b       	neg	r0,r0
   475dc:	88 01       	cmp/eq	#1,r0
   475de:	8d 0c       	bt.s	0x475fa
   475e0:	00 09       	nop	
   475e2:	d2 37       	mov.l	0x476c0,r2	! 285dc
   475e4:	42 0b       	jsr	@r2
   475e6:	00 09       	nop	
   475e8:	84 91       	mov.b	@(1,r9),r0
   475ea:	e2 67       	mov	#103,r2
   475ec:	d3 35       	mov.l	0x476c4,r3	! ffff63e8
   475ee:	cb 80       	or	#-128,r0
   475f0:	80 91       	mov.b	r0,@(1,r9)
   475f2:	2e b0       	mov.b	r11,@r14
   475f4:	2d 20       	mov.b	r2,@r13
   475f6:	a0 09       	bra	0x4760c
   475f8:	23 c0       	mov.b	r12,@r3
   475fa:	e3 67       	mov	#103,r3
   475fc:	d2 31       	mov.l	0x476c4,r2	! ffff63e8
   475fe:	2e b0       	mov.b	r11,@r14
   47600:	2d 30       	mov.b	r3,@r13
   47602:	22 c0       	mov.b	r12,@r2
   47604:	d3 30       	mov.l	0x476c8,r3	! ffff649c
   47606:	60 30       	mov.b	@r3,r0
   47608:	cb 01       	or	#1,r0
   4760a:	23 00       	mov.b	r0,@r3
   4760c:	68 c3       	mov	r12,r8
   4760e:	60 83       	mov	r8,r0
   47610:	4f 26       	lds.l	@r15+,pr
   47612:	68 f6       	mov.l	@r15+,r8
   47614:	69 f6       	mov.l	@r15+,r9
   47616:	6a f6       	mov.l	@r15+,r10
   47618:	6b f6       	mov.l	@r15+,r11
   4761a:	6c f6       	mov.l	@r15+,r12
   4761c:	6d f6       	mov.l	@r15+,r13
   4761e:	00 0b       	rts	
   47620:	6e f6       	mov.l	@r15+,r14
   47622:	d0 29       	mov.l	0x476c8,r0	! ffff649c
   47624:	60 00       	mov.b	@r0,r0
   47626:	c9 01       	and	#1,r0
   47628:	88 01       	cmp/eq	#1,r0
   4762a:	8f 01       	bf.s	0x47630
   4762c:	e4 01       	mov	#1,r4
   4762e:	e4 00       	mov	#0,r4
   47630:	00 0b       	rts	
   47632:	60 43       	mov	r4,r0
   47634:	2f e6       	mov.l	r14,@-r15
   47636:	e5 10       	mov	#16,r5
   47638:	d0 27       	mov.l	0x476d8,r0	! ffff63e1
   4763a:	2f d6       	mov.l	r13,@-r15
   4763c:	2f c6       	mov.l	r12,@-r15
   4763e:	2f b6       	mov.l	r11,@-r15
   47640:	2f a6       	mov.l	r10,@-r15
   47642:	ea 7f       	mov	#127,r10
   47644:	dc 21       	mov.l	0x476cc,r12	! ffff63e2
   47646:	2f 96       	mov.l	r9,@-r15
   47648:	4f 22       	sts.l	pr,@-r15
   4764a:	e9 01       	mov	#1,r9
   4764c:	dd 20       	mov.l	0x476d0,r13	! ffff6401
   4764e:	de 21       	mov.l	0x476d4,r14	! ffff6405
   47650:	60 00       	mov.b	@r0,r0
   47652:	c8 20       	tst	#32,r0
   47654:	00 29       	movt	r0
   47656:	70 ff       	add	#-1,r0
   47658:	60 0b       	neg	r0,r0
   4765a:	88 01       	cmp/eq	#1,r0
   4765c:	8f 11       	bf.s	0x47682
   4765e:	eb 03       	mov	#3,r11
   47660:	d4 1e       	mov.l	0x476dc,r4	! ffff6408
   47662:	84 43       	mov.b	@(3,r4),r0
   47664:	60 0c       	extu.b	r0,r0
   47666:	88 03       	cmp/eq	#3,r0
   47668:	8f 0b       	bf.s	0x47682
   4766a:	00 09       	nop	
   4766c:	84 45       	mov.b	@(5,r4),r0
   4766e:	60 0c       	extu.b	r0,r0
   47670:	93 24       	mov.w	0x476bc,r3	! 85
   47672:	30 30       	cmp/eq	r3,r0
   47674:	8f 05       	bf.s	0x47682
   47676:	00 09       	nop	
   47678:	84 46       	mov.b	@(6,r4),r0
   4767a:	60 0c       	extu.b	r0,r0
   4767c:	88 02       	cmp/eq	#2,r0
   4767e:	8d 04       	bt.s	0x4768a
   47680:	00 09       	nop	
   47682:	2e b0       	mov.b	r11,@r14
   47684:	2d a0       	mov.b	r10,@r13
   47686:	a0 09       	bra	0x4769c
   47688:	60 53       	mov	r5,r0
   4768a:	bf ca       	bsr	0x47622
   4768c:	00 09       	nop	
   4768e:	60 0c       	extu.b	r0,r0
   47690:	20 08       	tst	r0,r0
   47692:	8d 05       	bt.s	0x476a0
   47694:	00 09       	nop	
   47696:	e0 22       	mov	#34,r0
   47698:	2e b0       	mov.b	r11,@r14
   4769a:	2d a0       	mov.b	r10,@r13
   4769c:	a0 05       	bra	0x476aa
   4769e:	80 c1       	mov.b	r0,@(1,r12)
   476a0:	e2 02       	mov	#2,r2
   476a2:	e3 50       	mov	#80,r3
   476a4:	2e 20       	mov.b	r2,@r14
   476a6:	e9 00       	mov	#0,r9
   476a8:	2d 30       	mov.b	r3,@r13
   476aa:	60 93       	mov	r9,r0
   476ac:	4f 26       	lds.l	@r15+,pr
   476ae:	69 f6       	mov.l	@r15+,r9
   476b0:	6a f6       	mov.l	@r15+,r10
   476b2:	6b f6       	mov.l	@r15+,r11
   476b4:	6c f6       	mov.l	@r15+,r12
   476b6:	6d f6       	mov.l	@r15+,r13
   476b8:	00 0b       	rts	
   476ba:	6e f6       	mov.l	@r15+,r14
   476bc:	00 85       	mov.w	r8,@(r0,r0)
   476be:	ff ff       	.word 0xffff
   476c0:	00 02       	stc	sr,r0
   476c2:	85 dc       	mov.w	@(24,r13),r0
   476c4:	ff ff       	.word 0xffff
   476c6:	63 e8       	swap.b	r14,r3
   476c8:	ff ff       	.word 0xffff
   476ca:	64 9c       	extu.b	r9,r4
   476cc:	ff ff       	.word 0xffff
   476ce:	63 e2       	mov.l	@r14,r3
   476d0:	ff ff       	.word 0xffff
   476d2:	64 01       	mov.w	@r0,r4
   476d4:	ff ff       	.word 0xffff
   476d6:	64 05       	mov.w	@r0+,r4
   476d8:	ff ff       	.word 0xffff
   476da:	63 e1       	mov.w	@r14,r3
   476dc:	ff ff       	.word 0xffff
   476de:	64 08       	swap.b	r0,r4
   476e0:	2f e6       	mov.l	r14,@-r15
   476e2:	2f d6       	mov.l	r13,@-r15
   476e4:	4f 22       	sts.l	pr,@-r15
   476e6:	be 0a       	bsr	0x472fe
   476e8:	ee 01       	mov	#1,r14
   476ea:	d4 2c       	mov.l	0x4779c,r4	! ffff63e0
   476ec:	d5 2c       	mov.l	0x477a0,r5	! ffff649a
   476ee:	60 40       	mov.b	@r4,r0
   476f0:	d3 2d       	mov.l	0x477a8,r3	! ffff63e5
   476f2:	c9 fe       	and	#-2,r0
   476f4:	91 50       	mov.w	0x47798,r1	! 81
   476f6:	24 00       	mov.b	r0,@r4
   476f8:	60 50       	mov.b	@r5,r0
   476fa:	c9 7f       	and	#127,r0
   476fc:	25 00       	mov.b	r0,@r5
   476fe:	d5 29       	mov.l	0x477a4,r5	! ffff6408
   47700:	84 51       	mov.b	@(1,r5),r0
   47702:	23 00       	mov.b	r0,@r3
   47704:	84 54       	mov.b	@(4,r5),r0
   47706:	60 0c       	extu.b	r0,r0
   47708:	30 10       	cmp/eq	r1,r0
   4770a:	8d 15       	bt.s	0x47738
   4770c:	ed 00       	mov	#0,r13
   4770e:	91 44       	mov.w	0x4779a,r1	! 83
   47710:	30 10       	cmp/eq	r1,r0
   47712:	8d 1d       	bt.s	0x47750
   47714:	00 09       	nop	
   47716:	88 27       	cmp/eq	#39,r0
   47718:	8d 26       	bt.s	0x47768
   4771a:	00 09       	nop	
   4771c:	88 10       	cmp/eq	#16,r0
   4771e:	8d 2f       	bt.s	0x47780
   47720:	00 09       	nop	
   47722:	88 34       	cmp/eq	#52,r0
   47724:	8d 42       	bt.s	0x477ac
   47726:	00 09       	nop	
   47728:	88 36       	cmp/eq	#54,r0
   4772a:	8d 3f       	bt.s	0x477ac
   4772c:	00 09       	nop	
   4772e:	88 31       	cmp/eq	#49,r0
   47730:	8d 3c       	bt.s	0x477ac
   47732:	00 09       	nop	
   47734:	a0 46       	bra	0x477c4
   47736:	00 09       	nop	
   47738:	60 40       	mov.b	@r4,r0
   4773a:	cb 02       	or	#2,r0
   4773c:	be 42       	bsr	0x473c4
   4773e:	24 00       	mov.b	r0,@r4
   47740:	60 0c       	extu.b	r0,r0
   47742:	20 08       	tst	r0,r0
   47744:	8d 3d       	bt.s	0x477c2
   47746:	00 09       	nop	
   47748:	b0 f3       	bsr	0x47932
   4774a:	00 09       	nop	
   4774c:	a0 39       	bra	0x477c2
   4774e:	00 09       	nop	
   47750:	60 40       	mov.b	@r4,r0
   47752:	cb 04       	or	#4,r0
   47754:	be 4c       	bsr	0x473f0
   47756:	24 00       	mov.b	r0,@r4
   47758:	60 0c       	extu.b	r0,r0
   4775a:	20 08       	tst	r0,r0
   4775c:	8d 31       	bt.s	0x477c2
   4775e:	00 09       	nop	
   47760:	b0 e7       	bsr	0x47932
   47762:	00 09       	nop	
   47764:	a0 2d       	bra	0x477c2
   47766:	00 09       	nop	
   47768:	60 40       	mov.b	@r4,r0
   4776a:	cb 08       	or	#8,r0
   4776c:	be 64       	bsr	0x47438
   4776e:	24 00       	mov.b	r0,@r4
   47770:	60 0c       	extu.b	r0,r0
   47772:	20 08       	tst	r0,r0
   47774:	8d 25       	bt.s	0x477c2
   47776:	00 09       	nop	
   47778:	b0 db       	bsr	0x47932
   4777a:	00 09       	nop	
   4777c:	a0 21       	bra	0x477c2
   4777e:	00 09       	nop	
   47780:	60 40       	mov.b	@r4,r0
   47782:	cb 10       	or	#16,r0
   47784:	bf 56       	bsr	0x47634
   47786:	24 00       	mov.b	r0,@r4
   47788:	60 0c       	extu.b	r0,r0
   4778a:	20 08       	tst	r0,r0
   4778c:	8d 19       	bt.s	0x477c2
   4778e:	00 09       	nop	
   47790:	b0 cf       	bsr	0x47932
   47792:	00 09       	nop	
   47794:	a0 15       	bra	0x477c2
   47796:	00 09       	nop	
   47798:	00 81       	.word 0x0081
   4779a:	00 83       	.word 0x0083
   4779c:	ff ff       	.word 0xffff
   4779e:	63 e0       	mov.b	@r14,r3
   477a0:	ff ff       	.word 0xffff
   477a2:	64 9a       	negc	r9,r4
   477a4:	ff ff       	.word 0xffff
   477a6:	64 08       	swap.b	r0,r4
   477a8:	ff ff       	.word 0xffff
   477aa:	63 e5       	mov.w	@r14+,r3
   477ac:	d2 4d       	mov.l	0x478e4,r2	! ffff6405
   477ae:	e0 7f       	mov	#127,r0
   477b0:	d3 4e       	mov.l	0x478ec,r3	! ffff63e3
   477b2:	e1 03       	mov	#3,r1
   477b4:	22 10       	mov.b	r1,@r2
   477b6:	e2 10       	mov	#16,r2
   477b8:	d1 4b       	mov.l	0x478e8,r1	! ffff6401
   477ba:	21 00       	mov.b	r0,@r1
   477bc:	23 20       	mov.b	r2,@r3
   477be:	b0 b8       	bsr	0x47932
   477c0:	00 09       	nop	
   477c2:	6e d3       	mov	r13,r14
   477c4:	63 ec       	extu.b	r14,r3
   477c6:	23 38       	tst	r3,r3
   477c8:	8f 05       	bf.s	0x477d6
   477ca:	60 e3       	mov	r14,r0
   477cc:	d2 45       	mov.l	0x478e4,r2	! ffff6405
   477ce:	61 20       	mov.b	@r2,r1
   477d0:	d3 47       	mov.l	0x478f0,r3	! ffff63ff
   477d2:	71 04       	add	#4,r1
   477d4:	23 10       	mov.b	r1,@r3
   477d6:	4f 26       	lds.l	@r15+,pr
   477d8:	6d f6       	mov.l	@r15+,r13
   477da:	00 0b       	rts	
   477dc:	6e f6       	mov.l	@r15+,r14
   477de:	d4 45       	mov.l	0x478f4,r4	! ffff6492
   477e0:	93 7d       	mov.w	0x478de,r3	! ef
   477e2:	24 30       	mov.b	r3,@r4
   477e4:	90 7c       	mov.w	0x478e0,r0	! 8f
   477e6:	80 41       	mov.b	r0,@(1,r4)
   477e8:	d3 43       	mov.l	0x478f8,r3	! ffff63e7
   477ea:	e4 00       	mov	#0,r4
   477ec:	d2 43       	mov.l	0x478fc,r2	! ffff63e6
   477ee:	23 40       	mov.b	r4,@r3
   477f0:	22 40       	mov.b	r4,@r2
   477f2:	d4 43       	mov.l	0x47900,r4	! ffff63e0
   477f4:	84 41       	mov.b	@(1,r4),r0
   477f6:	cb 20       	or	#32,r0
   477f8:	00 0b       	rts	
   477fa:	80 41       	mov.b	r0,@(1,r4)
   477fc:	97 71       	mov.w	0x478e2,r7	! ff
   477fe:	e5 00       	mov	#0,r5
   47800:	d4 3c       	mov.l	0x478f4,r4	! ffff6492
   47802:	e1 09       	mov	#9,r1
   47804:	d2 3f       	mov.l	0x47904,r2	! ffff63fa
   47806:	63 20       	mov.b	@r2,r3
   47808:	63 3c       	extu.b	r3,r3
   4780a:	33 13       	cmp/ge	r1,r3
   4780c:	8d 08       	bt.s	0x47820
   4780e:	66 43       	mov	r4,r6
   47810:	26 50       	mov.b	r5,@r6
   47812:	60 53       	mov	r5,r0
   47814:	80 41       	mov.b	r0,@(1,r4)
   47816:	60 73       	mov	r7,r0
   47818:	80 42       	mov.b	r0,@(2,r4)
   4781a:	60 53       	mov	r5,r0
   4781c:	00 0b       	rts	
   4781e:	80 43       	mov.b	r0,@(3,r4)
   47820:	26 70       	mov.b	r7,@r6
   47822:	60 53       	mov	r5,r0
   47824:	80 41       	mov.b	r0,@(1,r4)
   47826:	00 0b       	rts	
   47828:	00 09       	nop	
   4782a:	2f e6       	mov.l	r14,@-r15
   4782c:	2f d6       	mov.l	r13,@-r15
   4782e:	2f c6       	mov.l	r12,@-r15
   47830:	4f 22       	sts.l	pr,@-r15
   47832:	d5 35       	mov.l	0x47908,r5	! ffff649c
   47834:	dd 32       	mov.l	0x47900,r13	! ffff63e0
   47836:	de 2f       	mov.l	0x478f4,r14	! ffff6492
   47838:	60 d3       	mov	r13,r0
   4783a:	84 01       	mov.b	@(1,r0),r0
   4783c:	c8 40       	tst	#64,r0
   4783e:	00 29       	movt	r0
   47840:	70 ff       	add	#-1,r0
   47842:	60 0b       	neg	r0,r0
   47844:	88 01       	cmp/eq	#1,r0
   47846:	8d 25       	bt.s	0x47894
   47848:	64 e3       	mov	r14,r4
   4784a:	e2 01       	mov	#1,r2
   4784c:	24 20       	mov.b	r2,@r4
   4784e:	60 53       	mov	r5,r0
   47850:	60 00       	mov.b	@r0,r0
   47852:	c9 01       	and	#1,r0
   47854:	88 01       	cmp/eq	#1,r0
   47856:	8f 06       	bf.s	0x47866
   47858:	ec 00       	mov	#0,r12
   4785a:	60 c3       	mov	r12,r0
   4785c:	80 e1       	mov.b	r0,@(1,r14)
   4785e:	80 e2       	mov.b	r0,@(2,r14)
   47860:	80 e3       	mov.b	r0,@(3,r14)
   47862:	a0 11       	bra	0x47888
   47864:	80 e4       	mov.b	r0,@(4,r14)
   47866:	b0 9b       	bsr	0x479a0
   47868:	00 09       	nop	
   4786a:	64 03       	mov	r0,r4
   4786c:	40 29       	shlr16	r0
   4786e:	40 19       	shlr8	r0
   47870:	80 e1       	mov.b	r0,@(1,r14)
   47872:	60 43       	mov	r4,r0
   47874:	40 29       	shlr16	r0
   47876:	80 e2       	mov.b	r0,@(2,r14)
   47878:	60 43       	mov	r4,r0
   4787a:	40 19       	shlr8	r0
   4787c:	80 e3       	mov.b	r0,@(3,r14)
   4787e:	60 43       	mov	r4,r0
   47880:	80 e4       	mov.b	r0,@(4,r14)
   47882:	84 d1       	mov.b	@(1,r13),r0
   47884:	cb 40       	or	#64,r0
   47886:	80 d1       	mov.b	r0,@(1,r13)
   47888:	d2 20       	mov.l	0x4790c,r2	! ffff63e8
   4788a:	22 c0       	mov.b	r12,@r2
   4788c:	84 d1       	mov.b	@(1,r13),r0
   4788e:	c9 7f       	and	#127,r0
   47890:	a0 20       	bra	0x478d4
   47892:	80 d1       	mov.b	r0,@(1,r13)
   47894:	e7 34       	mov	#52,r7
   47896:	60 53       	mov	r5,r0
   47898:	60 00       	mov.b	@r0,r0
   4789a:	c9 01       	and	#1,r0
   4789c:	88 01       	cmp/eq	#1,r0
   4789e:	8f 0a       	bf.s	0x478b6
   478a0:	e6 02       	mov	#2,r6
   478a2:	60 73       	mov	r7,r0
   478a4:	24 60       	mov.b	r6,@r4
   478a6:	80 e1       	mov.b	r0,@(1,r14)
   478a8:	84 d1       	mov.b	@(1,r13),r0
   478aa:	c9 bf       	and	#-65,r0
   478ac:	80 d1       	mov.b	r0,@(1,r13)
   478ae:	60 50       	mov.b	@r5,r0
   478b0:	cb 01       	or	#1,r0
   478b2:	a0 0f       	bra	0x478d4
   478b4:	25 00       	mov.b	r0,@r5
   478b6:	60 d3       	mov	r13,r0
   478b8:	84 01       	mov.b	@(1,r0),r0
   478ba:	c8 80       	tst	#-128,r0
   478bc:	00 29       	movt	r0
   478be:	70 ff       	add	#-1,r0
   478c0:	60 0b       	neg	r0,r0
   478c2:	88 01       	cmp/eq	#1,r0
   478c4:	8f 06       	bf.s	0x478d4
   478c6:	00 09       	nop	
   478c8:	24 60       	mov.b	r6,@r4
   478ca:	60 73       	mov	r7,r0
   478cc:	80 e1       	mov.b	r0,@(1,r14)
   478ce:	84 d1       	mov.b	@(1,r13),r0
   478d0:	c9 bf       	and	#-65,r0
   478d2:	80 d1       	mov.b	r0,@(1,r13)
   478d4:	4f 26       	lds.l	@r15+,pr
   478d6:	6c f6       	mov.l	@r15+,r12
   478d8:	6d f6       	mov.l	@r15+,r13
   478da:	00 0b       	rts	
   478dc:	6e f6       	mov.l	@r15+,r14
   478de:	00 ef       	mac.l	@r14+,@r0+
   478e0:	00 8f       	mac.l	@r8+,@r0+
   478e2:	00 ff       	mac.l	@r15+,@r0+
   478e4:	ff ff       	.word 0xffff
   478e6:	64 05       	mov.w	@r0+,r4
   478e8:	ff ff       	.word 0xffff
   478ea:	64 01       	mov.w	@r0,r4
   478ec:	ff ff       	.word 0xffff
   478ee:	63 e3       	mov	r14,r3
   478f0:	ff ff       	.word 0xffff
   478f2:	63 ff       	exts.w	r15,r3
   478f4:	ff ff       	.word 0xffff
   478f6:	64 92       	mov.l	@r9,r4
   478f8:	ff ff       	.word 0xffff
   478fa:	63 e7       	not	r14,r3
   478fc:	ff ff       	.word 0xffff
   478fe:	63 e6       	mov.l	@r14+,r3
   47900:	ff ff       	.word 0xffff
   47902:	63 e0       	mov.b	@r14,r3
   47904:	ff ff       	.word 0xffff
   47906:	63 fa       	negc	r15,r3
   47908:	ff ff       	.word 0xffff
   4790a:	64 9c       	extu.b	r9,r4
   4790c:	ff ff       	.word 0xffff
   4790e:	63 e8       	swap.b	r14,r3
   47910:	d3 42       	mov.l	0x47a1c,r3	! ffff6492
   47912:	92 80       	mov.w	0x47a16,r2	! 85
   47914:	00 0b       	rts	
   47916:	23 20       	mov.b	r2,@r3
   47918:	4f 22       	sts.l	pr,@-r15
   4791a:	bc f0       	bsr	0x472fe
   4791c:	00 09       	nop	
   4791e:	d5 40       	mov.l	0x47a20,r5	! ffff63e2
   47920:	d4 3e       	mov.l	0x47a1c,r4	! ffff6492
   47922:	62 50       	mov.b	@r5,r2
   47924:	24 20       	mov.b	r2,@r4
   47926:	84 51       	mov.b	@(1,r5),r0
   47928:	80 41       	mov.b	r0,@(1,r4)
   4792a:	84 52       	mov.b	@(2,r5),r0
   4792c:	4f 26       	lds.l	@r15+,pr
   4792e:	00 0b       	rts	
   47930:	80 42       	mov.b	r0,@(2,r4)
   47932:	4f 22       	sts.l	pr,@-r15
   47934:	d4 3b       	mov.l	0x47a24,r4	! ffff63e6
   47936:	63 40       	mov.b	@r4,r3
   47938:	d5 3b       	mov.l	0x47a28,r5	! ffff63e7
   4793a:	73 01       	add	#1,r3
   4793c:	24 30       	mov.b	r3,@r4
   4793e:	62 50       	mov.b	@r5,r2
   47940:	72 01       	add	#1,r2
   47942:	25 20       	mov.b	r2,@r5
   47944:	63 40       	mov.b	@r4,r3
   47946:	e2 04       	mov	#4,r2
   47948:	63 3c       	extu.b	r3,r3
   4794a:	33 23       	cmp/ge	r2,r3
   4794c:	8d 06       	bt.s	0x4795c
   4794e:	00 09       	nop	
   47950:	61 50       	mov.b	@r5,r1
   47952:	e3 0b       	mov	#11,r3
   47954:	61 1c       	extu.b	r1,r1
   47956:	31 33       	cmp/ge	r3,r1
   47958:	8f 04       	bf.s	0x47964
   4795a:	00 09       	nop	
   4795c:	bc 68       	bsr	0x47230
   4795e:	00 09       	nop	
   47960:	bb d2       	bsr	0x47108
   47962:	00 09       	nop	
   47964:	d4 31       	mov.l	0x47a2c,r4	! ffff63e0
   47966:	60 40       	mov.b	@r4,r0
   47968:	4f 26       	lds.l	@r15+,pr
   4796a:	cb 01       	or	#1,r0
   4796c:	00 0b       	rts	
   4796e:	24 00       	mov.b	r0,@r4
   47970:	d5 2f       	mov.l	0x47a30,r5	! ffff6408
   47972:	84 56       	mov.b	@(6,r5),r0
   47974:	d2 2f       	mov.l	0x47a34,r2	! ffff63ec
   47976:	64 0c       	extu.b	r0,r4
   47978:	63 22       	mov.l	@r2,r3
   4797a:	44 28       	shll16	r4
   4797c:	84 57       	mov.b	@(7,r5),r0
   4797e:	44 18       	shll8	r4
   47980:	60 0c       	extu.b	r0,r0
   47982:	40 28       	shll16	r0
   47984:	34 0c       	add	r0,r4
   47986:	84 58       	mov.b	@(8,r5),r0
   47988:	60 0c       	extu.b	r0,r0
   4798a:	40 18       	shll8	r0
   4798c:	34 0c       	add	r0,r4
   4798e:	84 59       	mov.b	@(9,r5),r0
   47990:	60 0c       	extu.b	r0,r0
   47992:	34 0c       	add	r0,r4
   47994:	33 40       	cmp/eq	r4,r3
   47996:	8f 01       	bf.s	0x4799c
   47998:	e6 01       	mov	#1,r6
   4799a:	e6 00       	mov	#0,r6
   4799c:	00 0b       	rts	
   4799e:	60 63       	mov	r6,r0
   479a0:	2f e6       	mov.l	r14,@-r15
   479a2:	2f d6       	mov.l	r13,@-r15
   479a4:	2f c6       	mov.l	r12,@-r15
   479a6:	2f b6       	mov.l	r11,@-r15
   479a8:	2f a6       	mov.l	r10,@-r15
   479aa:	4f 22       	sts.l	pr,@-r15
   479ac:	93 34       	mov.w	0x47a18,r3	! f430
   479ae:	6e 32       	mov.l	@r3,r14
   479b0:	d2 20       	mov.l	0x47a34,r2	! ffff63ec
   479b2:	e4 00       	mov	#0,r4
   479b4:	dc 20       	mov.l	0x47a38,r12	! 47ad2
   479b6:	22 e2       	mov.l	r14,@r2
   479b8:	d0 20       	mov.l	0x47a3c,r0	! ffff63e1
   479ba:	60 00       	mov.b	@r0,r0
   479bc:	c8 20       	tst	#32,r0
   479be:	00 29       	movt	r0
   479c0:	70 ff       	add	#-1,r0
   479c2:	60 0b       	neg	r0,r0
   479c4:	88 01       	cmp/eq	#1,r0
   479c6:	8f 0c       	bf.s	0x479e2
   479c8:	ed 10       	mov	#16,r13
   479ca:	6a 43       	mov	r4,r10
   479cc:	db 1c       	mov.l	0x47a40,r11	! 4eaac
   479ce:	65 b5       	mov.w	@r11+,r5
   479d0:	4c 0b       	jsr	@r12
   479d2:	64 e3       	mov	r14,r4
   479d4:	7a 01       	add	#1,r10
   479d6:	62 ac       	extu.b	r10,r2
   479d8:	32 d3       	cmp/ge	r13,r2
   479da:	8f f8       	bf.s	0x479ce
   479dc:	6e 03       	mov	r0,r14
   479de:	a0 0a       	bra	0x479f6
   479e0:	00 09       	nop	
   479e2:	6a 43       	mov	r4,r10
   479e4:	db 17       	mov.l	0x47a44,r11	! 4eacc
   479e6:	65 b5       	mov.w	@r11+,r5
   479e8:	4c 0b       	jsr	@r12
   479ea:	64 e3       	mov	r14,r4
   479ec:	7a 01       	add	#1,r10
   479ee:	63 ac       	extu.b	r10,r3
   479f0:	33 d3       	cmp/ge	r13,r3
   479f2:	8f f8       	bf.s	0x479e6
   479f4:	6e 03       	mov	r0,r14
   479f6:	64 e3       	mov	r14,r4
   479f8:	d3 13       	mov.l	0x47a48,r3	! ffff0000
   479fa:	62 e3       	mov	r14,r2
   479fc:	4f 26       	lds.l	@r15+,pr
   479fe:	44 29       	shlr16	r4
   47a00:	6a f6       	mov.l	@r15+,r10
   47a02:	42 28       	shll16	r2
   47a04:	6b f6       	mov.l	@r15+,r11
   47a06:	64 4d       	extu.w	r4,r4
   47a08:	6c f6       	mov.l	@r15+,r12
   47a0a:	22 39       	and	r3,r2
   47a0c:	6d f6       	mov.l	@r15+,r13
   47a0e:	34 2c       	add	r2,r4
   47a10:	60 43       	mov	r4,r0
   47a12:	00 0b       	rts	
   47a14:	6e f6       	mov.l	@r15+,r14
   47a16:	00 85       	mov.w	r8,@(r0,r0)
   47a18:	f4 30       	fadd	fr3,fr4
   47a1a:	ff ff       	.word 0xffff
   47a1c:	ff ff       	.word 0xffff
   47a1e:	64 92       	mov.l	@r9,r4
   47a20:	ff ff       	.word 0xffff
   47a22:	63 e2       	mov.l	@r14,r3
   47a24:	ff ff       	.word 0xffff
   47a26:	63 e6       	mov.l	@r14+,r3
   47a28:	ff ff       	.word 0xffff
   47a2a:	63 e7       	not	r14,r3
   47a2c:	ff ff       	.word 0xffff
   47a2e:	63 e0       	mov.b	@r14,r3
   47a30:	ff ff       	.word 0xffff
   47a32:	64 08       	swap.b	r0,r4
   47a34:	ff ff       	.word 0xffff
   47a36:	63 ec       	extu.b	r14,r3
   47a38:	00 04       	mov.b	r0,@(r0,r0)
   47a3a:	7a d2       	add	#-46,r10
   47a3c:	ff ff       	.word 0xffff
   47a3e:	63 e1       	mov.w	@r14,r3
   47a40:	00 04       	mov.b	r0,@(r0,r0)
   47a42:	ea ac       	mov	#-84,r10
   47a44:	00 04       	mov.b	r0,@(r0,r0)
   47a46:	ea cc       	mov	#-52,r10
   47a48:	ff ff       	.word 0xffff
   47a4a:	00 00       	.word 0x0000
   47a4c:	d6 2a       	mov.l	0x47af8,r6	! 4eaec
   47a4e:	7f f4       	add	#-12,r15
   47a50:	24 5a       	xor	r5,r4
   47a52:	e5 1f       	mov	#31,r5
   47a54:	60 4c       	extu.b	r4,r0
   47a56:	20 59       	and	r5,r0
   47a58:	03 6c       	mov.b	@(r0,r6),r3
   47a5a:	67 4d       	extu.w	r4,r7
   47a5c:	63 3c       	extu.b	r3,r3
   47a5e:	47 09       	shlr2	r7
   47a60:	2f 31       	mov.w	r3,@r15
   47a62:	47 09       	shlr2	r7
   47a64:	60 7c       	extu.b	r7,r0
   47a66:	20 59       	and	r5,r0
   47a68:	00 6c       	mov.b	@(r0,r6),r0
   47a6a:	67 4d       	extu.w	r4,r7
   47a6c:	60 0c       	extu.b	r0,r0
   47a6e:	64 73       	mov	r7,r4
   47a70:	81 f2       	mov.w	r0,@(4,r15)
   47a72:	62 73       	mov	r7,r2
   47a74:	44 19       	shlr8	r4
   47a76:	60 4c       	extu.b	r4,r0
   47a78:	20 59       	and	r5,r0
   47a7a:	e4 01       	mov	#1,r4
   47a7c:	00 6c       	mov.b	@(r0,r6),r0
   47a7e:	42 19       	shlr8	r2
   47a80:	60 0c       	extu.b	r0,r0
   47a82:	24 79       	and	r7,r4
   47a84:	81 f4       	mov.w	r0,@(8,r15)
   47a86:	44 08       	shll2	r4
   47a88:	44 08       	shll2	r4
   47a8a:	42 09       	shlr2	r2
   47a8c:	42 09       	shlr2	r2
   47a8e:	34 2c       	add	r2,r4
   47a90:	60 4c       	extu.b	r4,r0
   47a92:	20 59       	and	r5,r0
   47a94:	02 6c       	mov.b	@(r0,r6),r2
   47a96:	64 2c       	extu.b	r2,r4
   47a98:	85 f4       	mov.w	@(8,r15),r0
   47a9a:	65 4d       	extu.w	r4,r5
   47a9c:	45 18       	shll8	r5
   47a9e:	45 08       	shll2	r5
   47aa0:	45 08       	shll2	r5
   47aa2:	60 0d       	extu.w	r0,r0
   47aa4:	40 18       	shll8	r0
   47aa6:	35 0c       	add	r0,r5
   47aa8:	85 f2       	mov.w	@(4,r15),r0
   47aaa:	60 0d       	extu.w	r0,r0
   47aac:	40 08       	shll2	r0
   47aae:	40 08       	shll2	r0
   47ab0:	35 0c       	add	r0,r5
   47ab2:	35 3c       	add	r3,r5
   47ab4:	64 5d       	extu.w	r5,r4
   47ab6:	62 43       	mov	r4,r2
   47ab8:	42 21       	shar	r2
   47aba:	42 21       	shar	r2
   47abc:	42 21       	shar	r2
   47abe:	60 43       	mov	r4,r0
   47ac0:	40 18       	shll8	r0
   47ac2:	40 08       	shll2	r0
   47ac4:	40 08       	shll2	r0
   47ac6:	40 00       	shll	r0
   47ac8:	64 23       	mov	r2,r4
   47aca:	34 0c       	add	r0,r4
   47acc:	60 43       	mov	r4,r0
   47ace:	00 0b       	rts	
   47ad0:	7f 0c       	add	#12,r15
   47ad2:	63 43       	mov	r4,r3
   47ad4:	2f e6       	mov.l	r14,@-r15
   47ad6:	43 29       	shlr16	r3
   47ad8:	4f 22       	sts.l	pr,@-r15
   47ada:	7f fc       	add	#-4,r15
   47adc:	2f 31       	mov.w	r3,@r15
   47ade:	bf b5       	bsr	0x47a4c
   47ae0:	6e 43       	mov	r4,r14
   47ae2:	64 03       	mov	r0,r4
   47ae4:	63 f1       	mov.w	@r15,r3
   47ae6:	60 ed       	extu.w	r14,r0
   47ae8:	24 3a       	xor	r3,r4
   47aea:	40 28       	shll16	r0
   47aec:	64 4d       	extu.w	r4,r4
   47aee:	30 4c       	add	r4,r0
   47af0:	7f 04       	add	#4,r15
   47af2:	4f 26       	lds.l	@r15+,pr
   47af4:	00 0b       	rts	
   47af6:	6e f6       	mov.l	@r15+,r14
   47af8:	00 04       	mov.b	r0,@(r0,r0)
   47afa:	ea ec       	mov	#-20,r10
   47afc:	2f e6       	mov.l	r14,@-r15
   47afe:	2f d6       	mov.l	r13,@-r15
   47b00:	2f c6       	mov.l	r12,@-r15
   47b02:	2f b6       	mov.l	r11,@-r15
   47b04:	2f a6       	mov.l	r10,@-r15
   47b06:	2f 96       	mov.l	r9,@-r15
   47b08:	ff fb       	fmov	fr15,@-r15
   47b0a:	4f 22       	sts.l	pr,@-r15
   47b0c:	d3 42       	mov.l	0x47c18,r3	! f6fe
   47b0e:	7f dc       	add	#-36,r15
   47b10:	43 0b       	jsr	@r3
   47b12:	00 09       	nop	
   47b14:	dc 41       	mov.l	0x47c1c,r12	! 2088
   47b16:	64 f3       	mov	r15,r4
   47b18:	9d 76       	mov.w	0x47c08,r13	! e0
   47b1a:	65 d3       	mov	r13,r5
   47b1c:	4c 0b       	jsr	@r12
   47b1e:	74 1c       	add	#28,r4
   47b20:	9a 73       	mov.w	0x47c0a,r10	! f746
   47b22:	e6 01       	mov	#1,r6
   47b24:	95 72       	mov.w	0x47c0c,r5	! 200
   47b26:	de 3e       	mov.l	0x47c20,r14	! 4b04
   47b28:	4e 0b       	jsr	@r14
   47b2a:	64 a3       	mov	r10,r4
   47b2c:	db 3d       	mov.l	0x47c24,r11	! 2098
   47b2e:	4b 0b       	jsr	@r11
   47b30:	54 f7       	mov.l	@(28,r15),r4
   47b32:	ff 8d       	fldi0	fr15
   47b34:	d3 3c       	mov.l	0x47c28,r3	! ac9a
   47b36:	43 0b       	jsr	@r3
   47b38:	f4 fc       	fmov	fr15,fr4
   47b3a:	65 d3       	mov	r13,r5
   47b3c:	64 f3       	mov	r15,r4
   47b3e:	4c 0b       	jsr	@r12
   47b40:	74 18       	add	#24,r4
   47b42:	e6 01       	mov	#1,r6
   47b44:	95 63       	mov.w	0x47c0e,r5	! 800
   47b46:	4e 0b       	jsr	@r14
   47b48:	64 a3       	mov	r10,r4
   47b4a:	4b 0b       	jsr	@r11
   47b4c:	54 f6       	mov.l	@(24,r15),r4
   47b4e:	d3 37       	mov.l	0x47c2c,r3	! 3af4
   47b50:	43 0b       	jsr	@r3
   47b52:	e4 10       	mov	#16,r4
   47b54:	1f 08       	mov.l	r0,@(32,r15)
   47b56:	65 d3       	mov	r13,r5
   47b58:	64 f3       	mov	r15,r4
   47b5a:	4c 0b       	jsr	@r12
   47b5c:	74 14       	add	#20,r4
   47b5e:	e6 01       	mov	#1,r6
   47b60:	9a 56       	mov.w	0x47c10,r10	! f754
   47b62:	65 63       	mov	r6,r5
   47b64:	4e 0b       	jsr	@r14
   47b66:	64 a3       	mov	r10,r4
   47b68:	4b 0b       	jsr	@r11
   47b6a:	54 f5       	mov.l	@(20,r15),r4
   47b6c:	65 d3       	mov	r13,r5
   47b6e:	64 f3       	mov	r15,r4
   47b70:	4c 0b       	jsr	@r12
   47b72:	74 10       	add	#16,r4
   47b74:	e6 01       	mov	#1,r6
   47b76:	e5 02       	mov	#2,r5
   47b78:	4e 0b       	jsr	@r14
   47b7a:	64 a3       	mov	r10,r4
   47b7c:	4b 0b       	jsr	@r11
   47b7e:	54 f4       	mov.l	@(16,r15),r4
   47b80:	d3 2b       	mov.l	0x47c30,r3	! 3b08
   47b82:	43 0b       	jsr	@r3
   47b84:	54 f8       	mov.l	@(32,r15),r4
   47b86:	65 d3       	mov	r13,r5
   47b88:	64 f3       	mov	r15,r4
   47b8a:	4c 0b       	jsr	@r12
   47b8c:	74 0c       	add	#12,r4
   47b8e:	e6 00       	mov	#0,r6
   47b90:	e5 40       	mov	#64,r5
   47b92:	4e 0b       	jsr	@r14
   47b94:	64 a3       	mov	r10,r4
   47b96:	4b 0b       	jsr	@r11
   47b98:	54 f3       	mov.l	@(12,r15),r4
   47b9a:	d3 26       	mov.l	0x47c34,r3	! 8384
   47b9c:	43 0b       	jsr	@r3
   47b9e:	f4 fc       	fmov	fr15,fr4
   47ba0:	9a 37       	mov.w	0x47c12,r10	! f76c
   47ba2:	e6 00       	mov	#0,r6
   47ba4:	d2 24       	mov.l	0x47c38,r2	! 4acc
   47ba6:	e5 04       	mov	#4,r5
   47ba8:	42 0b       	jsr	@r2
   47baa:	64 a3       	mov	r10,r4
   47bac:	d3 22       	mov.l	0x47c38,r3	! 4acc
   47bae:	e6 00       	mov	#0,r6
   47bb0:	e5 05       	mov	#5,r5
   47bb2:	43 0b       	jsr	@r3
   47bb4:	64 a3       	mov	r10,r4
   47bb6:	65 d3       	mov	r13,r5
   47bb8:	64 f3       	mov	r15,r4
   47bba:	4c 0b       	jsr	@r12
   47bbc:	74 08       	add	#8,r4
   47bbe:	e6 01       	mov	#1,r6
   47bc0:	99 28       	mov.w	0x47c14,r9	! f75e
   47bc2:	e5 40       	mov	#64,r5
   47bc4:	4e 0b       	jsr	@r14
   47bc6:	64 93       	mov	r9,r4
   47bc8:	4b 0b       	jsr	@r11
   47bca:	54 f2       	mov.l	@(8,r15),r4
   47bcc:	65 d3       	mov	r13,r5
   47bce:	64 f3       	mov	r15,r4
   47bd0:	4c 0b       	jsr	@r12
   47bd2:	74 04       	add	#4,r4
   47bd4:	e6 01       	mov	#1,r6
   47bd6:	65 63       	mov	r6,r5
   47bd8:	75 7f       	add	#127,r5
   47bda:	4e 0b       	jsr	@r14
   47bdc:	64 93       	mov	r9,r4
   47bde:	4b 0b       	jsr	@r11
   47be0:	54 f1       	mov.l	@(4,r15),r4
   47be2:	65 d3       	mov	r13,r5
   47be4:	4c 0b       	jsr	@r12
   47be6:	64 f3       	mov	r15,r4
   47be8:	e6 01       	mov	#1,r6
   47bea:	e5 40       	mov	#64,r5
   47bec:	4e 0b       	jsr	@r14
   47bee:	64 a3       	mov	r10,r4
   47bf0:	4b 0b       	jsr	@r11
   47bf2:	64 f2       	mov.l	@r15,r4
   47bf4:	7f 24       	add	#36,r15
   47bf6:	4f 26       	lds.l	@r15+,pr
   47bf8:	ff f9       	fmov	@r15+,fr15
   47bfa:	69 f6       	mov.l	@r15+,r9
   47bfc:	6a f6       	mov.l	@r15+,r10
   47bfe:	6b f6       	mov.l	@r15+,r11
   47c00:	6c f6       	mov.l	@r15+,r12
   47c02:	6d f6       	mov.l	@r15+,r13
   47c04:	00 0b       	rts	
   47c06:	6e f6       	mov.l	@r15+,r14
   47c08:	00 e0       	.word 0x00e0
   47c0a:	f7 46       	fmov	@(r0,r4),fr7
   47c0c:	02 00       	.word 0x0200
   47c0e:	08 00       	.word 0x0800
   47c10:	f7 54       	fcmp/eq	fr5,fr7
   47c12:	f7 6c       	fmov	fr6,fr7
   47c14:	f7 5e       	fmac	fr0,fr5,fr7
   47c16:	ff ff       	.word 0xffff
   47c18:	00 00       	.word 0x0000
   47c1a:	f6 fe       	fmac	fr0,fr15,fr6
   47c1c:	00 00       	.word 0x0000
   47c1e:	20 88       	tst	r8,r0
   47c20:	00 00       	.word 0x0000
   47c22:	4b 04       	rotl	r11
   47c24:	00 00       	.word 0x0000
   47c26:	20 98       	tst	r9,r0
   47c28:	00 00       	.word 0x0000
   47c2a:	ac 9a       	bra	0x47562
   47c2c:	00 00       	.word 0x0000
   47c2e:	3a f4       	div1	r15,r10
   47c30:	00 00       	.word 0x0000
   47c32:	3b 08       	sub	r0,r11
   47c34:	00 00       	.word 0x0000
   47c36:	83 84       	.word 0x8384
   47c38:	00 00       	.word 0x0000
   47c3a:	4a cc       	.word 0x4acc
   47c3c:	d2 40       	mov.l	0x47d40,r2	! ffff63f1
   47c3e:	e1 00       	mov	#0,r1
   47c40:	90 77       	mov.w	0x47d32,r0	! f010
   47c42:	e3 01       	mov	#1,r3
   47c44:	22 30       	mov.b	r3,@r2
   47c46:	20 10       	mov.b	r1,@r0
   47c48:	94 74       	mov.w	0x47d34,r4	! f012
   47c4a:	60 40       	mov.b	@r4,r0
   47c4c:	c9 fc       	and	#-4,r0
   47c4e:	24 00       	mov.b	r0,@r4
   47c50:	93 71       	mov.w	0x47d36,r3	! f0
   47c52:	91 71       	mov.w	0x47d38,r1	! f016
   47c54:	21 30       	mov.b	r3,@r1
   47c56:	90 70       	mov.w	0x47d3a,r0	! 81
   47c58:	93 70       	mov.w	0x47d3c,r3	! f011
   47c5a:	23 00       	mov.b	r0,@r3
   47c5c:	60 40       	mov.b	@r4,r0
   47c5e:	c9 0b       	and	#11,r0
   47c60:	cb 50       	or	#80,r0
   47c62:	00 0b       	rts	
   47c64:	24 00       	mov.b	r0,@r4
   47c66:	2f e6       	mov.l	r14,@-r15
   47c68:	4f 22       	sts.l	pr,@-r15
   47c6a:	d3 36       	mov.l	0x47d44,r3	! 779c2
   47c6c:	43 0b       	jsr	@r3
   47c6e:	00 09       	nop	
   47c70:	d3 33       	mov.l	0x47d40,r3	! ffff63f1
   47c72:	6e 03       	mov	r0,r14
   47c74:	62 30       	mov.b	@r3,r2
   47c76:	64 ec       	extu.b	r14,r4
   47c78:	62 2c       	extu.b	r2,r2
   47c7a:	32 40       	cmp/eq	r4,r2
   47c7c:	8d 09       	bt.s	0x47c92
   47c7e:	00 09       	nop	
   47c80:	24 48       	tst	r4,r4
   47c82:	8f 04       	bf.s	0x47c8e
   47c84:	00 09       	nop	
   47c86:	b0 50       	bsr	0x47d2a
   47c88:	00 09       	nop	
   47c8a:	a0 02       	bra	0x47c92
   47c8c:	00 09       	nop	
   47c8e:	b0 24       	bsr	0x47cda
   47c90:	00 09       	nop	
   47c92:	d3 2b       	mov.l	0x47d40,r3	! ffff63f1
   47c94:	d1 2c       	mov.l	0x47d48,r1	! ffff63f0
   47c96:	23 e0       	mov.b	r14,@r3
   47c98:	62 10       	mov.b	@r1,r2
   47c9a:	22 28       	tst	r2,r2
   47c9c:	8f 04       	bf.s	0x47ca8
   47c9e:	00 09       	nop	
   47ca0:	4f 26       	lds.l	@r15+,pr
   47ca2:	d2 2a       	mov.l	0x47d4c,r2	! 47d94
   47ca4:	42 2b       	jmp	@r2
   47ca6:	6e f6       	mov.l	@r15+,r14
   47ca8:	4f 26       	lds.l	@r15+,pr
   47caa:	00 0b       	rts	
   47cac:	6e f6       	mov.l	@r15+,r14
   47cae:	d0 26       	mov.l	0x47d48,r0	! ffff63f0
   47cb0:	63 00       	mov.b	@r0,r3
   47cb2:	23 38       	tst	r3,r3
   47cb4:	8f 03       	bf.s	0x47cbe
   47cb6:	00 09       	nop	
   47cb8:	d2 25       	mov.l	0x47d50,r2	! 47e24
   47cba:	42 2b       	jmp	@r2
   47cbc:	00 09       	nop	
   47cbe:	d1 25       	mov.l	0x47d54,r1	! 7794e
   47cc0:	41 2b       	jmp	@r1
   47cc2:	00 09       	nop	
   47cc4:	d1 20       	mov.l	0x47d48,r1	! ffff63f0
   47cc6:	62 10       	mov.b	@r1,r2
   47cc8:	22 28       	tst	r2,r2
   47cca:	8f 03       	bf.s	0x47cd4
   47ccc:	00 09       	nop	
   47cce:	d3 22       	mov.l	0x47d58,r3	! 47ecc
   47cd0:	43 2b       	jmp	@r3
   47cd2:	00 09       	nop	
   47cd4:	d3 21       	mov.l	0x47d5c,r3	! 779b4
   47cd6:	43 2b       	jmp	@r3
   47cd8:	00 09       	nop	
   47cda:	e3 00       	mov	#0,r3
   47cdc:	d0 1a       	mov.l	0x47d48,r0	! ffff63f0
   47cde:	4f 22       	sts.l	pr,@-r15
   47ce0:	d2 1d       	mov.l	0x47d58,r2	! 47ecc
   47ce2:	42 0b       	jsr	@r2
   47ce4:	20 30       	mov.b	r3,@r0
   47ce6:	d1 1e       	mov.l	0x47d60,r1	! 761cc
   47ce8:	41 0b       	jsr	@r1
   47cea:	00 09       	nop	
   47cec:	d2 1d       	mov.l	0x47d64,r2	! 762a8
   47cee:	42 0b       	jsr	@r2
   47cf0:	00 09       	nop	
   47cf2:	d1 1d       	mov.l	0x47d68,r1	! 75b38
   47cf4:	41 0b       	jsr	@r1
   47cf6:	00 09       	nop	
   47cf8:	d2 1c       	mov.l	0x47d6c,r2	! 764d8
   47cfa:	42 0b       	jsr	@r2
   47cfc:	00 09       	nop	
   47cfe:	d1 1c       	mov.l	0x47d70,r1	! 776d8
   47d00:	41 0b       	jsr	@r1
   47d02:	00 09       	nop	
   47d04:	91 15       	mov.w	0x47d32,r1	! f010
   47d06:	e2 00       	mov	#0,r2
   47d08:	21 20       	mov.b	r2,@r1
   47d0a:	94 13       	mov.w	0x47d34,r4	! f012
   47d0c:	60 40       	mov.b	@r4,r0
   47d0e:	c9 fc       	and	#-4,r0
   47d10:	24 00       	mov.b	r0,@r4
   47d12:	93 10       	mov.w	0x47d36,r3	! f0
   47d14:	92 10       	mov.w	0x47d38,r2	! f016
   47d16:	22 30       	mov.b	r3,@r2
   47d18:	90 0f       	mov.w	0x47d3a,r0	! 81
   47d1a:	93 0f       	mov.w	0x47d3c,r3	! f011
   47d1c:	23 00       	mov.b	r0,@r3
   47d1e:	60 40       	mov.b	@r4,r0
   47d20:	c9 0b       	and	#11,r0
   47d22:	cb 50       	or	#80,r0
   47d24:	4f 26       	lds.l	@r15+,pr
   47d26:	00 0b       	rts	
   47d28:	24 00       	mov.b	r0,@r4
   47d2a:	e3 01       	mov	#1,r3
   47d2c:	d2 06       	mov.l	0x47d48,r2	! ffff63f0
   47d2e:	00 0b       	rts	
   47d30:	22 30       	mov.b	r3,@r2
   47d32:	f0 10       	fadd	fr1,fr0
   47d34:	f0 12       	fmul	fr1,fr0
   47d36:	00 f0       	.word 0x00f0
   47d38:	f0 16       	fmov	@(r0,r1),fr0
   47d3a:	00 81       	.word 0x0081
   47d3c:	f0 11       	fsub	fr1,fr0
   47d3e:	ff ff       	.word 0xffff
   47d40:	ff ff       	.word 0xffff
   47d42:	63 f1       	mov.w	@r15,r3
   47d44:	00 07       	mul.l	r0,r0
   47d46:	79 c2       	add	#-62,r9
   47d48:	ff ff       	.word 0xffff
   47d4a:	63 f0       	mov.b	@r15,r3
   47d4c:	00 04       	mov.b	r0,@(r0,r0)
   47d4e:	7d 94       	add	#-108,r13
   47d50:	00 04       	mov.b	r0,@(r0,r0)
   47d52:	7e 24       	add	#36,r14
   47d54:	00 07       	mul.l	r0,r0
   47d56:	79 4e       	add	#78,r9
   47d58:	00 04       	mov.b	r0,@(r0,r0)
   47d5a:	7e cc       	add	#-52,r14
   47d5c:	00 07       	mul.l	r0,r0
   47d5e:	79 b4       	add	#-76,r9
   47d60:	00 07       	mul.l	r0,r0
   47d62:	61 cc       	extu.b	r12,r1
   47d64:	00 07       	mul.l	r0,r0
   47d66:	62 a8       	swap.b	r10,r2
   47d68:	00 07       	mul.l	r0,r0
   47d6a:	5b 38       	mov.l	@(32,r3),r11
   47d6c:	00 07       	mul.l	r0,r0
   47d6e:	64 d8       	swap.b	r13,r4
   47d70:	00 07       	mul.l	r0,r0
   47d72:	76 d8       	add	#-40,r6
   47d74:	2f e6       	mov.l	r14,@-r15
   47d76:	4f 22       	sts.l	pr,@-r15
   47d78:	d3 05       	mov.l	0x47d90,r3	! 48b18
   47d7a:	43 0b       	jsr	@r3
   47d7c:	ee 00       	mov	#0,r14
   47d7e:	60 0c       	extu.b	r0,r0
   47d80:	20 08       	tst	r0,r0
   47d82:	8d 01       	bt.s	0x47d88
   47d84:	00 09       	nop	
   47d86:	ee 01       	mov	#1,r14
   47d88:	4f 26       	lds.l	@r15+,pr
   47d8a:	60 e3       	mov	r14,r0
   47d8c:	00 0b       	rts	
   47d8e:	6e f6       	mov.l	@r15+,r14
   47d90:	00 04       	mov.b	r0,@(r0,r0)
   47d92:	8b 18       	bf	0x47dc6
   47d94:	2f e6       	mov.l	r14,@-r15
   47d96:	4f 22       	sts.l	pr,@-r15
   47d98:	94 7a       	mov.w	0x47e90,r4	! 90
   47d9a:	7f fc       	add	#-4,r15
   47d9c:	d3 3e       	mov.l	0x47e98,r3	! 3af4
   47d9e:	43 0b       	jsr	@r3
   47da0:	00 09       	nop	
   47da2:	e5 01       	mov	#1,r5
   47da4:	d3 3e       	mov.l	0x47ea0,r3	! 251c
   47da6:	2f 02       	mov.l	r0,@r15
   47da8:	de 3c       	mov.l	0x47e9c,r14	! ffff63f6
   47daa:	43 0b       	jsr	@r3
   47dac:	64 e1       	mov.w	@r14,r4
   47dae:	e3 08       	mov	#8,r3
   47db0:	2e 01       	mov.w	r0,@r14
   47db2:	62 e1       	mov.w	@r14,r2
   47db4:	62 2d       	extu.w	r2,r2
   47db6:	32 33       	cmp/ge	r3,r2
   47db8:	8f 05       	bf.s	0x47dc6
   47dba:	00 09       	nop	
   47dbc:	b0 86       	bsr	0x47ecc
   47dbe:	00 09       	nop	
   47dc0:	d2 38       	mov.l	0x47ea4,r2	! 47230
   47dc2:	42 0b       	jsr	@r2
   47dc4:	00 09       	nop	
   47dc6:	de 38       	mov.l	0x47ea8,r14	! ffff6400
   47dc8:	d0 38       	mov.l	0x47eac,r0	! ffff649a
   47dca:	60 00       	mov.b	@r0,r0
   47dcc:	c8 20       	tst	#32,r0
   47dce:	00 29       	movt	r0
   47dd0:	70 ff       	add	#-1,r0
   47dd2:	60 0b       	neg	r0,r0
   47dd4:	88 01       	cmp/eq	#1,r0
   47dd6:	8f 14       	bf.s	0x47e02
   47dd8:	00 09       	nop	
   47dda:	e5 01       	mov	#1,r5
   47ddc:	d2 34       	mov.l	0x47eb0,r2	! 2534
   47dde:	42 0b       	jsr	@r2
   47de0:	64 e0       	mov.b	@r14,r4
   47de2:	2e 00       	mov.b	r0,@r14
   47de4:	60 e0       	mov.b	@r14,r0
   47de6:	60 0c       	extu.b	r0,r0
   47de8:	88 03       	cmp/eq	#3,r0
   47dea:	8f 0c       	bf.s	0x47e06
   47dec:	00 09       	nop	
   47dee:	d2 31       	mov.l	0x47eb4,r2	! ffff6492
   47df0:	91 4f       	mov.w	0x47e92,r1	! f013
   47df2:	63 20       	mov.b	@r2,r3
   47df4:	21 30       	mov.b	r3,@r1
   47df6:	94 4d       	mov.w	0x47e94,r4	! f014
   47df8:	60 40       	mov.b	@r4,r0
   47dfa:	c9 7f       	and	#127,r0
   47dfc:	cb 78       	or	#120,r0
   47dfe:	a0 02       	bra	0x47e06
   47e00:	24 00       	mov.b	r0,@r4
   47e02:	e2 00       	mov	#0,r2
   47e04:	2e 20       	mov.b	r2,@r14
   47e06:	d4 2c       	mov.l	0x47eb8,r4	! ffff6498
   47e08:	63 41       	mov.w	@r4,r3
   47e0a:	63 3d       	extu.w	r3,r3
   47e0c:	43 15       	cmp/pl	r3
   47e0e:	8f 03       	bf.s	0x47e18
   47e10:	00 09       	nop	
   47e12:	63 41       	mov.w	@r4,r3
   47e14:	73 ff       	add	#-1,r3
   47e16:	24 31       	mov.w	r3,@r4
   47e18:	64 f2       	mov.l	@r15,r4
   47e1a:	7f 04       	add	#4,r15
   47e1c:	d3 27       	mov.l	0x47ebc,r3	! 3b08
   47e1e:	4f 26       	lds.l	@r15+,pr
   47e20:	43 2b       	jmp	@r3
   47e22:	6e f6       	mov.l	@r15+,r14
   47e24:	4f 22       	sts.l	pr,@-r15
   47e26:	d5 26       	mov.l	0x47ec0,r5	! ffff63f8
   47e28:	92 35       	mov.w	0x47e96,r2	! f015
   47e2a:	63 20       	mov.b	@r2,r3
   47e2c:	25 30       	mov.b	r3,@r5
   47e2e:	94 31       	mov.w	0x47e94,r4	! f014
   47e30:	60 40       	mov.b	@r4,r0
   47e32:	c9 bf       	and	#-65,r0
   47e34:	cb b8       	or	#-72,r0
   47e36:	24 00       	mov.b	r0,@r4
   47e38:	d6 22       	mov.l	0x47ec4,r6	! ffff649e
   47e3a:	60 40       	mov.b	@r4,r0
   47e3c:	c9 38       	and	#56,r0
   47e3e:	26 00       	mov.b	r0,@r6
   47e40:	60 40       	mov.b	@r4,r0
   47e42:	c9 87       	and	#-121,r0
   47e44:	cb 80       	or	#-128,r0
   47e46:	24 00       	mov.b	r0,@r4
   47e48:	d1 14       	mov.l	0x47e9c,r1	! ffff63f6
   47e4a:	e3 00       	mov	#0,r3
   47e4c:	21 31       	mov.w	r3,@r1
   47e4e:	60 60       	mov.b	@r6,r0
   47e50:	20 08       	tst	r0,r0
   47e52:	8d 05       	bt.s	0x47e60
   47e54:	00 09       	nop	
   47e56:	b0 39       	bsr	0x47ecc
   47e58:	00 09       	nop	
   47e5a:	d2 12       	mov.l	0x47ea4,r2	! 47230
   47e5c:	42 2b       	jmp	@r2
   47e5e:	4f 26       	lds.l	@r15+,pr
   47e60:	d0 12       	mov.l	0x47eac,r0	! ffff649a
   47e62:	60 00       	mov.b	@r0,r0
   47e64:	c8 20       	tst	#32,r0
   47e66:	00 29       	movt	r0
   47e68:	70 ff       	add	#-1,r0
   47e6a:	60 0b       	neg	r0,r0
   47e6c:	88 01       	cmp/eq	#1,r0
   47e6e:	8f 0d       	bf.s	0x47e8c
   47e70:	00 09       	nop	
   47e72:	62 50       	mov.b	@r5,r2
   47e74:	d0 14       	mov.l	0x47ec8,r0	! ffff63f9
   47e76:	63 00       	mov.b	@r0,r3
   47e78:	32 30       	cmp/eq	r3,r2
   47e7a:	8f 02       	bf.s	0x47e82
   47e7c:	00 09       	nop	
   47e7e:	a1 05       	bra	0x4808c
   47e80:	4f 26       	lds.l	@r15+,pr
   47e82:	b0 23       	bsr	0x47ecc
   47e84:	00 09       	nop	
   47e86:	d3 07       	mov.l	0x47ea4,r3	! 47230
   47e88:	43 2b       	jmp	@r3
   47e8a:	4f 26       	lds.l	@r15+,pr
   47e8c:	a0 48       	bra	0x47f20
   47e8e:	4f 26       	lds.l	@r15+,pr
   47e90:	00 90       	.word 0x0090
   47e92:	f0 13       	fdiv	fr1,fr0
   47e94:	f0 14       	fcmp/eq	fr1,fr0
   47e96:	f0 15       	fcmp/gt	fr1,fr0
   47e98:	00 00       	.word 0x0000
   47e9a:	3a f4       	div1	r15,r10
   47e9c:	ff ff       	.word 0xffff
   47e9e:	63 f6       	mov.l	@r15+,r3
   47ea0:	00 00       	.word 0x0000
   47ea2:	25 1c       	cmp/str	r1,r5
   47ea4:	00 04       	mov.b	r0,@(r0,r0)
   47ea6:	72 30       	add	#48,r2
   47ea8:	ff ff       	.word 0xffff
   47eaa:	64 00       	mov.b	@r0,r4
   47eac:	ff ff       	.word 0xffff
   47eae:	64 9a       	negc	r9,r4
   47eb0:	00 00       	.word 0x0000
   47eb2:	25 34       	mov.b	r3,@-r5
   47eb4:	ff ff       	.word 0xffff
   47eb6:	64 92       	mov.l	@r9,r4
   47eb8:	ff ff       	.word 0xffff
   47eba:	64 98       	swap.b	r9,r4
   47ebc:	00 00       	.word 0x0000
   47ebe:	3b 08       	sub	r0,r11
   47ec0:	ff ff       	.word 0xffff
   47ec2:	63 f8       	swap.b	r15,r3
   47ec4:	ff ff       	.word 0xffff
   47ec6:	64 9e       	exts.b	r9,r4
   47ec8:	ff ff       	.word 0xffff
   47eca:	63 f9       	swap.w	r15,r3
   47ecc:	d2 2b       	mov.l	0x47f7c,r2	! ffff63f0
   47ece:	63 20       	mov.b	@r2,r3
   47ed0:	23 38       	tst	r3,r3
   47ed2:	8f 04       	bf.s	0x47ede
   47ed4:	e5 00       	mov	#0,r5
   47ed6:	94 4e       	mov.w	0x47f76,r4	! f012
   47ed8:	60 40       	mov.b	@r4,r0
   47eda:	c9 5b       	and	#91,r0
   47edc:	24 00       	mov.b	r0,@r4
   47ede:	d3 28       	mov.l	0x47f80,r3	! ffff63fa
   47ee0:	d2 28       	mov.l	0x47f84,r2	! ffff63fb
   47ee2:	23 50       	mov.b	r5,@r3
   47ee4:	22 50       	mov.b	r5,@r2
   47ee6:	d1 28       	mov.l	0x47f88,r1	! ffff63fc
   47ee8:	d3 28       	mov.l	0x47f8c,r3	! ffff6403
   47eea:	21 50       	mov.b	r5,@r1
   47eec:	23 50       	mov.b	r5,@r3
   47eee:	d2 28       	mov.l	0x47f90,r2	! ffff6404
   47ef0:	d1 28       	mov.l	0x47f94,r1	! ffff6402
   47ef2:	22 50       	mov.b	r5,@r2
   47ef4:	21 50       	mov.b	r5,@r1
   47ef6:	d4 28       	mov.l	0x47f98,r4	! ffff649a
   47ef8:	d2 28       	mov.l	0x47f9c,r2	! ffff63fd
   47efa:	60 40       	mov.b	@r4,r0
   47efc:	d3 28       	mov.l	0x47fa0,r3	! ffff63fe
   47efe:	c9 bf       	and	#-65,r0
   47f00:	24 00       	mov.b	r0,@r4
   47f02:	60 40       	mov.b	@r4,r0
   47f04:	c9 df       	and	#-33,r0
   47f06:	24 00       	mov.b	r0,@r4
   47f08:	60 40       	mov.b	@r4,r0
   47f0a:	c9 7f       	and	#127,r0
   47f0c:	24 00       	mov.b	r0,@r4
   47f0e:	84 41       	mov.b	@(1,r4),r0
   47f10:	c9 fd       	and	#-3,r0
   47f12:	80 41       	mov.b	r0,@(1,r4)
   47f14:	22 50       	mov.b	r5,@r2
   47f16:	23 50       	mov.b	r5,@r3
   47f18:	84 41       	mov.b	@(1,r4),r0
   47f1a:	c9 fb       	and	#-5,r0
   47f1c:	00 0b       	rts	
   47f1e:	80 41       	mov.b	r0,@(1,r4)
   47f20:	2f e6       	mov.l	r14,@-r15
   47f22:	e2 04       	mov	#4,r2
   47f24:	d4 1f       	mov.l	0x47fa4,r4	! ffff63f8
   47f26:	2f d6       	mov.l	r13,@-r15
   47f28:	2f c6       	mov.l	r12,@-r15
   47f2a:	2f b6       	mov.l	r11,@-r15
   47f2c:	2f a6       	mov.l	r10,@-r15
   47f2e:	eb 00       	mov	#0,r11
   47f30:	dc 1b       	mov.l	0x47fa0,r12	! ffff63fe
   47f32:	2f 96       	mov.l	r9,@-r15
   47f34:	4f 22       	sts.l	pr,@-r15
   47f36:	9a 1f       	mov.w	0x47f78,r10	! 89
   47f38:	dd 17       	mov.l	0x47f98,r13	! ffff649a
   47f3a:	de 18       	mov.l	0x47f9c,r14	! ffff63fd
   47f3c:	63 e0       	mov.b	@r14,r3
   47f3e:	63 3c       	extu.b	r3,r3
   47f40:	33 23       	cmp/ge	r2,r3
   47f42:	8d 35       	bt.s	0x47fb0
   47f44:	69 b3       	mov	r11,r9
   47f46:	e5 01       	mov	#1,r5
   47f48:	84 d1       	mov.b	@(1,r13),r0
   47f4a:	cb 04       	or	#4,r0
   47f4c:	80 d1       	mov.b	r0,@(1,r13)
   47f4e:	63 e0       	mov.b	@r14,r3
   47f50:	d0 15       	mov.l	0x47fa8,r0	! ffff6408
   47f52:	63 3c       	extu.b	r3,r3
   47f54:	62 40       	mov.b	@r4,r2
   47f56:	03 24       	mov.b	r2,@(r0,r3)
   47f58:	63 c0       	mov.b	@r12,r3
   47f5a:	61 40       	mov.b	@r4,r1
   47f5c:	31 3c       	add	r3,r1
   47f5e:	2c 10       	mov.b	r1,@r12
   47f60:	d3 12       	mov.l	0x47fac,r3	! 2534
   47f62:	43 0b       	jsr	@r3
   47f64:	64 e0       	mov.b	@r14,r4
   47f66:	64 03       	mov	r0,r4
   47f68:	62 4c       	extu.b	r4,r2
   47f6a:	32 a7       	cmp/gt	r10,r2
   47f6c:	8f 01       	bf.s	0x47f72
   47f6e:	00 09       	nop	
   47f70:	64 a3       	mov	r10,r4
   47f72:	a0 75       	bra	0x48060
   47f74:	2e 40       	mov.b	r4,@r14
   47f76:	f0 12       	fmul	fr1,fr0
   47f78:	00 89       	.word 0x0089
   47f7a:	ff ff       	.word 0xffff
   47f7c:	ff ff       	.word 0xffff
   47f7e:	63 f0       	mov.b	@r15,r3
   47f80:	ff ff       	.word 0xffff
   47f82:	63 fa       	negc	r15,r3
   47f84:	ff ff       	.word 0xffff
   47f86:	63 fb       	neg	r15,r3
   47f88:	ff ff       	.word 0xffff
   47f8a:	63 fc       	extu.b	r15,r3
   47f8c:	ff ff       	.word 0xffff
   47f8e:	64 03       	mov	r0,r4
   47f90:	ff ff       	.word 0xffff
   47f92:	64 04       	mov.b	@r0+,r4
   47f94:	ff ff       	.word 0xffff
   47f96:	64 02       	mov.l	@r0,r4
   47f98:	ff ff       	.word 0xffff
   47f9a:	64 9a       	negc	r9,r4
   47f9c:	ff ff       	.word 0xffff
   47f9e:	63 fd       	extu.w	r15,r3
   47fa0:	ff ff       	.word 0xffff
   47fa2:	63 fe       	exts.b	r15,r3
   47fa4:	ff ff       	.word 0xffff
   47fa6:	63 f8       	swap.b	r15,r3
   47fa8:	ff ff       	.word 0xffff
   47faa:	64 08       	swap.b	r0,r4
   47fac:	00 00       	.word 0x0000
   47fae:	25 34       	mov.b	r3,@-r5
   47fb0:	84 d1       	mov.b	@(1,r13),r0
   47fb2:	c9 fb       	and	#-5,r0
   47fb4:	80 d1       	mov.b	r0,@(1,r13)
   47fb6:	67 e0       	mov.b	@r14,r7
   47fb8:	d6 2e       	mov.l	0x48074,r6	! ffff6408
   47fba:	62 7c       	extu.b	r7,r2
   47fbc:	84 63       	mov.b	@(3,r6),r0
   47fbe:	60 0c       	extu.b	r0,r0
   47fc0:	70 04       	add	#4,r0
   47fc2:	32 00       	cmp/eq	r0,r2
   47fc4:	8f 3a       	bf.s	0x4803c
   47fc6:	65 40       	mov.b	@r4,r5
   47fc8:	62 c0       	mov.b	@r12,r2
   47fca:	65 5c       	extu.b	r5,r5
   47fcc:	62 2c       	extu.b	r2,r2
   47fce:	35 20       	cmp/eq	r2,r5
   47fd0:	8f 31       	bf.s	0x48036
   47fd2:	00 09       	nop	
   47fd4:	d2 28       	mov.l	0x48078,r2	! 47132
   47fd6:	42 0b       	jsr	@r2
   47fd8:	00 09       	nop	
   47fda:	60 0c       	extu.b	r0,r0
   47fdc:	20 08       	tst	r0,r0
   47fde:	8d 03       	bt.s	0x47fe8
   47fe0:	00 09       	nop	
   47fe2:	e9 01       	mov	#1,r9
   47fe4:	d2 25       	mov.l	0x4807c,r2	! ffff6400
   47fe6:	22 b0       	mov.b	r11,@r2
   47fe8:	69 9c       	extu.b	r9,r9
   47fea:	29 98       	tst	r9,r9
   47fec:	8f 23       	bf.s	0x48036
   47fee:	00 09       	nop	
   47ff0:	d2 20       	mov.l	0x48074,r2	! ffff6408
   47ff2:	63 20       	mov.b	@r2,r3
   47ff4:	91 3c       	mov.w	0x48070,r1	! 80
   47ff6:	63 3c       	extu.b	r3,r3
   47ff8:	33 10       	cmp/eq	r1,r3
   47ffa:	8f 1c       	bf.s	0x48036
   47ffc:	00 09       	nop	
   47ffe:	d0 20       	mov.l	0x48080,r0	! ffff6409
   48000:	60 00       	mov.b	@r0,r0
   48002:	60 0c       	extu.b	r0,r0
   48004:	88 10       	cmp/eq	#16,r0
   48006:	8f 16       	bf.s	0x48036
   48008:	00 09       	nop	
   4800a:	d2 1e       	mov.l	0x48084,r2	! ffff640a
   4800c:	90 31       	mov.w	0x48072,r0	! f0
   4800e:	63 20       	mov.b	@r2,r3
   48010:	63 3c       	extu.b	r3,r3
   48012:	33 00       	cmp/eq	r0,r3
   48014:	8f 0f       	bf.s	0x48036
   48016:	00 09       	nop	
   48018:	b1 38       	bsr	0x4828c
   4801a:	00 09       	nop	
   4801c:	60 d3       	mov	r13,r0
   4801e:	84 01       	mov.b	@(1,r0),r0
   48020:	c9 01       	and	#1,r0
   48022:	88 01       	cmp/eq	#1,r0
   48024:	8f 04       	bf.s	0x48030
   48026:	00 09       	nop	
   48028:	84 d1       	mov.b	@(1,r13),r0
   4802a:	c9 fe       	and	#-2,r0
   4802c:	a0 03       	bra	0x48036
   4802e:	80 d1       	mov.b	r0,@(1,r13)
   48030:	d3 12       	mov.l	0x4807c,r3	! ffff6400
   48032:	b1 02       	bsr	0x4823a
   48034:	23 b0       	mov.b	r11,@r3
   48036:	2e b0       	mov.b	r11,@r14
   48038:	a0 12       	bra	0x48060
   4803a:	2c b0       	mov.b	r11,@r12
   4803c:	67 7c       	extu.b	r7,r7
   4803e:	60 73       	mov	r7,r0
   48040:	06 54       	mov.b	r5,@(r0,r6)
   48042:	e5 01       	mov	#1,r5
   48044:	63 c0       	mov.b	@r12,r3
   48046:	62 40       	mov.b	@r4,r2
   48048:	32 3c       	add	r3,r2
   4804a:	2c 20       	mov.b	r2,@r12
   4804c:	d3 0e       	mov.l	0x48088,r3	! 2534
   4804e:	43 0b       	jsr	@r3
   48050:	64 e0       	mov.b	@r14,r4
   48052:	64 03       	mov	r0,r4
   48054:	62 4c       	extu.b	r4,r2
   48056:	32 a7       	cmp/gt	r10,r2
   48058:	8f 01       	bf.s	0x4805e
   4805a:	00 09       	nop	
   4805c:	64 a3       	mov	r10,r4
   4805e:	2e 40       	mov.b	r4,@r14
   48060:	4f 26       	lds.l	@r15+,pr
   48062:	69 f6       	mov.l	@r15+,r9
   48064:	6a f6       	mov.l	@r15+,r10
   48066:	6b f6       	mov.l	@r15+,r11
   48068:	6c f6       	mov.l	@r15+,r12
   4806a:	6d f6       	mov.l	@r15+,r13
   4806c:	00 0b       	rts	
   4806e:	6e f6       	mov.l	@r15+,r14
   48070:	00 80       	.word 0x0080
   48072:	00 f0       	.word 0x00f0
   48074:	ff ff       	.word 0xffff
   48076:	64 08       	swap.b	r0,r4
   48078:	00 04       	mov.b	r0,@(r0,r0)
   4807a:	71 32       	add	#50,r1
   4807c:	ff ff       	.word 0xffff
   4807e:	64 00       	mov.b	@r0,r4
   48080:	ff ff       	.word 0xffff
   48082:	64 09       	swap.w	r0,r4
   48084:	ff ff       	.word 0xffff
   48086:	64 0a       	negc	r0,r4
   48088:	00 00       	.word 0x0000
   4808a:	25 34       	mov.b	r3,@-r5
   4808c:	2f e6       	mov.l	r14,@-r15
   4808e:	2f d6       	mov.l	r13,@-r15
   48090:	2f c6       	mov.l	r12,@-r15
   48092:	4f 22       	sts.l	pr,@-r15
   48094:	d5 4b       	mov.l	0x481c4,r5	! ffff63fc
   48096:	7f fc       	add	#-4,r15
   48098:	d4 4b       	mov.l	0x481c8,r4	! ffff63fa
   4809a:	dc 4c       	mov.l	0x481cc,r12	! ffff63fb
   4809c:	de 4c       	mov.l	0x481d0,r14	! ffff649a
   4809e:	66 40       	mov.b	@r4,r6
   480a0:	d3 4c       	mov.l	0x481d4,r3	! ffff63ff
   480a2:	66 6c       	extu.b	r6,r6
   480a4:	60 30       	mov.b	@r3,r0
   480a6:	60 0c       	extu.b	r0,r0
   480a8:	36 07       	cmp/gt	r0,r6
   480aa:	8f 4f       	bf.s	0x4814c
   480ac:	ed 00       	mov	#0,r13
   480ae:	96 86       	mov.w	0x481be,r6	! f012
   480b0:	60 60       	mov.b	@r6,r0
   480b2:	c9 5b       	and	#91,r0
   480b4:	26 00       	mov.b	r0,@r6
   480b6:	24 d0       	mov.b	r13,@r4
   480b8:	2c d0       	mov.b	r13,@r12
   480ba:	25 d0       	mov.b	r13,@r5
   480bc:	84 e1       	mov.b	@(1,r14),r0
   480be:	c9 fe       	and	#-2,r0
   480c0:	80 e1       	mov.b	r0,@(1,r14)
   480c2:	60 e0       	mov.b	@r14,r0
   480c4:	d2 44       	mov.l	0x481d8,r2	! ffff6403
   480c6:	c9 fe       	and	#-2,r0
   480c8:	d3 44       	mov.l	0x481dc,r3	! ffff6404
   480ca:	2e 00       	mov.b	r0,@r14
   480cc:	60 e0       	mov.b	@r14,r0
   480ce:	c9 fd       	and	#-3,r0
   480d0:	2e 00       	mov.b	r0,@r14
   480d2:	60 e0       	mov.b	@r14,r0
   480d4:	c9 fb       	and	#-5,r0
   480d6:	2e 00       	mov.b	r0,@r14
   480d8:	60 e0       	mov.b	@r14,r0
   480da:	c9 f7       	and	#-9,r0
   480dc:	2e 00       	mov.b	r0,@r14
   480de:	60 e0       	mov.b	@r14,r0
   480e0:	c9 ef       	and	#-17,r0
   480e2:	2e 00       	mov.b	r0,@r14
   480e4:	84 e1       	mov.b	@(1,r14),r0
   480e6:	c9 f7       	and	#-9,r0
   480e8:	80 e1       	mov.b	r0,@(1,r14)
   480ea:	22 d0       	mov.b	r13,@r2
   480ec:	23 d0       	mov.b	r13,@r3
   480ee:	d1 3c       	mov.l	0x481e0,r1	! ffff6402
   480f0:	d2 3c       	mov.l	0x481e4,r2	! ffff6400
   480f2:	21 d0       	mov.b	r13,@r1
   480f4:	84 e1       	mov.b	@(1,r14),r0
   480f6:	c9 fd       	and	#-3,r0
   480f8:	80 e1       	mov.b	r0,@(1,r14)
   480fa:	60 e3       	mov	r14,r0
   480fc:	22 d0       	mov.b	r13,@r2
   480fe:	60 00       	mov.b	@r0,r0
   48100:	c8 80       	tst	#-128,r0
   48102:	8f 06       	bf.s	0x48112
   48104:	00 09       	nop	
   48106:	60 e0       	mov.b	@r14,r0
   48108:	c9 bf       	and	#-65,r0
   4810a:	2e 00       	mov.b	r0,@r14
   4810c:	60 e0       	mov.b	@r14,r0
   4810e:	c9 df       	and	#-33,r0
   48110:	2e 00       	mov.b	r0,@r14
   48112:	60 e3       	mov	r14,r0
   48114:	60 00       	mov.b	@r0,r0
   48116:	c8 40       	tst	#64,r0
   48118:	00 29       	movt	r0
   4811a:	70 ff       	add	#-1,r0
   4811c:	60 0b       	neg	r0,r0
   4811e:	88 01       	cmp/eq	#1,r0
   48120:	8d 02       	bt.s	0x48128
   48122:	00 09       	nop	
   48124:	a0 83       	bra	0x4822e
   48126:	00 09       	nop	
   48128:	b0 b0       	bsr	0x4828c
   4812a:	00 09       	nop	
   4812c:	60 e3       	mov	r14,r0
   4812e:	84 01       	mov.b	@(1,r0),r0
   48130:	c9 01       	and	#1,r0
   48132:	88 01       	cmp/eq	#1,r0
   48134:	8f 04       	bf.s	0x48140
   48136:	00 09       	nop	
   48138:	84 e1       	mov.b	@(1,r14),r0
   4813a:	c9 fe       	and	#-2,r0
   4813c:	a0 77       	bra	0x4822e
   4813e:	80 e1       	mov.b	r0,@(1,r14)
   48140:	7f 04       	add	#4,r15
   48142:	4f 26       	lds.l	@r15+,pr
   48144:	6c f6       	mov.l	@r15+,r12
   48146:	6d f6       	mov.l	@r15+,r13
   48148:	a0 77       	bra	0x4823a
   4814a:	6e f6       	mov.l	@r15+,r14
   4814c:	36 00       	cmp/eq	r0,r6
   4814e:	8f 05       	bf.s	0x4815c
   48150:	67 50       	mov.b	@r5,r7
   48152:	66 73       	mov	r7,r6
   48154:	84 e1       	mov.b	@(1,r14),r0
   48156:	cb 02       	or	#2,r0
   48158:	a0 08       	bra	0x4816c
   4815a:	80 e1       	mov.b	r0,@(1,r14)
   4815c:	66 c0       	mov.b	@r12,r6
   4815e:	66 6c       	extu.b	r6,r6
   48160:	d0 21       	mov.l	0x481e8,r0	! ffff6492
   48162:	06 6c       	mov.b	@(r0,r6),r6
   48164:	2f 60       	mov.b	r6,@r15
   48166:	62 f0       	mov.b	@r15,r2
   48168:	37 2c       	add	r2,r7
   4816a:	25 70       	mov.b	r7,@r5
   4816c:	93 28       	mov.w	0x481c0,r3	! f013
   4816e:	23 60       	mov.b	r6,@r3
   48170:	95 27       	mov.w	0x481c2,r5	! f014
   48172:	60 50       	mov.b	@r5,r0
   48174:	c9 7f       	and	#127,r0
   48176:	cb 78       	or	#120,r0
   48178:	25 00       	mov.b	r0,@r5
   4817a:	d2 1c       	mov.l	0x481ec,r2	! ffff63f9
   4817c:	22 60       	mov.b	r6,@r2
   4817e:	61 40       	mov.b	@r4,r1
   48180:	71 01       	add	#1,r1
   48182:	24 10       	mov.b	r1,@r4
   48184:	60 c0       	mov.b	@r12,r0
   48186:	70 01       	add	#1,r0
   48188:	2c 00       	mov.b	r0,@r12
   4818a:	60 e3       	mov	r14,r0
   4818c:	84 01       	mov.b	@(1,r0),r0
   4818e:	c8 02       	tst	#2,r0
   48190:	8f 46       	bf.s	0x48220
   48192:	00 09       	nop	
   48194:	61 40       	mov.b	@r4,r1
   48196:	e0 05       	mov	#5,r0
   48198:	61 1c       	extu.b	r1,r1
   4819a:	31 07       	cmp/gt	r0,r1
   4819c:	8d 2a       	bt.s	0x481f4
   4819e:	00 09       	nop	
   481a0:	61 c0       	mov.b	@r12,r1
   481a2:	e3 04       	mov	#4,r3
   481a4:	61 1c       	extu.b	r1,r1
   481a6:	31 37       	cmp/gt	r3,r1
   481a8:	8f 41       	bf.s	0x4822e
   481aa:	00 09       	nop	
   481ac:	b1 a2       	bsr	0x484f4
   481ae:	2c d0       	mov.b	r13,@r12
   481b0:	d3 0f       	mov.l	0x481f0,r3	! 4728e
   481b2:	7f 04       	add	#4,r15
   481b4:	4f 26       	lds.l	@r15+,pr
   481b6:	6c f6       	mov.l	@r15+,r12
   481b8:	6d f6       	mov.l	@r15+,r13
   481ba:	43 2b       	jmp	@r3
   481bc:	6e f6       	mov.l	@r15+,r14
   481be:	f0 12       	fmul	fr1,fr0
   481c0:	f0 13       	fdiv	fr1,fr0
   481c2:	f0 14       	fcmp/eq	fr1,fr0
   481c4:	ff ff       	.word 0xffff
   481c6:	63 fc       	extu.b	r15,r3
   481c8:	ff ff       	.word 0xffff
   481ca:	63 fa       	negc	r15,r3
   481cc:	ff ff       	.word 0xffff
   481ce:	63 fb       	neg	r15,r3
   481d0:	ff ff       	.word 0xffff
   481d2:	64 9a       	negc	r9,r4
   481d4:	ff ff       	.word 0xffff
   481d6:	63 ff       	exts.w	r15,r3
   481d8:	ff ff       	.word 0xffff
   481da:	64 03       	mov	r0,r4
   481dc:	ff ff       	.word 0xffff
   481de:	64 04       	mov.b	@r0+,r4
   481e0:	ff ff       	.word 0xffff
   481e2:	64 02       	mov.l	@r0,r4
   481e4:	ff ff       	.word 0xffff
   481e6:	64 00       	mov.b	@r0,r4
   481e8:	ff ff       	.word 0xffff
   481ea:	64 92       	mov.l	@r9,r4
   481ec:	ff ff       	.word 0xffff
   481ee:	63 f9       	swap.w	r15,r3
   481f0:	00 04       	mov.b	r0,@(r0,r0)
   481f2:	72 8e       	add	#-114,r2
   481f4:	d3 4d       	mov.l	0x4832c,r3	! 471c8
   481f6:	43 0b       	jsr	@r3
   481f8:	00 09       	nop	
   481fa:	60 0c       	extu.b	r0,r0
   481fc:	20 08       	tst	r0,r0
   481fe:	8f 16       	bf.s	0x4822e
   48200:	00 09       	nop	
   48202:	e3 03       	mov	#3,r3
   48204:	62 c0       	mov.b	@r12,r2
   48206:	62 2c       	extu.b	r2,r2
   48208:	32 37       	cmp/gt	r3,r2
   4820a:	8f 10       	bf.s	0x4822e
   4820c:	00 09       	nop	
   4820e:	b1 71       	bsr	0x484f4
   48210:	2c d0       	mov.b	r13,@r12
   48212:	7f 04       	add	#4,r15
   48214:	d3 46       	mov.l	0x48330,r3	! 4728e
   48216:	4f 26       	lds.l	@r15+,pr
   48218:	6c f6       	mov.l	@r15+,r12
   4821a:	6d f6       	mov.l	@r15+,r13
   4821c:	43 2b       	jmp	@r3
   4821e:	6e f6       	mov.l	@r15+,r14
   48220:	d1 44       	mov.l	0x48334,r1	! 4717e
   48222:	7f 04       	add	#4,r15
   48224:	4f 26       	lds.l	@r15+,pr
   48226:	6c f6       	mov.l	@r15+,r12
   48228:	6d f6       	mov.l	@r15+,r13
   4822a:	41 2b       	jmp	@r1
   4822c:	6e f6       	mov.l	@r15+,r14
   4822e:	7f 04       	add	#4,r15
   48230:	4f 26       	lds.l	@r15+,pr
   48232:	6c f6       	mov.l	@r15+,r12
   48234:	6d f6       	mov.l	@r15+,r13
   48236:	00 0b       	rts	
   48238:	6e f6       	mov.l	@r15+,r14
   4823a:	d4 3f       	mov.l	0x48338,r4	! ffff6492
   4823c:	93 6c       	mov.w	0x48318,r3	! 80
   4823e:	65 43       	mov	r4,r5
