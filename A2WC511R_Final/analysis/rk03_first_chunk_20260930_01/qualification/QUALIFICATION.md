# First-chunk probe qualification

OFFLINE QUALIFICATION = PASS (156/156 cases)
RK03_FIRST_CHUNK_PHYSICAL = NOT_RUN

The supersession note records the earlier transition and OEM-return physical PASS results without changing historical reports. The new first-chunk executable is qualified separately and has not contacted the vehicle.

- Branch: `rk03/first-chunk-physical`
- Commit: `76f8bc16495529645f10fab6dd5f5b522cbe190b`
- Executable SHA256: `3a6abe4e11fc6a85682c33018e67b533897860a932962f2840976fbd35ed1c02`
- Qualification SHA256: `51f42896bc04e63b62fdcbb57b490ef8212af69f906e71e5e51c577ce12a6af4`
- Two clean builds are byte-identical.
- Independent native, runner/evidence, launcher and recovery reviews passed.
- All16 seed vectors and the exact successful BF/81/83 transcript passed; all12 real-clock waits meet the requested minima.
- The physical path can send one fixed128-byte36 at FFFF3000 after one34, then requires exact76 and closes transport.
- Original846 checkpoint files and current.bin remain hash-identical.

The next required human state is IGNITION OFF, followed by TEST MODE ON and the exact new authorization PROCEED RK03 FIRST CHUNK PROBE. No physical authorization is recorded. There will be no automatic retry.

After the attempt, recovery requires IGNITION OFF then NORMAL MODE ON, followed by the unchanged passive BF/A8 OEM-return observer. Full-kernel-upload-no-start preparation is conditional on physical PASS and remains offline only.
