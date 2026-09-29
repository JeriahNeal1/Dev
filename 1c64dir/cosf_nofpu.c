/********************************************************************************/
/* Copyright (C) 1992,2007 Renesas Technology Corp. and Renesas Solutions Corp. */
/* All rights reserved.                                                         */
/********************************************************************************/
/*! \file cosf.c
 *  \brief FFlib cosf関数ファイル
 */

#include "common.h"


/*!
 *  \brief  cosf関数（ライブラリ）
 *  \param  d0  入力値
 * （代入の手間を省くため、float型をunsigned long型として受け取っている）
 *  \return  cosf値
 * （代入の手間を省くため、float型をunsigned long型として返している）
 *
 *<hr>
 *  \par 内部処理：
 */
unsigned long cosf(unsigned long d0)	/* FFLIB B-012 B-016 */
{	
	unsigned long m;			/* 浮動小数点の仮数部(Q32固定小数点数)	*/
	unsigned long fpart;		/* 浮動小数点の小数部					*/
	long e;						/* 浮動小数点の指数部					*/

	/*! 浮動小数点の指数部と仮数部の切り出し				*/
	/*! →指数部の切り出し frexp_e()						*/
	e = frexp_e( d0 );			/* -126～e～129				*/
	/*! →仮数部の切り出し frexp_m()						*/
	m = frexp_m( d0 );			/* MSB=1のQ32固定小数点数	*/

	/*! 指数部のチェック */
	if( e <= 0 ){
		if( e < -16 ){
			/*! →指数部が-16未満の場合、１を返す「cos(x)=1 ±x≒0」*/
			/* return 1.0f; */
			d0 = 0x3F800000;
		}else{
			/*! →指数部が０以下の場合は直接多項式計算をする __poly_cosL() */
			/* 仮数部のうち小数点以下の数値を求める */
			m >>= 1;					/* 0mmmmmmmmmmmmm							*/
			fpart = m >> (-e);			/* 0.mmmmmmmmmmmm(e=0) 0.00mmmmmmmmmm(e=-2)	*/
			/* 0は「cos(x)=+X ±x≒0」cos(x)が正数になるため						*/
			d0 = 0;
			d0 = __poly_cosL((long)fpart, e, (long)d0);	/* FFLIB B-011	*/
		}
	}else{
		/*! →指数部が１以上の場合内部関数を呼ぶ __insinL() */
		/*! 　(異常値チェックは内部関数で行なっている)      */

		/* cos(x)は n = 2 */
		d0 = __insinL( 2, m, e, d0 );								/* FFLIB B-011	*/
	}
	return (d0);						/* FFLIB B-016	*/
}
