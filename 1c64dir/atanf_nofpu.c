/********************************************************************************/
/* Copyright (C) 1992,2007 Renesas Technology Corp. and Renesas Solutions Corp. */
/* All rights reserved.                                                         */
/********************************************************************************/
/*! \file atanf.c
 *  \brief FFlib atanf関数ファイル
 */

#include "common.h"

/*! atanf多項式係数 */
static const long coeffL[] = {
	0xFFCB8BA1,		/*	S31 * -0.001600787,	*/
	0x014832A3,		/*	S31 *  0.010015802,	*/
	0xFC3BE36D,		/*	S31 * -0.029422352,	*/
	0x072E21CD,		/*	S31 *  0.056095338,	*/
	0xF5646E59,		/*	S31 * -0.082872588,	*/
	0x0DF6B188,		/*	S31 *  0.109090988,	*/
	0xEDC0E0B3,		/*	S31 * -0.142551339,	*/
	0x1998CDB2,		/*	S31 *  0.199975693,	*/
	0xD5555B8E,		/*	S31 * -0.333332592,	*/
	0x6487ED5B,		/*	S31 *  (PI/2)*0.5	*/
};

/*! 多項式計算時の乗算定義 */
#define MUL(x,y) (dmuls_h(x,y)<<1)

/*--------------------------------------------------
 * 内部関数（プロトタイプ）
 *--------------------------------------------------*/
static long poly_atanL1(long d1, long d3, long e, long sign);			/* FFLIB B-011	*/
static long poly_atanL2(long d1, long d3, long e, long sign);			/* FFLIB B-011	*/
static unsigned long rev32(unsigned long m);							/* FFLIB B-011	*/

/*!
 *  \brief  atanf係数 多項式計算
 *  \param  d1   浮動小数点の小数部
 *  \param  d3   浮動小数点の仮数部(Q32固定小数点数)
 *  \param  e    指数
 *  \param  sign 符号
 *  \return  atanf値（long型）
 */
static long poly_atanL1(long d1, long d3, long e, long sign)			/* FFLIB B-011	*/
{
	long ans, d2;
	const long *p;

	p = coeffL;
	d2 = dmulu_h(d1, d1) << 1;
	ans = *p++;

#ifdef OPT_TYPE_SIZE
	/* ROMサイズ優先オプションを選択した場合は多項式計算をループにする */
	/* ただしコンパイラの最適化オプションでループ展開を選択した場合 */
	/* 展開される可能性がある */
	{
		unsigned short i;
		for( i = 8; i != 0; --i ){
			ans = *p++ + MUL(ans, d2);
		}
	}
#else
	ans = *p++ + MUL(ans, d2);
	ans = *p++ + MUL(ans, d2);
	ans = *p++ + MUL(ans, d2);
	ans = *p++ + MUL(ans, d2);
	ans = *p++ + MUL(ans, d2);
	ans = *p++ + MUL(ans, d2);
	ans = *p++ + MUL(ans, d2);
	ans = *p++ + MUL(ans, d2);
#endif
	ans =       MUL(ans, d2);
	ans = d3  + MUL(ans, d3);
	return __normalize(ans << 1, e, sign);								/* FFLIB B-011	*/
}

/*!
 *  \brief  atanf係数 多項式計算
 *  \param  d1   浮動小数点の小数部
 *  \param  d3   浮動小数点の仮数部(Q32固定小数点数)
 *  \param  e    指数
 *  \param  sign 符号
 *  \return  atanf値（long型）
 */
