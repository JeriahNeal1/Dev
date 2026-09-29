/*--------------------------------------------------------------------*/
/* SH C/C++ Compiler Ver. 9.0                                         */
/* Copyright (c) 2003, Renesas Technology Corporation and             */
/*                     Renesas Solutions Corporation                  */
/* All Rights Reserved.                                               */
/* Licensed material of Renesas Technology Corporation                */
/*--------------------------------------------------------------------*/
/**********************************************************************/
/* SPEC;                                                              */
/*   NAME = acosf: single precision arccosine function;               */
/*   FUNC = Computes single precision arccosine of its argument;      */
/*   CLAS = UNIT;                                                     */
/*   NOTE = SH C/C++ fast floating point library;                     */
/* END;                                                               */
/**********************************************************************/
#ifndef _FPD                            /* fpu!=double                */

#include <mathf.h>                      /* FFPLB-010 (A)              */

#include "fperror.h"                    /* FFPLB-024 (A)              */

#define PI 3.14159265358979f            /* FFPLB-010 (A)              */

extern const float __asinf_coeff[];     /* FFPLB-010 (A)              */

static float poly_asinf_neg(float d1, float d2, /* FFPLB-041 (A)      */
                     float*p, float big, /* FFPLB-013 (A)             */
					 float small, float bd1) /* FFPLB-013 (A)         */
{                                       /* FFPLB-013 (A)              */
  float fr5, fr6, fr7, fr8, d4, d3;     /* FFPLB-013 (A)              */
  d4=d2*d2;                             /* FFPLB-013 (A)              */
  d3=d2*d1;                             /* FFPLB-013 (A)              */
  big-=bd1;                             /* FFPLB-013 (A)              */
  big+=d1;                              /* FFPLB-013 (A)              */
  small+=big;                           /* FFPLB-013 (A)              */
  fr7=*p++;                             /* FFPLB-013 (A)              */
  fr6=*p++;                             /* FFPLB-013 (A)              */
  fr8=*p++;                             /* FFPLB-013 (A)              */
  fr8+=d4*fr7;                          /* FFPLB-013 (A)              */
  fr5=*p++;                             /* FFPLB-013 (A)              */
  fr7=*p++;                             /* FFPLB-013 (A)              */
  fr5+=d4*fr6;                          /* FFPLB-013 (A)              */
  fr7+=d4*fr8;                          /* FFPLB-013 (A)              */
  fr6=*p++;                             /* FFPLB-013 (A)              */
  fr8=*p++;                             /* FFPLB-013 (A)              */
  fr6+=d4*fr5;                          /* FFPLB-013 (A)              */
  fr8+=d4*fr7;                          /* FFPLB-013 (A)              */
  fr5=*p++;                             /* FFPLB-013 (A)              */
  fr7=*p++;                             /* FFPLB-013 (A)              */
  fr5+=d4*fr6;                          /* FFPLB-013 (A)              */
  fr7+=d4*fr8;                          /* FFPLB-013 (A)              */
  fr7+=d2*fr5;                          /* FFPLB-013 (A)              */
  small+=d3*fr7;                        /* FFPLB-013 (A)              */
  bd1+=small;                           /* FFPLB-013 (A)              */
  return bd1;                           /* FFPLB-013 (A)              */
}                                       /* FFPLB-013 (A)              */

extern float __nanf_value(void);        /* FFPLB-010 (A)              */

extern float __poly_acosf_neg(float, float, float, float);
                                        /* FFPLB-013 (C)              */
extern float __poly_acosf(float, float, float, float); /* FFPLB-013(C)*/

extern float __asincosf_const_tbl[];    /* FFPLB-010 (A)              */

static float acosf_special(float d0){   /* FFPLB-013 (C)              */
  if (d0==1.0f)                         /* FFPLB-013 (C)              */
    return 0.0f;                        /* FFPLB-013 (C)              */
  if (d0==-1.0f)                        /* FFPLB-013 (C)              */
    return PI;                          /* FFPLB-013 (C)              */
  else{                                 /* FFPLB-013 (C)              */
    _errno=EDOM;                        /* FFPLB-024 (A)              */
    return __nanf_value();              /* FFPLB-024 (C)              */
  }                                     /* FFPLB-024 (A)              */
}                                       /* FFPLB-010 (A)              */

float acosf(float d0)
{
  float d1, d3;                         /* FFPLB-010 (C)              */
  unsigned long u0;                     /* FFPLB-013 (A)              */
  float *p=__asincosf_const_tbl;        /* FFPLB-013 (A)              */
  float big, small;                     /* FFPLB-013 (A)              */
  u0=*(unsigned long*)&d0;              /* FFPLB-013 (C)              */
  if ((u0&0x7f800000)>=0x3f800000)      /* FFPLB-013 (C)              */
    return acosf_special(d0);           /* FFPLB-013 (C)              */
  d3=fabsf(d0);                         /* FFPLB-010 (C)              */
  small=*p++;                           /* FFPLB-013 (A)              */
  big=*p++;                             /* FFPLB-013 (A)              */
  if(d3<=0.71f)                         /* FFPLB-010 (C)              */
    return poly_asinf_neg(-d0, d0*d0, __asinf_coeff, /* FFPLB-013 (C) */
	                      big, small, big-d0); /* FFPLB-013 (C)       */
  d3=1.0f-d3;                           /* FFPLB-013 (C)              */
  d1=sqrtf(d3+d3);                      /* FFPLB-013 (C)              */
  if(d0>0.0f)                           /* FFPLB-010 (C)              */
    return __poly_acosf(d3, d1, 0.0f, 0.0f); /* FFPLB-013 (C)         */
  else                                  /* FFPLB-010 (C)              */
    return __poly_acosf_neg(d3, d1, big+big, small+small);
	                                    /* FFPLB-013 (C)              */
}

#else                                   /* fpu=double                 */
#define acos acosf                      /* Renames acos to acosf      */
#include "acos.c"                       /* Includes double arccosine  */
#endif
