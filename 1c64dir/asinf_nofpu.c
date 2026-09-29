/********************************************************************************/
/* Copyright (C) 1992,2006 Renesas Technology Corp. and Renesas Solutions Corp. */
/* All rights reserved.                                                         */
/********************************************************************************/
/******************************************************************/
/* SPEC;                                                          */
/*   NAME = asin : arcsin value output ;                          */
/*   FUNC = asin : output IEEE double format ;                    */
/*   CLAS = UNIT ;                                                */
/*   NOTE = SHC floating point library ;                          */
/* END;                                                           */
/******************************************************************/
#ifndef _FPD					    /* A S50001SP */

#include "fdefs.h"
#include "fexts.h"
float asinf(p)
float p;
{
    float ret;
    ret=_istos(_in_asins(_stois(p)));
    if (isEMAXf(ret)){
        if (isMANTf(ret)){
            _errno = EDOM;
        }
        else {
            _errno = ERANGE;
        }
    }
    return ret;
}

#else						    /* A S50001SP */
#define asin asinf     				    /* A S50001SP */
#include "asin.c"				    /* A S50001SP */
#endif						    /* A S50001SP */
