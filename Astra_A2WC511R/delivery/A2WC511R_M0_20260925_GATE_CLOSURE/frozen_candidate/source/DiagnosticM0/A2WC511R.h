#ifndef A2WC511R_M0_TARGET_H
#define A2WC511R_M0_TARGET_H
/* Actual target identity and read-only input addresses.
 * Addresses derive from handoff state/SYMBOLS.json and existing A2WC511R IDB.
 * 4CA1 and 4C50:02 retain raw meanings; neither proves communications freshness. */
#define TARGET_ECU A2WC511R
#define ECU_CALIBRATION_ID "A2WC511R"
#define ECU_IDENTIFIER "2F12515306"
#define AUTO_TRANS 1
#define M0_PACKED_SOURCE 0xFFFF4C75u
#define M0_PACKED_SNAPSHOT 0xFFFF4C8Du
#define M0_UPDATE_LATCH 0xFFFF4CA1u
#define M0_STATUS_FLAGS 0xFFFF4C50u
/* No default code address, RAM hole, hook pointer or reset change is supplied.
 * Linker allocation and wrapper must be accepted before integration. */
#endif