static long poly_atanL2(long d1, long d3, long e, long sign) /* d3,e: for padding */	/* FFLIB B-011	*/
{
	long ans, d2;
	const long *p;

	p = coeffL;
	d2 = dmulu_h(d1 , d1) << 1;
	ans = *p++;

#ifdef OPT_TYPE_SIZE
	/* ROMサイズ優先オプションを選択した場合は多項式計算をループにする */
	/* ただしコンパイラの最適化オプションでループ展開を選択した場合 */
	/* 展開される可能性がある */
	{
		unsigned short i;
		for( i = 8; i != 0; --i ){
			ans = *p++ + MUL(ans, d2);
		}
	}
#else
	ans = *p++ + MUL(ans, d2);
	ans = *p++ + MUL(ans, d2);
	ans = *p++ + MUL(ans, d2);
	ans = *p++ + MUL(ans, d2);
	ans = *p++ + MUL(ans, d2);
	ans = *p++ + MUL(ans, d2);
	ans = *p++ + MUL(ans, d2);
	ans = *p++ + MUL(ans, d2);
#endif
	ans =       MUL(ans, d2);
	ans = d1  + MUL(ans, d1);
	ans = *p - (ans >> 1);
	return __normalize(ans << 1, 1, sign);				/* FFLIB B-011	*/
}

static unsigned long rev32(unsigned long m)				/* FFLIB B-011	*/
{
	unsigned long t;
	unsigned long r;
	r = (unsigned long)0x80000000 / (m >> 16);
	r = (r - 2) << 16;
	t = -dmulu_h(r, m) << 1;
	r += dmulu_h(t, r);
	return r;
}

/*!
 *  \brief  atanf関数（ライブラリ）
 *  \param  d0  入力値
 * （代入の手間を省くため、float型をunsigned long型として受け取っている）
 *  \return  atanf値
 * （代入の手間を省くため、float型をunsigned long型として返している）
 *
 *<hr>
 *  \par 内部処理：
 */
unsigned long atanf(unsigned long d0)	/* FFLIB B-012 B-016 */
{
	unsigned long m;			/* 浮動小数点の仮数部(Q32固定小数点数)	*/
	unsigned long fpart;		/* 浮動小数点の小数部					*/
	long e;						/* 浮動小数点の指数部					*/

	/*! 浮動小数点の指数部と仮数部の切り出し				*/
	/*! →指数部の切り出し frexp_e()						*/
	e = frexp_e(d0);			/* -126～e～129				*/
	/*! →仮数部の切り出し frexp_m()						*/
	m = frexp_m(d0);			/* MSB=1のQ32固定小数点数	*/

	/*! 指数部のチェック */
	if( e <= 0 ){
		if( e < -11){
			/*! →指数部が-11未満の場合、値をそのまま返す		*/
			return (d0);				/* FFLIB B-016	*/
		}
		/*! →指数部が0以下の場合は直接多項式計算をする poly_atanL1()	*/
		/* 仮数部のうち小数点以下の数値を求める				*/
		m >>= 1;					/* 0mmmmmmmmmmmmm							*/
		fpart = m >> (-e);			/* 0.mmmmmmmmmmmm(e=0) 0.00mmmmmmmmmm(e=-2)	*/
		d0 = poly_atanL1(fpart, m, e, d0);
	}else{
		if( e > 31){
			/* NAN対応 */
			if( (e > 128) && ((m << 1) != 0) ){
				/*! →±NANの時は±NANを返す */
				_errno = EDOM;		/* FFLIB B-015	*/
				if( (long)d0 < 0 ){
					/* -NAN */
					d0 = MNS_NAN;
				}else{
					/* +NAN */
					d0 = PLS_NAN;
				}
				/*! →±∞の時はそのまま返す */
				return (d0);			/* FFLIB B-016	*/
			}
			m = 0;
			fpart = 0;
		}else{
			e = 1 - e;
			m = rev32(m);
			if( m == 0 ){
				m--;					/* m = 0xFFFFFFFF; */
			}
			m >>= 1;
			fpart = m >> (-e);
		}
		/*! →指数部が1以上の場合はpoly_atanL2()を呼び出す */
		d0 = poly_atanL2(fpart, m, e, d0); 
	}
	return (d0);						/* FFLIB B-016	*/
}
