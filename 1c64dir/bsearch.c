/********************************************************************************/
/* Copyright (C) 1992,2006 Renesas Technology Corp. and Renesas Solutions Corp. */
/* All rights reserved.                                                         */
/********************************************************************************/
/*****************************************************************/
/* SPEC ;                                                        */
/*   NAME = bsearch :                                            */
/*   FUNC = this module do the following function ;              */
/*                                                               */
/*         (1) search an array of nmemb objects ;                */
/*                                                               */
/*                                                               */
/*   CLAS = UNIT ;                                               */
/*   END ;                                                       */
/*****************************************************************/

                                                   /* D S01006SP */
#include "h2lfun.h"
#include "lstdlib.h"
#include "ebsearc.h"
void *bsearch(key,base,nmemb,size,compar)
const void *key,*base;
size_t nmemb;
size_t size;
int (*compar)(const void*,const void*);
{
     size_t low,high,mid;
     int    cond;

     low=1;
     high=nmemb;
     while ((1<=low)&&(low<=high)){
         mid=(high-low)/2+low;
         cond=(*compar)(key,((char *)base+(mid-1)*size));
         if (cond<0)  high=mid-1;
         if (cond>0)  low=mid+1;
         if (cond==0) return((char *)base+(mid-1)*size);
     }
     return(NULL);
}
