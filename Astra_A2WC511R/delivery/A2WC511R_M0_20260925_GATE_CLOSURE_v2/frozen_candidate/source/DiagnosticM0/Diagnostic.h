#ifndef A2WC511R_DIAGNOSTIC_M0_H
#define A2WC511R_DIAGNOSTIC_M0_H
/* GPL-3.0-or-later. A2WC511R source-port diagnostic closure.
 * No output authority, peripheral writes, active controls or freshness inference.
 * Fixed-width types avoid dependency on HEW's generated headers or host libc. */
typedef unsigned char m0_u8;
typedef unsigned short m0_u16;
typedef unsigned int m0_u32;
typedef char m0_require_uint32[(sizeof(m0_u32) == 4) ? 1 : -1];
typedef char m0_require_uint16[(sizeof(m0_u16) == 2) ? 1 : -1];
#if defined(M0_HOST_TEST) && defined(_WIN32)
#define M0_API __declspec(dllexport)
#else
#define M0_API __attribute__((section(".m0.code"), aligned(4)))
#endif
enum m0_reason {
 M0_NOT_FIRST=1u, M0_LATCH_NOT_ONE=2u, M0_STATUS02_CLEAR=4u,
 M0_FRESHNESS_UNKNOWN=8u, M0_STALE=16u, M0_SOURCE_DISAGREES=32u,
 M0_INVALID_FRESHNESS=64u, M0_UNSUPPORTED_NIBBLE=128u,
 M0_CAPTURE_CHANGED=256u, M0_CAPTURE_COHERENCE_UNPROVEN=512u
};
enum m0_freshness { M0_UNKNOWN=0, M0_FRESH=1, M0_KNOWN_STALE=2 };
typedef struct {
 m0_u8 source, snapshot, latch, flags;
 m0_u8 freshness, capture_changed, reserved0, reserved1;
} M0Input;
/* All fields describe observations; matching first gear never permits outputs.
 * sequence protects publication only. It is not ECU/TCU communication freshness.
 * Reader contract: read sequence-before; reject odd; read all32 bytes; reread
 * sequence-after; require equal even sequences plus magic and initialized==1.
 * Requires one nonreentrant writer. No claim that separate logger samples are
 * atomic or that the CAN snapshot is fresh/coherent. Counter wrap can cause ABA.
 * decoded_* are local reconstructions, NOT reads of OEM4BC1/4BC2.
 * Explicit init or guarded lazy init; no warm-reset/power-cycle identification. */
typedef struct {
 m0_u32 sequence, magic, samples, reasons;
 m0_u32 transitions;
 m0_u8 source, snapshot, latch, flags;
 m0_u8 target_nibble, current_nibble, decoded_target, decoded_current;
 m0_u8 freshness, previous_snapshot, initialized, capture_changed;
} M0State;
typedef char m0_require_state32[(sizeof(M0State) == 32) ? 1 : -1];
#define M0_MAGIC 0x4D304431u
M0_API m0_u8 m0_decode(m0_u8 nibble, m0_u8 previous);
M0_API m0_u32 m0_reasons(const M0Input *input);
M0_API void m0_init(volatile M0State *state);
M0_API void m0_observe(volatile M0State *state, const M0Input *input);
#endif
