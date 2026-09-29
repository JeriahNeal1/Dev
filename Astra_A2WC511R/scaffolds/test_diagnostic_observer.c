#include "diagnostic_observer.h"
#include <assert.h>
#include <stdio.h>
int main(void) {
 unsigned int p,n,prev,count=0;
 for(n=0;n<256;n++)for(prev=0;prev<256;prev++) {
  unsigned int expected=n<8?n:(n==8?0:prev);
  assert(a2wc_decode_nibble((uint8_t)n,(uint8_t)prev)==expected);count++;
 }
 for(p=0;p<256;p++) {
  struct a2wc_diag_input in={(uint8_t)p,(uint8_t)p,1,2,A2WC_FRESHNESS_UNKNOWN};
  struct a2wc_diag_output out=a2wc_observe(in);
  assert(out.target_nibble==(p>>4));assert(out.current_nibble==(p&15));
  assert(out.rejection_reasons&A2WC_FRESHNESS_UNPROVEN);
  assert(!!(out.rejection_reasons&A2WC_NOT_MATCHING_FIRST)==(p!=0x11));count+=4;
 }
 { struct a2wc_diag_input in={0x11,0x11,1,2,A2WC_FRESH};
   assert(a2wc_observe(in).rejection_reasons==0);count++;
   in.freshness=A2WC_STALE;assert(a2wc_observe(in).rejection_reasons&A2WC_DATA_STALE);count++;
   in.freshness=255;assert(a2wc_observe(in).rejection_reasons&A2WC_INVALID_FRESHNESS_INPUT);count++;
   in.packed_source=0x21;assert(a2wc_observe(in).rejection_reasons&A2WC_SOURCE_SNAPSHOT_DISAGREE);count++;
   in.update_latch=2;assert(a2wc_observe(in).rejection_reasons&A2WC_LATCH_NOT_ONE);count++;
   in.status_flags=0;assert(a2wc_observe(in).rejection_reasons&A2WC_STATUS02_CLEAR);count++;
 }
 printf("PASS %u host diagnostic-observer assertions; NOT an ECU binary/test.\n",count);
 return 0;
}
