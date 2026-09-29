/********************************************************************************/
/* Copyright (C) 1992 (1995 - 2011) Renesas Electronics Corporation and         */
/* Renesas Solutions Corp. All Rights Reserved.                                 */
/********************************************************************************/
/*! \file  common.h
 *  \brief FFlib用ヘッダファイル
 *  \note  ソースからはこのヘッダをインクルードし、\n
 *         このファイルで各環境(SH,H8,M16C,M32R)用のヘッダファイルをインクルードする
 */

#ifndef _FFLIB_H_
#define _FFLIB_H_


/*
**--------------------------------------------------
** ライブラリのビルドオプション
** OPT_TYPE_SIZE有効：サイズ最適化（対応：有り：多項式ループ化）
** OPT_TYPE_SPEED：スピード最適化（対応：有り：共通モジュールのインライン展開）
**--------------------------------------------------
*/
#define OPT_TYPE_SIZE
#define OPT_TYPE_SPEED

/*
**--------------------------------------------------
** モジュール共通定数定義
**--------------------------------------------------
*/
/*! 固定小数点変換用定数(Q32変換) */
#define S32			(65536.0f*65536.0f)

/*! 固定小数点変換用定数(Q31変換) */
#define S31			(65536.0f*32768.0f)

/*! 固定小数点変換用定数(Q30変換) */
#define S30			(32768.0f*32768.0f)



/*
**--------------------------------------------------
**マイコン別設定
**--------------------------------------------------
*/
/* マイコン別インクルードファイル			*/
/* 及び、コンパイラ別インライン展開の指定	*/
/* それぞれのマクロはコンパイラの暗黙宣言	*/
#ifdef _SH
	/* SH用(SHC) */
	#define INLINE static
	#pragma inline(integer, fraction, frexp_m, frexp_e)
	#pragma inline(in_sqrtf)
	#pragma inline(get_n, myfmod)
	#include "fflb_sh.h"
#else
#ifdef __H8__
	/* H8用(H8C) */
	#define INLINE __inline static
	#include "fflb_h8.h"
#else
#ifdef __M32R__
	/* M32R用(CC32R) */
	#define INLINE inline static
	#include "fflb_m32r.h"
	/* 但しCC32Rでインライン展開を有効にするには
	** 最適化レベルを４以上にする必要がある[-O4]
	*/
#else
#ifdef M16C
	/* M16C用(NC30) */
	#define INLINE inline
	#include "fflb_m16c.h"
#endif	/* M16C */
#endif	/* __M32R__ */
#endif	/* __H8__ */
#endif	/* _SH */

/*
**--------------------------------------------------
** FFlib関数（外部公開関数）
**--------------------------------------------------
*/
unsigned long sinf( unsigned long );	/* FFLIB B-012 B-016	*/
unsigned long cosf( unsigned long );	/* FFLIB B-012 B-016	*/
unsigned long expf( unsigned long );	/* FFLIB B-012 B-016	*/
unsigned long logf( unsigned long );	/* FFLIB B-012 B-016	*/
#if defined(_SH2E)|defined(_SH3E)|defined(_SH4)|defined(_SH4A)|defined(_SH2AFPU)	/* BSH030 */
float sqrtf( float );
#else
unsigned long sqrtf( unsigned long );	/* FFLIB B-012 B-016	*/
#endif
unsigned long tanf( unsigned long );	/* FFLIB B-012 B-016	*/
unsigned long atanf( unsigned long );	/* FFLIB B-012 B-016	*/

/*
**--------------------------------------------------
** 内部関数（プロトタイプ）
**--------------------------------------------------
*/
/* sin/cosメイン処理 */
long __insinL(unsigned long phase, unsigned long m, long e, unsigned long d0);					/* FFLIB B-011	*/
/* sin係数 多項式計算 */
long __poly_sinL(long d0, long d3, long e, long sign);											/* FFLIB B-011	*/
/* cos係数 多項式計算 */
long __poly_cosL(long d1, long e, long sign);													/* FFLIB B-011	*/

/* ------ normalize and round ------------------------ */
long __myround(unsigned long m2, long e4, long sign); 		/* mant, exp, sign				*/	/* FFLIB B-011	*/
long __rtn_inf(unsigned long r5);							/* sign							*/	/* FFLIB B-011	*/
long __normalize(unsigned long m, long e, long sign);		/* mant, exp, sign				*/	/* FFLIB B-011	*/
long __normalize1(unsigned long r2, long r4, long r5);		/* mant, exp, sign				*/	/* FFLIB B-011	*/
long __denorm(unsigned long r2, long r4, long r5);			/* construct denormalized num.	*/	/* FFLIB B-011	*/

