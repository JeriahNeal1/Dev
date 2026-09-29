#include "Diagnostic.h"
M0_API m0_u8 m0_decode(m0_u8 nibble, m0_u8 previous)
{
 if (nibble < 8u) return nibble;
 if (nibble == 8u) return 0u;
 return previous;
}
M0_API m0_u32 m0_reasons(const M0Input *in)
{
 /* Double reads cannot prove atomic/coherent CAN data. Retain this reason. */
 m0_u32 reasons = M0_CAPTURE_COHERENCE_UNPROVEN;
 if (in->snapshot != 0x11u) reasons |= M0_NOT_FIRST;
 if (in->latch != 1u) reasons |= M0_LATCH_NOT_ONE;
 if ((in->flags & 2u) == 0u) reasons |= M0_STATUS02_CLEAR;
 if (in->freshness == M0_UNKNOWN) reasons |= M0_FRESHNESS_UNKNOWN;
 else if (in->freshness == M0_KNOWN_STALE) reasons |= M0_STALE;
 else if (in->freshness != M0_FRESH) reasons |= M0_INVALID_FRESHNESS;
 if (in->source != in->snapshot) reasons |= M0_SOURCE_DISAGREES;
 if ((in->snapshot >> 4) > 8u || (in->snapshot & 15u) > 8u)
  reasons |= M0_UNSUPPORTED_NIBBLE;
 if (in->capture_changed != 0u) reasons |= M0_CAPTURE_CHANGED;
 return reasons;
}
M0_API void m0_init(volatile M0State *state)
{
 volatile m0_u8 *p = (volatile m0_u8 *)state;
 m0_u32 i, seq = 0u;
 if (state->magic == M0_MAGIC && state->initialized == 1u)
  seq = state->sequence & ~1u;
 state->sequence = seq + 1u;
 for (i = sizeof(state->sequence); i < sizeof(*state); ++i) p[i] = 0;
 state->magic = M0_MAGIC;
 state->reasons = M0_FRESHNESS_UNKNOWN | M0_CAPTURE_COHERENCE_UNPROVEN;
 state->initialized = 1u;
 state->sequence = seq + 2u;
}
M0_API void m0_observe(volatile M0State *state, const M0Input *in)
{
 m0_u32 seq = state->sequence;
 m0_u8 target = (m0_u8)(in->snapshot >> 4);
 m0_u8 current = (m0_u8)(in->snapshot & 15u);
 /* This is an explicit software-observer prerequisite, not a boot detector. */
 if (state->magic != M0_MAGIC || state->initialized != 1u) {
  m0_init(state);
  seq = state->sequence;
 }
 state->sequence = (seq & ~1u) + 1u;
 if (state->samples != 0u && state->previous_snapshot != in->snapshot)
  state->transitions = state->transitions + 1u;
 state->source = in->source;
 state->snapshot = in->snapshot;
 state->latch = in->latch;
 state->flags = in->flags;
 state->target_nibble = target;
 state->current_nibble = current;
 state->decoded_target = m0_decode(target, state->decoded_target);
 state->decoded_current = m0_decode(current, state->decoded_current);
 state->freshness = in->freshness;
 state->capture_changed = in->capture_changed;
 state->reasons = m0_reasons(in);
 state->previous_snapshot = in->snapshot;
 state->samples = state->samples + 1u;
 state->sequence = (seq & ~1u) + 2u;
}
