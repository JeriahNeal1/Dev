# A2WC511R MerpMod validation gates

- [ ] Untouched stock ROM archived in at least two locations.
- [ ] Current intended base ROM archived separately.
- [ ] ROM file size is exactly 1,048,576 bytes.
- [ ] CALID at 0x2000 is A2WC511R.
- [ ] ECU ID is 2F12515306.
- [ ] ROM hole is all 0xFF and has no valid XREFs.
- [ ] RAM hole is unreferenced, outside stack/VBR/indirect use, and sentinel-tested.
- [ ] Every patch old-value matches the original ROM.
- [ ] SharpTune hewbuild passes read, baseline, test, apply, remove, byte-identical revert,
      and definition generation.
- [ ] Patched ROM remains exactly 1,048,576 bytes.
- [ ] ECUFlash corrects the Subaru DBW checksum.
- [ ] Logic-only flash starts, idles, communicates, and logs normally.
- [ ] Brake switch toggles correctly.
- [ ] Vehicle speed, RPM, throttle, and gear values are plausible.
- [ ] MerpMod LC Engaged toggles only in the intended conditions.
- [ ] No timing/fueling intervention until the logic-only test passes.
- [ ] Launch validation begins at zero added fuel and mild timing retard.
- [ ] Wideband AFR, boost, knock, coolant, IAT, ATF and battery voltage are logged.
- [ ] Existing 5EAT WOT-shift/stall fault is resolved before repeated launch testing.
