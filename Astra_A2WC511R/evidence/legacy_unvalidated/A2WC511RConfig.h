#ifndef A2WC511R_CONFIG_H
#define A2WC511R_CONFIG_H

//////////////////////////////
// A2WC511R TARGET OPTIONS
//////////////////////////////

#define AUTO_TRANS 1
#define SD_DMAP     0

#define ECU_IDENTIFIER_CHARS  (10)
#define ECU_CALIBRATION_CHARS (8)
#define MOD_CALIBRATION_ID     FFFFFFFF
#define MOD_ECU_IDENTIFIER     FFFFFFFFFF

/* Unit-test expectation for the exact uploaded ROM at 1.25 V MAF input.
 * Recalculate if the base ROM or MAF table changes.
 */
#define EXPECTED_MAF_SENSOR 3.27f
#define EXPECTED_MAF_SD     3.73053f

#endif
