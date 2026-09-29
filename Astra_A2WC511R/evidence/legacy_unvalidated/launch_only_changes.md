# Launch-only source changes

Do not enable the stock MerpMod timing/fuel replacement tables until they have been
populated from your own calibration. The upstream README explicitly says its default
tables are not base maps.

Recommended launch-only design:

1. Add `#define LAUNCH_ONLY_HACKS 1` to your chosen build header.
2. In `EcuHacks.h`, do not force `SWITCH_HACKS` solely because timing/POLF is enabled
   when `LAUNCH_ONLY_HACKS` is set.
3. In `TimingHacks.c`, begin from `PrimaryOEMTimingTable`; apply LC retard only while
   `LCEngaged == 1`.
4. In `FuelHacks.c`, begin from `PrimaryOEMPolfTable`; apply LC lock/compensation only
   while `LCEngaged == 1`.
5. In the automatic `RevLimCode`, require brake, low speed, minimum throttle, and a
   verified drive-gear state.
6. First flash: LC timing/fuel modes disabled. Log only.
