/*--------------------------------------------------------------------*/
/* SH C/C++ Compiler Ver. 9.0                                         */
/* Copyright (c) 2003, Renesas Technology Corporation and             */
/*                     Renesas Solutions Corporation                  */
/* All Rights Reserved.                                               */
/* Licensed material of Renesas Technology Corporation                */
/*--------------------------------------------------------------------*/
/**********************************************************************/
/* SPEC;                                                              */
/*   NAME = atan: double precision arctangent function;               */
/*   FUNC = Computes double precision arctangent of its argument;     */
/*   CLAS = UNIT;                                                     */
/*   NOTE = SH C/C++ fast floating point library;                     */
/* END;                                                               */
/**********************************************************************/
#if defined _FLT || defined _FPS        /* double=float or fpu=single */
#define atanf atan                      /* rename atanf to atan       */
#include "atanf.c"                      /* include tanf               */
#else

#include "fperror.h"                    /* FFPLB-024 (A)              */

/* Arctangent coefficient                                             */
static const double atand_coeff[11]={   /* FFPLB-008 (C)              */
  -1.5411449615035691e-02,              /* FFPLB-008 (C)              */
  3.5631002397392621e-02,               /* FFPLB-008 (C)              */
  -4.9369357446407101e-02,              /* FFPLB-008 (C)              */
  5.8235923311475972e-02,               /* FFPLB-008 (C)              */
  -6.6595317264949633e-02,              /* FFPLB-008 (C)              */
  7.6917240251518235e-02,               /* FFPLB-008 (C)              */
  -9.0908775510497905e-02,              /* FFPLB-008 (C)              */
  1.1111110033070735e-01,               /* FFPLB-008 (C)              */
  -1.4285714264201504e-01,              /* FFPLB-008 (C)              */
  1.9999999999784845e-01,               /* FFPLB-008 (C)              */
  -3.3333333333332582e-01};             /* FFPLB-008 (C)              */

static double poly_atand(double f0){
  double d2, d4, a1, a2;                /* FFPLB-008 (C)              */
  double *p=atand_coeff;
  d2=f0*f0;                             /* FFPLB-008 (C)              */
  d4=d2*d2;                             /* FFPLB-008 (C)              */
  a1=*p++;                              /* FFPLB-008 (C)              */
  a2=*p++;                              /* FFPLB-008 (C)              */
  a1*=d4;                               /* FFPLB-008 (C)              */
  a1+=*p++;                             /* FFPLB-008 (C)              */
  a2*=d4;                               /* FFPLB-008 (C)              */
  a2+=*p++;                             /* FFPLB-008 (C)              */
  a1*=d4;                               /* FFPLB-008 (C)              */
  a1+=*p++;                             /* FFPLB-008 (C)              */
  a2*=d4;                               /* FFPLB-008 (C)              */
  a2+=*p++;                             /* FFPLB-008 (C)              */
  a1*=d4;                               /* FFPLB-008 (C)              */
  a1+=*p++;                             /* FFPLB-008 (C)              */
  a2*=d4;                               /* FFPLB-008 (C)              */
  a2+=*p++;                             /* FFPLB-008 (C)              */
  a1*=d4;                               /* FFPLB-008 (C)              */
  a1+=*p++;                             /* FFPLB-008 (C)              */
  a2*=d4;                               /* FFPLB-008 (C)              */
  a2+=*p++;                             /* FFPLB-008 (C)              */
  a1*=d4;                               /* FFPLB-008 (C)              */
  a1+=*p++;                             /* FFPLB-008 (C)              */
  a2*=d4;                               /* FFPLB-008 (C)              */
  a2=a2+a1*d2;                          /* FFPLB-008 (C)              */
  f0=f0+a2*f0;                          /* FFPLB-008 (C)              */
  return f0;                            /* FFPLB-008 (C)              */
}

#define EXP_MASK 0x7FF00000             /* Mask of double exponent    */
#define SIGN_MASK 0x80000000            /* Mask of double sign        */
#define MANT_MASK 0x000FFFFF            /* Mask of double mantissa    */
                                        /* (upper half)               */

#define NAN_VALUE 0x7FF80000            /* Value of double NaN (upper */
                                        /* half)                      */

#define PI     3.1415926535897932

extern double __nand_value(void);

static double atand_special_case(unsigned long hi, unsigned long lo){
  double result;
  if (hi&MANT_MASK || lo!=0){           /* FFPLB-030 (C)              */
    _errno=EDOM;                        /* FFPLB-030 (A)              */
    return __nand_value();
  }                                     /* FFPLB-030 (A)              */
  else if (hi&SIGN_MASK){               /* Input is -infinity         */
    return -PI/2.0;
  }
  else                                  /* Input is +infinity         */
    return PI/2.0;
}

#define ATAN05 0.46364760900080612
#define ATAN1  (PI/4)
#define ATAN2  1.1071487177940905
#define ATAN5  1.3734007669450159

double atan(double d0){
#ifdef _BIG                             /* Big endian                 */
  if ((*(unsigned long *)&d0&EXP_MASK)==EXP_MASK){ /* FFPLB-024 (C)   */
                                        /* Check NaN or Infinity      */
    return atand_special_case(*(unsigned long *)&d0, /* FFPLB-030 (C) */
	                          *((unsigned long *)&d0+1));
							            /* FFPLB-030(C)               */
  }                                     /* FFPLB-024 (A)              */
#else                                   /* Little endian              */
  if ((*((unsigned long *)&d0+1)&EXP_MASK)==EXP_MASK){ /* FFPLB-024(C)*/
                                        /* Check NaN or Infinity      */
    return atand_special_case(*((unsigned long *)&d0+1),/*FFPLB-051(C)*/
	                          *(unsigned long *)&d0); /* FFPLB-051(C) */
							            /* FFPLB-030(C)               */
  }                                     /* FFPLB-024 (A)              */
#endif
  /* Dispatch by the range                                            */
  if (d0==0.0)                          /* Handle the cases of +-0    */
    return d0;
  if (d0>=0.0){
    if (d0<0.40)
      return poly_atand(d0);
    if (d0<0.72)
      return ATAN05+poly_atand((d0-0.5)/(1.0+0.5*d0));
    if(d0<1.4)
      return ATAN1+poly_atand((d0-1.0)/(1.0+d0));
    if(d0<3.0)
      return ATAN2+poly_atand((d0-2.0)/(1.0+2*d0));
    return ATAN5+poly_atand((d0-5.0)/(1.0+5*d0));
  }
  d0=-d0;
  if (d0<0.40)
    return -poly_atand(d0);
  if (d0<0.72)
    return -ATAN05-poly_atand((d0-0.5)/(1.0+0.5*d0));
  if(d0<1.4)
    return -ATAN1-poly_atand((d0-1.0)/(1.0+d0));
  if(d0<3.0)
    return -ATAN2-poly_atand((d0-2.0)/(1.0+2*d0));
  return -ATAN5-poly_atand((d0-5.0)/(1.0+5*d0));
}
#endif
