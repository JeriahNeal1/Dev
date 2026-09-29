/******************************************************************************
*                                                             \  ___  /       *
*                                                               /   \         *
* Edison Design Group C++  Runtime                           - | \^/ | -      *
*                                                               \   /         *
* Proprietary information of Edison Design Group Inc.         /  | |  \       *
* Copyright 1992-1994 Edison Design Group Inc.                   [_]          *
*                                                                             *
******************************************************************************/
/*

Declarations relating to dtor_list.c -- destruction list processing.

*/

#ifndef DTOR_LIST_H
#define DTOR_LIST_H 1

#ifndef MAIN_H
#include "main.h"
#endif /* ifndef MAIN_H */

/*
Data structure used to build a list of static object destructions
to be performed at the end of execution.  Entries are added to the
list each time a static object is created.  New objects are added
to the front of the list.
*/
typedef struct a_needed_destruction *a_needed_destruction_ptr;
typedef struct a_needed_destruction {
  a_needed_destruction_ptr
		next;
			/* Pointer to the next entry in the list. */
  void		*object;
			/* Pointer to the object to be destroyed if this
			   is a "simple" destruction, or a NULL pointer
		 	   if this is a "complex" destruction.  A simple
			   destruction is one that can be done with
			   a single call to the destructor passing an
			   object pointer and a destruction flag. */
  a_void_function_ptr
		destruction_routine;
			/* For a simple destruction, this points to the
			   destructor to be called. For a complex destruction,
                           this is a pointer to a function that when called,
                           will call the necessary destructors. */
} a_needed_destruction;

extern void __process_needed_destructions(void);

EXTERN_C void __record_needed_destruction(a_needed_destruction_ptr ndp);

#endif /* DTOR_LIST_H */


/******************************************************************************
*                                                             \  ___  /       *
*                                                               /   \         *
* Edison Design Group C++  Runtime                           - | \^/ | -      *
*                                                               \   /         *
* Proprietary information of Edison Design Group Inc.         /  | |  \       *
* Copyright 1992-1994 Edison Design Group Inc.                   [_]          *
*                                                                             *
******************************************************************************/
