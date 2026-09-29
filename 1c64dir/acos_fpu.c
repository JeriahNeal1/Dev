/*--------------------------------------------------------------------*/
/* SH C/C++ Compiler Ver. 9.0                                         */
/* Copyright (c) 2003, Renesas Technology Corporation and             */
/*                     Renesas Solutions Corporation                  */
/* All Rights Reserved.                                               */
/* Licensed material of Renesas Technology Corporation                */
/*--------------------------------------------------------------------*/
/**********************************************************************/
/* SPEC;                                                              */
/*   NAME = acos: double precision arccosine function;                */
/*   FUNC = Computes double precision arccosine of its argument;      */
/*   CLAS = UNIT;                                                     */
/*   NOTE = SH C/C++ fast floating point library;                     */
/* END;                                                               */
/**********************************************************************/
#if defined _FLT || defined _FPS        /* double=float or fpu=single */
#define acosf acos                      /* rename acosf to acos       */
#include "acosf.c"                      /* include acosf              */
#else

#include "fperror.h"                    /* FFPLB-024 (A)              */

#define EXP_MASK 0x7ff00000             /* FFPLB-024 (A)              */

#define PI 3.1415926535897932

static const double acosd_coeff[10]={   /* FFPLB-008 (A)              */
  4.2127311960877789e-05,
  5.6816541888565027e-05,
  1.5600540473396204e-04,
  3.8319613705626175e-04,
  9.8874133697038606e-04,
  2.6854086672933695e-03,
  7.8918167913052891e-03,
  2.6516504293920042e-02,
  1.1785113019776139e-01,
  1.4142135623730950e+00};

extern double sqrt(double);             /* FFPLB-008 (A)              */

static double poly_acos(double f0){     /* FFPLB-008 (A)              */
  double ans;                           /* FFPLB-008 (A)              */
  double d1=1.0-f0;                     /* FFPLB-008 (A)              */
  double*p=acosd_coeff;                 /* FFPLB-008 (A)              */
  ans=*p++;                             /* FFPLB-008 (A)              */
  ans=*p++ +d1*ans;                     /* FFPLB-008 (A)              */
  ans=*p++ +d1*ans;                     /* FFPLB-008 (A)              */
  ans=*p++ +d1*ans;                     /* FFPLB-008 (A)              */
  ans=*p++ +d1*ans;                     /* FFPLB-008 (A)              */
  ans=*p++ +d1*ans;                     /* FFPLB-008 (A)              */
  ans=*p++ +d1*ans;                     /* FFPLB-008 (A)              */
  ans=*p++ +d1*ans;                     /* FFPLB-008 (A)              */
  ans=*p++ +d1*ans;                     /* FFPLB-008 (A)              */
  ans=*p++ +d1*ans;                     /* FFPLB-008 (A)              */
  return ans*sqrt(d1);                  /* FFPLB-008 (A)              */
}

/* Table of PI/2-3200/2048, 3200/2048 (approx. PI/2)                  */
static const double pi2d_tbl[]={        /* FFPLB-011 (A)              */
  0.0082963267948966192,                /* FFPLB-011 (A)              */
  3200.0/2048.0};                       /* FFPLB-011 (A)              */

extern double asin(double);

extern double __nand_value(void);       /* FFPLB-018 (A)              */

double acos(double d0)
{
  double result;                        /* FFPLB-001 (C)              */
  double *p=pi2d_tbl;                   /* FFPLB-011 (C)              */
#ifdef _BIG                             /* Big endian                 */
  if ((*(unsigned long *)&d0&EXP_MASK)==EXP_MASK){ /* FFPLB-024 (A)   */
                                        /* FFPLB-024 (A)              */
	_errno=EDOM;                        /* FFPLB-024 (A)              */
    return __nand_value();              /* FFPLB-024 (A)              */
  }                                     /* FFPLB-024 (A)              */
#else                                   /* FFPLB-024 (A)              */
  if ((*((unsigned long *)&d0+1)&EXP_MASK)==EXP_MASK){ /* FFPLB-024(A)*/
                                        /* FFPLB-024 (A)              */
	_errno=EDOM;                        /* FFPLB-024 (A)              */
    return __nand_value();              /* FFPLB-024 (A)              */
  }                                     /* FFPLB-024 (A)              */
#endif
  if (d0>=0.8){                         /* FFPLB-018 (C)              */
    if (d0>1.0){                        /* FFPLB-024 (C)              */
	  _errno=EDOM;                      /* FFPLB-024 (A)              */
	  return __nand_value();            /* FFPLB-018 (A)              */
    }                                   /* FFPLB-024 (A)              */
    return poly_acos(d0);               /* FFPLB-008 (C)              */
  }                                     /* FFPLB-018 (A)              */
  result=asin(-d0);                     /* FFPLB-001 (A)              */
  result+=*p++;
  return result+*p;
}
#endif
