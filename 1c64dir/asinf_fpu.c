/*--------------------------------------------------------------------*/
/* SH C/C++ Compiler Ver. 9.0                                         */
/* Copyright (c) 2003, Renesas Technology Corporation and             */
/*                     Renesas Solutions Corporation                  */
/* All Rights Reserved.                                               */
/* Licensed material of Renesas Technology Corporation                */
/*--------------------------------------------------------------------*/
/**********************************************************************/
/* SPEC;                                                              */
/*   NAME = asinf: single precision arcsine function;                 */
/*   FUNC = Computes single precision arcsine of its argument;        */
/*   CLAS = UNIT;                                                     */
/*   NOTE = SH C/C++ fast floating point library;                     */
/* END;                                                               */
/**********************************************************************/

#ifndef _FPD                            /* fpu!=double                */

#include <mathf.h>                      /* For fabsf and sqrt         */

#include "fperror.h"                    /* FFPLB-024 (A)              */

#define PI 3.14159265358979f

extern const float __asinf_coeff[];     /* FFPLB-010 (C)              */

static float poly_asinf(float d1, float d2, float *p){ /* FFPLB-013(C)*/
  float fr5, fr6, fr7, fr8, d4, d3;     /* FFPLB-013 (C)              */
  d4=d2*d2;                             /* FFPLB-013 (C)              */
  d3=d2*d1;                             /* FFPLB-013 (C)              */
  fr7=*p++;                             /* FFPLB-013 (C)              */
  fr6=*p++;                             /* FFPLB-013 (C)              */
  fr8=*p++;                             /* FFPLB-013 (C)              */
  fr8+=d4*fr7;                          /* FFPLB-013 (C)              */
  fr5=*p++;                             /* FFPLB-013 (C)              */
  fr7=*p++;                             /* FFPLB-013 (C)              */
  fr5+=d4*fr6;                          /* FFPLB-013 (C)              */
  fr7+=d4*fr8;                          /* FFPLB-013 (C)              */
  fr6=*p++;                             /* FFPLB-013 (C)              */
  fr8=*p++;                             /* FFPLB-013 (C)              */
  fr6+=d4*fr5;                          /* FFPLB-013 (C)              */
  fr8+=d4*fr7;                          /* FFPLB-013 (C)              */
  fr5=*p++;                             /* FFPLB-013 (C)              */
  fr7=*p++;                             /* FFPLB-013 (C)              */
  fr5+=d4*fr6;                          /* FFPLB-013 (C)              */
  fr7+=d4*fr8;                          /* FFPLB-013 (C)              */
  fr7+=d2*fr5;                          /* FFPLB-013 (C)              */
  d1+=d3*fr7;	                        /* FFPLB-013 (C)              */
  return d1;                            /* FFPLB-013 (C)              */
}

extern float __nanf_value(void);        /* FFPLB-002 (C)              */

extern float __poly_acosf_neg(float, float, float, float);
                                        /* FFPLB-010 (C)              */
extern float __poly_acosf(float, float, float, float); /* FFPLB-010(A)*/

extern float __asincosf_const_tbl[];    /* FFPLB-010 (A)              */

static float asinf_special(float d0){   /* FFPLB-010 (A)      */
  if (d0==1.0f)                         /* FFPLB-013 (C)              */
    return PI/2.0f;                     /* FFPLB-013 (C)              */
  if (d0==-1.0f)                        /* FFPLB-013 (C)              */
    return -PI/2.0f;                    /* FFPLB-013 (C)              */
  else{                                 /* FFPLB-024 (C)              */
    _errno=EDOM;                        /* FFPLB-024 (A)              */
    return __nanf_value();              /* FFPLB-024 (C)              */
  }                                     /* FFPLB-024 (A)              */
}                                       /* FFPLB-010 (A)              */

float asinf(float d0)
{
  float d1, d3;                         /* FFPLB-013 (A)              */
  unsigned long u0;                     /* FFPLB-013 (A)              */
  float *p=__asincosf_const_tbl;        /* FFPLB-013 (A)              */
  float big, small;                     /* FFPLB-013 (A)              */
  u0=*(unsigned long*)&d0;              /* FFPLB-013 (C)              */
  if ((u0&0x7f800000)>=0x3f800000)      /* FFPLB-013 (C)              */
    return asinf_special(d0);           /* FFPLB-013 (C)              */
  if (d0==0.0f)                         /* Handle cases of +-0        */
    return d0;
  d3=fabsf(d0);
  if (d3<0.71f)
    return poly_asinf(d0, d0*d0, __asinf_coeff); /* FFPLB-013 (C)     */
  d3=1.0f-d3;                           /* FFPLB-013 (A)              */
  d1=sqrtf(d3+d3);                      /* FFPLB-013 (A)              */
  small=*p++;                           /* FFPLB-013 (C)              */
  big=*p++;                             /* FFPLB-013 (C)              */
  if (d0>0.0f)                          /* FFPLB-010 (C)              */
    return __poly_acosf_neg(d3, d1, big, small); /* FFPLB-013 (C)     */
  else                                  /* FFPLB-010 (C)              */
    return __poly_acosf(d3, d1, -big, -small); /* FFPLB-013 (C)       */
}

#else                                   /* fpu=double                 */
#define asin asinf                      /* Renames asin to asinf      */
#include "asin.c"                       /* FFPLB-043 (C)              */
#endif
