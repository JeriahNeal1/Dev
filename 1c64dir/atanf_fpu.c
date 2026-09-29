/*--------------------------------------------------------------------*/
/* SH C/C++ Compiler Ver. 9.0                                         */
/* Copyright (c) 2003, Renesas Technology Corporation and             */
/*                     Renesas Solutions Corporation                  */
/* All Rights Reserved.                                               */
/* Licensed material of Renesas Technology Corporation                */
/*--------------------------------------------------------------------*/
/**********************************************************************/
/* SPEC;                                                              */
/*   NAME = atanf: single precision arctangent function;              */
/*   FUNC = Computes single precision arctangent of its argument;     */
/*   CLAS = UNIT;                                                     */
/*   NOTE = SH C/C++ fast floating point library;                     */
/* END;                                                               */
/**********************************************************************/
#ifndef _FPD                            /* fpu!=double                */

#include <mathf.h>                      /* FFLB-010 (A)               */

#include "fperror.h"                    /* FFPLB-024 (A)              */

#define PI 3.14159265358979f

/* Arctangent coefficient                                             */
static const float atanf_coeff[9]={     /* FFPLB-010 (C)              */
  -0.001600787f,                        /* FFPLB-010 (C)              */
  0.010015802f,                         /* FFPLB-010 (C)              */
  -0.029422352f,                        /* FFPLB-010 (C)              */
  0.056095338f,                         /* FFPLB-010 (C)              */
  -0.082872588f,                        /* FFPLB-010 (C)              */
  0.109090988f,                         /* FFPLB-010 (C)              */
  -0.142551339f,                        /* FFPLB-010 (C)              */
  0.199975693f,                         /* FFPLB-010 (C)              */
  -0.333332592f};                        /* FFPLB-010 (C)              */

static float poly_atanf(float d1,       /* FFPLB-010 (C)              */
						float *offset)  /* FFPLB-010 (C)              */
{
  float fr5, fr6, fr7, fr8, d2, d4, *p; /* FFPLB-010 (C)              */
  d2=d1*d1;                             /* FFPLB-010 (C)              */
  d4=d2*d2;                             /* FFPLB-010 (C)              */
  p=atanf_coeff;                        /* FFPLB-010 (C)              */
  fr7=*p++;                             /* FFPLB-010 (C)              */
  fr6=*p++;                             /* FFPLB-010 (C)              */
  fr8=*p++;                             /* FFPLB-010 (C)              */
  fr8+=d4*fr7;                          /* FFPLB-010 (C)              */
  fr5=*p++;                             /* FFPLB-010 (C)              */
  fr7=*p++;                             /* FFPLB-010 (C)              */
  fr5+=d4*fr6;                          /* FFPLB-010 (C)              */
  fr7+=d4*fr8;                          /* FFPLB-010 (C)              */
  fr6=*p++;                             /* FFPLB-010 (C)              */
  fr8=*p++;                             /* FFPLB-010 (C)              */
  fr6+=d4*fr5;                          /* FFPLB-010 (C)              */
  fr8+=d4*fr7;                          /* FFPLB-010 (C)              */
  fr5=*p++;                             /* FFPLB-010 (C)              */
  fr7=*p++;                             /* FFPLB-010 (C)              */
  fr5+=d4*fr6;                          /* FFPLB-010 (C)              */
  fr7+=d4*fr8;                          /* FFPLB-010 (C)              */
  fr5*=d4;	                            /* FFPLB-010 (C)              */
  fr5+=d2*fr7;                          /* FFPLB-010 (C)              */
  d4=*offset++;		                    /* FFPLB-010 (C)              */
  d4+=d1*fr5;                           /* FFPLB-010 (C)              */
  d4+=d1;                               /* FFPLB-010 (C)              */
  d4+=*offset;                          /* FFPLB-010 (C)              */
  return d4;                            /* FFPLB-010 (C)              */
}

#define EXP_MASK 0x7F800000             /* Mask of float exponent     */
#define SIGN_MASK 0x80000000            /* Mask of float sign         */
#define MANT_MASK 0x007FFFFF            /* Mask of float mantissa     */

extern float __nanf_value(void);

static float atanf_special_case(unsigned long v){
  if (v&MANT_MASK){                     /* FFPLB-026 (C)              */
    _errno=EDOM;                        /* FFPLB-026 (A)              */
    return __nanf_value();
  }                                     /* FFPLB-026 (A)              */
  if (v&SIGN_MASK)                      /* Input is -infinity         */
    return -PI/2.0f;
  /* Input is +infinity         */
  return PI/2.0f;
}

#define PI2APPROX ((float)((int)(PI*1024)/2048.0f)) /* FFPLB-010 (A)  */
#define PI2ADJUST 4.838267923333e-04f   /* FFPLB-010 (A)              */

static const float const_tbl[6]={       /* FFPLB-010 (A)              */
  0,                                    /* FFPLB-010 (A)              */
  0,                                    /* FFPLB-010 (A)              */
  PI2ADJUST,                            /* FFPLB-010 (A)              */
  PI2APPROX,                            /* FFPLB-010 (A)              */
  -PI2ADJUST,                           /* FFPLB-010 (A)              */
  -PI2APPROX};                          /* FFPLB-010 (A)              */

float atanf(float d0)
{
  float d3;                             /* FFPLB-010 (A)              */
  float *p;                             /* FFPLB-010 (A)              */
  if (d0==0.0f)  /* Handle the cases of +-0 */           /* C S91093P */
    return d0;
  if (d0>0.0f)                                           /* C S91093P */
    d3=d0;                              /* FFPLB-050 (C)              */
  else                                  /* FFPLB-050 (C)              */
    d3=-d0;                             /* FFPLB-050 (C)              */
  if (d3<1.0f)                          /* FFPLB-025 (C)              */
    return poly_atanf(d0, &const_tbl[0]); /* FFPLB-010 (C)            */
  if (d3==1.0f)                         /* FFPLB-025 (A)              */
    if (d0>0.0f)                                         /* C S91093P */
	  return PI/4.0f;                   /* FFPLB-025 (A)              */
    else                                /* FFPLB-025 (A)              */
	  return -PI/4.0f;                  /* FFPLB-025 (A)              */
  if ((*(unsigned long *)&d0&EXP_MASK)==EXP_MASK){ /* FFPLB-024 (C)   */
    return atanf_special_case(*(unsigned long *)&d0);
  }                                     /* FFPLB-024 (A)              */
  p=&const_tbl[2];                      /* FFPLB-010 (C)              */
  if (d0>1.0f)                          /* FFPLB-010 (C)              */
    return poly_atanf(-1.0f/d0, &const_tbl[2]); /* FFPLB-010 (C)      */
  else                                  /* FFPLB-010 (C)              */
    return poly_atanf(-1.0f/d0, &const_tbl[4]); /* FFPLB-010 (C)      */
}

#else                                   /* fpu=double                 */
#define atan atanf                      /* Renames atan to atanf      */
#include "atan.c"                       /* Includes double arctangent */
#endif
