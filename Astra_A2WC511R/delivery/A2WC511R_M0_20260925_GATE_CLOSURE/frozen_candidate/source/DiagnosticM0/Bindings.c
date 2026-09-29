#include "Diagnostic.h"
#include "A2WC511R.h"
#include "DiagnosticConfig.h"
/* Caller supplies RAM: synthetic for harness, UNAPPROVED candidate for the
 * explicitly experimental link. This sampler never selects the allocation. */
static m0_u8 read8(m0_u32 address)
{
 return *(const volatile m0_u8 *)address;
}
M0_API void m0_sample_hardware(volatile M0State *state)
{
 M0Input in;
 m0_u8 source2, snapshot2, latch2, flags2;
 in.source = read8(M0_PACKED_SOURCE);
 in.snapshot = read8(M0_PACKED_SNAPSHOT);
 in.latch = read8(M0_UPDATE_LATCH);
 in.flags = read8(M0_STATUS_FLAGS);
 source2 = read8(M0_PACKED_SOURCE);
 snapshot2 = read8(M0_PACKED_SNAPSHOT);
 latch2 = read8(M0_UPDATE_LATCH);
 flags2 = read8(M0_STATUS_FLAGS);
 in.capture_changed = (in.source != source2 || in.snapshot != snapshot2 ||
                       in.latch != latch2 || in.flags != flags2) ? 1u : 0u;
 in.freshness = M0_UNKNOWN; /* Never infer freshness from status/latch or gear. */
 in.reserved0 = 0u;
 in.reserved1 = 0u;
 m0_observe(state, &in);
}
