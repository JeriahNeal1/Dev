#ifndef A2WC_DIAGNOSTIC_OBSERVER_H
#define A2WC_DIAGNOSTIC_OBSERVER_H
/* HOST-TESTED SCAFFOLD ONLY. No ECU addresses/hooks, output authority or timing model.
 * A successful result is an observation, not permission to actuate/launch/flash. */
#include <stdint.h>
enum a2wc_freshness { A2WC_FRESHNESS_UNKNOWN=0, A2WC_FRESH=1, A2WC_STALE=2 };
enum a2wc_observation_reason {
 A2WC_NOT_MATCHING_FIRST=1u<<0, A2WC_LATCH_NOT_ONE=1u<<1,
 A2WC_STATUS02_CLEAR=1u<<2, A2WC_FRESHNESS_UNPROVEN=1u<<3,
 A2WC_DATA_STALE=1u<<4, A2WC_SOURCE_SNAPSHOT_DISAGREE=1u<<5,
 A2WC_INVALID_FRESHNESS_INPUT=1u<<6
};
struct a2wc_diag_input { uint8_t packed_source, packed_snapshot, update_latch, status_flags, freshness; };
struct a2wc_diag_output { uint8_t target_nibble, current_nibble; uint32_t rejection_reasons; };
uint8_t a2wc_decode_nibble(uint8_t nibble,uint8_t previous);
struct a2wc_diag_output a2wc_observe(struct a2wc_diag_input in);
#endif
