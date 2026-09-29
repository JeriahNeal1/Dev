/*--------------------------------------------------------------------*/
/* SH C/C++ Compiler Ver. 9.0                                         */
/* Copyright (c) 2003, Renesas Technology Corporation and             */
/*                     Renesas Solutions Corporation                  */
/* All Rights Reserved.                                               */
/* Licensed material of Renesas Technology Corporation                */
/*--------------------------------------------------------------------*/
/**********************************************************************/
/* SPEC;                                                              */
/*   NAME = cosf: double precision hyperbolic cosine function;        */
/*   FUNC = Computes double precision hyperbolic cosine of its        */
/*          argument;                                                 */
/*   CLAS = UNIT;                                                     */
/*   NOTE = SH C/C++ fast floating point library;                     */
/* END;                                                               */
/**********************************************************************/
#if defined _FLT || defined _FPS        /* double=float or fpu=single */
#define coshf cosh                      /* rename coshf to cosh       */
#include "coshf.c"                      /* include coshf              */
#else

#include "fperror.h"                    /* FFPLB-024 (A)              */

#define EXP_MASK 0x7ff00000             /* FFPLB-024 (A)              */
#define MANT_MASK 0x000fffff            /* FFPLB-024 (A)              */

static const double cosh_coeff[7]={1.1659189193300430e-11,
                                   2.0873768732701969e-09,
                                   2.7557343693470997e-07,
                                   2.4801587191852433e-05,
                                   1.3888888889151032e-03,
                                   4.1666666666663712e-02,
                                   5.0000000000000011e-01};


static double poly_cosh(double d1)      /* FFPLB-015 (C)              */
{
  double d2, d4;
  double *p=cosh_coeff;
  d2=d1*d1;
  d4=*p++;
  d4=*p++ +d4*d2;
  d4=*p++ +d4*d2;
  d4=*p++ +d4*d2;
  d4=*p++ +d4*d2;
  d4=*p++ +d4*d2;
  d4=*p++ +d4*d2;
  d4=1.0  +d4*d2;
  return d4;
}

double exp(double);

double cosh(double d0){
  double d1=d0;
  double result;                        /* FFPLB-024 (A)              */
  if (d0<0.0)
    d1=-d0;
  if(d1<1.0)                            /* FFPLB-031 (C)              */
    return poly_cosh(d0);
  d1=exp(d1);
  result=0.5*(d1+1.0/d1);               /* FFPLB-024 (C)              */
#ifdef _BIG                             /* FFPLB-024 (A)              */
  if ((*(unsigned long *)&result&EXP_MASK)==EXP_MASK) /*FFPLB-024 (A) */
                                        /* FFPLB-024 (A)              */
    if ((*(unsigned long *)&result&MANT_MASK)!=0 || /* FFPLB-024 (A)  */
	    *((unsigned long *)&result+1)!=0)   /* FFPLB-024 (A)          */
	  _errno=EDOM;                      /* FFPLB-024 (A)              */
    else                                /* FFPLB-024 (A)              */
	  _errno=ERANGE;                    /* FFPLB-024 (A)              */
#else                                   /* FFPLB-024 (A)              */
  if ((*((unsigned long *)&result+1)&EXP_MASK)==EXP_MASK)
                                        /* FFPLB-024 (A)              */
    if ((*((unsigned long *)&result+1)&MANT_MASK)!=0 || /*FFPLB-024(A)*/
	    *(unsigned long *)&result!=0)   /* FFPLB-024 (A)              */
      _errno=EDOM;                      /* FFPLB-024 (A)              */
    else                                /* FFPLB-024 (A)              */
	  _errno=ERANGE;                    /* FFPLB-024 (A)              */
#endif                                  /* FFPLB-024 (A)              */
  return result;                        /* FFPLB-024 (A)              */
}
#endif