#ifdef OPT_TYPE_SPEED
/*
**--------------------------------------------------
** 内部関数（インライン展開 or static）
**--------------------------------------------------
*/
/* 前置のINLINEは環境によりinlineやstaticに置き代わる */
/*!
 *  \brief  擬似double値の整数部取得関数
 *  \param  u  Q32固定小数点数
 *  \param  e  指数
 *  \return    整数値
 *  \note  引数をu*2^eとして、そのうちの整数部分を求めて戻り値とする\n
 *  整数部分が0の場合は0を返す  eが33以上の場合は不定\n
 */
INLINE unsigned long integer(unsigned long u, long e)
{
	if(e <= 0){
		return (0);
	}else{
		return (u >> (32 - e));
	}
}
/*!
 *  \brief  擬似double値の小数部取得関数
 *  \param  u  Q32固定小数点数
 *  \param  e  指数部
 *  \return    Q32固定小数点数
 *
 *  引数をu*2^nとして、そのうちの少数部分を求めて\n
 *  固定小数点数として戻り値とする\n
 *  eが32以上の場合は不定\n
 *  eが-32以上の場合は不定\n
 */
INLINE unsigned long fraction(unsigned long u, long e)
{
	if(e < 0){
		return (u >> (-e));
	}else{
		return (u << e);
	}
}
/*!
 *  \brief  float型のデータから仮数部を切り出す
 *  \param  f  元のデータ（I/Fはunsigned longだが中身はfloat）
 *  \return  切り出した仮数部
 *  \note   仮数部のMSBは必ず１\n
 *  - 仮数部(return)\n
 *  MSB  .  .  ... b8  b7  b6  ...  .  LSB\n
 *   1   m  m  ...  m   0   0  ...  0   0
 */
INLINE unsigned long frexp_m(unsigned long f)
{
	return (0x80000000 | (f << 8));
}
/*!
 *  \brief  float型のデータから指数部を切り出す
 *  \param  f  元のデータ（I/Fはunsigned longだが中身はfloat）
 *  \return  切り出した指数部
 *  \note   戻り値の値域は-126～129\n
 *  - 指数部\n
 *  MSB  ...  b1 LSB\n
 *   s   ...  n   n
 */
INLINE long frexp_e(unsigned long f)
{
	return ((long)((f << 1) >> 24) - 126);
}

#ifdef __H8__
/*!
 *  \brief  32b.+.32b+.32b処理
 *  \param  *i     Q0整数
 *  \param  *fpart Q32固定小数点数
 *  \param  adder  Q32固定小数点数
 *  \note   加算後の小数部はfpartに入る
 */
INLINE void __addc3( long *i, unsigned long *fpart, unsigned long adder)
{
/*   input  &iiii.       */
/*   input       .&fpart */
/* + input       .adder  */
/* --------------------- */
/*             +c        */
/*   output &iiii.       */
/*   return      .&fpart */

	if( *fpart + adder < *fpart ){
		*i = *i + 1;
	}
	*fpart = *fpart + adder;
}

/*!
 *  \brief  固定小数点用正規化関数
 *  \param  m  非正規化固定小数点数ポインタ
 *  \param  e  指数値を格納するポインタ
 *
 * 引数mをMSBが1となるように正規化する\n
 * 引数eには正規化した際の指数をセットする
 */
INLINE void __fixed_normalize( unsigned long *m, short *e )
{
	while( (long)*m > 0 ){		/* MSB = 0なら繰り返す		*/
		*e = *e - 1;			/* 指数は-1する				*/
		*m = *m << 1;			/* 固定小数点数を左シフト	*/
	}
}

/*!
 *  \brief  64b(32b.32b)の論理左１ビットシフト処理
 *  \param  *i     Q0整数
 *  \param  *fpart Q32固定小数点数
 *  \note   fpartのMSBがiのLSBに入る
 */
INLINE void __shll64( long *i, unsigned long *fpart)
{
/*   input  &iiii.       */
/*   input       .&fpart */
/* <<1                   */
/* --------------------- */
/*                       */
/*  output &iiiic.       */
/*  output       .&fpart */

	*i = (*i << 1) | (*fpart >> 31);
	*fpart <<= 1;
}
#endif		/* __H8__ */

#else	/* OPT_TYPE_SPEED */

#ifdef __H8__
/* 32b.+.32b+.32b処理 */
void __addc3( long *i, unsigned long *fpart, unsigned long adder);

/* 固定小数点用正規化関数 */
void __fixed_normalize( unsigned long *m, short *e );

/* 64b(32b.32b)の論理左１ビットシフト処理 */
void __shll64( long *i, unsigned long *fpart);
#endif	/* __H8__ */

unsigned long __integer(short e, unsigned long u);
unsigned long __fraction(short e, unsigned long u);
unsigned long __frexp_m(unsigned long f);
short __frexp_e(unsigned long f);
#endif		/* OPT_TYPE_SPEED */

#ifdef __H8__
/* no inline */
/* 64b-96b */
unsigned long __sub96( unsigned long *dw_1i, unsigned long *dw_1f, unsigned long dw_2i, unsigned long dw_2f, unsigned long dw_2ff);
#endif	/* __H8__ */

#endif		/* _FFLIB_H_ */
