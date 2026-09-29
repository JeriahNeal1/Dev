#include "diagnostic_observer.h"
uint8_t a2wc_decode_nibble(uint8_t nibble,uint8_t previous) {
 if (nibble < 8u) return nibble;
 if (nibble == 8u) return 0u;
 return previous; /* Mirrors the observed decoder's hold behavior; NOT freshness. */
}
struct a2wc_diag_output a2wc_observe(struct a2wc_diag_input in) {
 struct a2wc_diag_output out;
 out.target_nibble=(uint8_t)((in.packed_snapshot>>4)&15u);
 out.current_nibble=(uint8_t)(in.packed_snapshot&15u);
 out.rejection_reasons=0u;
 if(in.packed_snapshot!=0x11u)out.rejection_reasons|=A2WC_NOT_MATCHING_FIRST;
 if(in.update_latch!=1u)out.rejection_reasons|=A2WC_LATCH_NOT_ONE;
 if((in.status_flags&2u)==0u)out.rejection_reasons|=A2WC_STATUS02_CLEAR;
 if(in.freshness==A2WC_FRESHNESS_UNKNOWN)out.rejection_reasons|=A2WC_FRESHNESS_UNPROVEN;
 else if(in.freshness==A2WC_STALE)out.rejection_reasons|=A2WC_DATA_STALE;
 else if(in.freshness!=A2WC_FRESH)out.rejection_reasons|=A2WC_INVALID_FRESHNESS_INPUT;
 if(in.packed_source!=in.packed_snapshot)out.rejection_reasons|=A2WC_SOURCE_SNAPSHOT_DISAGREE;
 return out;
}
