/*--------------------------------------------------------------------*/
/* SH C/C++ Compiler Ver. 9.0                                         */
/* Copyright (c) 2003, Renesas Technology Corporation and             */
/*                     Renesas Solutions Corporation                  */
/* All Rights Reserved.                                               */
/* Licensed material of Renesas Technology Corporation                */
/*--------------------------------------------------------------------*/
/**********************************************************************/
/* SPEC;                                                              */
/*   NAME = coshf: single precision hyperbolic cosine function;       */
/*   FUNC = Computes single precision hyperbolic cosine of its        */
/*          argument;                                                 */
/*   CLAS = UNIT;                                                     */
/*   NOTE = SH C/C++ fast floating point library;                     */
/* END;                                                               */
/**********************************************************************/
#ifndef _FPD                            /* fpu!=double                */

#include <mathf.h>

#include "fperror.h"                    /* FFPLB-024 (A)              */

#define EXP_MASK 0x7f800000             /* FFPLB-024 (A)              */
#define MANT_MASK 0x007fffff            /* FFPLB-024 (A)              */

static const float cosh_coeff[6]={2.319125582979E-09f,
                                  2.738703701669E-07f,
                                  2.480735459526E-05f,
                                  1.388880057037E-03f,
                                  4.166667139621E-02f,
                                  0.5f};

static float poly_coshf(float d1)
{
  float *p=cosh_coeff;
  float d2;
  float ans;
  d2=d1*d1;
  ans=*p++;
  ans=*p++ +ans*d2;
  ans=*p++ +ans*d2;
  ans=*p++ +ans*d2;
  ans=*p++ +ans*d2;
  ans=*p++ +ans*d2;
  ans=1.0f +ans*d2; 
  return ans;
}

float expf(float);

float coshf(float d0){
  float d1=fabsf(d0);
  float result;                         /* FFPLB-024 (A)              */
  if(d1<2.5f)                           /* FFPLB-028 (C)              */
    return poly_coshf(d0);
  d1=expf(d1);
  result=0.5f*(d1+1.0f/d1);             /* FFPLB-024 (C)              */
  if ((*(unsigned long *)&result&EXP_MASK)==EXP_MASK) /* FFPLB-024 (A)*/
    if ((*(unsigned long *)&result&MANT_MASK)==0) /* FFPLB-024 (A)    */
	  _errno=ERANGE;                    /* FFPLB-024 (A)              */
    else                                /* FFPLB-024 (A)              */
	  _errno=EDOM;                      /* FFPLB-024 (A)              */
  return result;                        /* FFPLB-024 (A)              */
}

#else                                   /* fpu=double                 */
#define cosh coshf                      /* Renames cosh to coshf      */
#include "cosh.c"                       /* Includes double cosh       */
#endif
