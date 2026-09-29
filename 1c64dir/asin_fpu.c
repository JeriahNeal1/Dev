/*--------------------------------------------------------------------*/
/* SH C/C++ Compiler Ver. 9.0                                         */
/* Copyright (c) 2003, Renesas Technology Corporation and             */
/*                     Renesas Solutions Corporation                  */
/* All Rights Reserved.                                               */
/* Licensed material of Renesas Technology Corporation                */
/*--------------------------------------------------------------------*/
/**********************************************************************/
/* SPEC;                                                              */
/*   NAME = asin: double precision arcsine function;                  */
/*   FUNC = Computes double precision arcsine of its argument;        */
/*   CLAS = UNIT;                                                     */
/*   NOTE = SH C/C++ fast floating point library;                     */
/* END;                                                               */
/**********************************************************************/
#if defined _FLT || defined _FPS        /* double=float or fpu=single */
#define asinf asin                      /* rename asinf to asin       */
#include "asinf.c"                      /* include asinf              */
#else

#include "fperror.h"                    /* FFPLB-024 (A)              */

/* Arcsine coefficient                                                */
static const double asind_coeff[12]={3.1761799008028509e-02,
                                     -1.5998442264688166e-02,
                                     1.9380699448302274e-02,
                                     6.5830649850293435e-03,
                                     1.2156256544304502e-02,
                                     1.3887231158013437e-02,
                                     1.7359501830608530e-02,
                                     2.2371771442767674e-02,
                                     3.0381958588206871e-02,
                                     4.4642856841146340e-02,
                                     7.5000000003225837e-02,
                                     1.6666666666665461e-01};

static double poly_asind(double f0)     /* FFPLB-042 (A)              */
{
  double d2,d4;
  double *p=asind_coeff;
  d2=f0*f0;
  d4=*p++;
  d4=*p++ +d4*d2;
  d4=*p++ +d4*d2;
  d4=*p++ +d4*d2;
  d4=*p++ +d4*d2;
  d4=*p++ +d4*d2;
  d4=*p++ +d4*d2;
  d4=*p++ +d4*d2;
  d4=*p++ +d4*d2;
  d4=*p++ +d4*d2;
  d4=*p++ +d4*d2;
  d4=*p++ +d4*d2;
  d4=1.0           +d4*d2;
  d4=d4*f0;
  return d4;
}

#define PI 3.1415926535897932

#define EXP_MASK 0x7FF00000             /* Mask of double exponent    */

extern double atan(double);
extern double sqrt(double);

extern double __nand_value(void);

double asin(double d0)
{
  double d3;
#ifdef _BIG                             /* Big endian                 */
  if ((*(unsigned long *)&d0&EXP_MASK)==EXP_MASK){ /* FFPLB-024 (C)   */
    _errno=EDOM;                        /* FFPLB-024 (A)              */
                                        /* Check NaN or Infinity      */
    return __nand_value();
  }                                     /* FFPLB-024 (A)              */
#else                                   /* Little endian              */
  if ((*((unsigned long *)&d0+1)&EXP_MASK)==EXP_MASK){ /* FFPLB-024(C)*/
    _errno=EDOM;                        /* FFPLB-024 (A)              */
                                        /* Check NaN or Infinity      */
    return __nand_value();
  }                                     /* FFPLB-024 (A)              */
#endif
  if (d0==0.0)                          /* Handle cases of +-0        */
    return d0;
  d3=d0;
  if (d0<0)
    d3=-d3;
  if (d3<0.5)
    return poly_asind(d0);
  if (d3>1.0){                          /* FFPLB-024 (C)              */
    _errno=EDOM;                        /* FFPLB-024 (A)              */
    return __nand_value();
  }                                     /* FFPLB-024 (A)              */
  d3=sqrt((1.0-d0)*(1.0+d0));
  if (d3==0.0){
    d3=PI/2.0;
    if (d0<0.0) d3=-d3;
    return d3;
  }
  return atan(d0/d3);
}
#endif
