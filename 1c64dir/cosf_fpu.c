/*--------------------------------------------------------------------*/
/* SH C/C++ Compiler Ver. 9.0                                         */
/* Copyright (c) 2003, Renesas Technology Corporation and             */
/*                     Renesas Solutions Corporation                  */
/* All Rights Reserved.                                               */
/* Licensed material of Renesas Technology Corporation                */
/*--------------------------------------------------------------------*/
/**********************************************************************/
/* SPEC;                                                              */
/*   NAME = cosf: single precision cosine function;                   */
/*   FUNC = Computes single precision cosine of its argument;         */
/*   CLAS = UNIT;                                                     */
/*   NOTE = SH C/C++ fast floating point library;                     */
/* END;                                                               */
/**********************************************************************/
#ifndef _FPD                            /* fpu!=double                */

#include <mathf.h>

#include "fperror.h"                    /* FFPLB-024 (A)              */

extern float __internal_sincosf(float, int);
extern float __poly_cosf(float, float); /* FFPLB-010 (C)              */

float cosf(float d2){
  float d1=fabsf(d2);
  if (d1<1.0f)
    return __poly_cosf(d1, d2*d2);      /* FFPLB-010 (C)              */
  return __internal_sincosf(d1, 2);
}

#else                                   /* fpu=double                 */
#define cos cosf                        /* Renames cos to cosinf      */
#include "cos.c"                        /* Includes double cosine     */  
#endif
