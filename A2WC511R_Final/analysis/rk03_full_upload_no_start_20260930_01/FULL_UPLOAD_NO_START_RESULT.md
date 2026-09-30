# FULL_KERNEL_UPLOAD_NO_START: offline qualification PASS

No physical operation occurred in this resumed scope. Previous first-chunk physical PASS and passive OEM-return PASS remain preserved. The vehicle did not need to be connected.

Branch: `rk03/full-upload-no-start`. Commit: `4cb0bee977fcd979af2e88223c1ff14898ab72bf`.

`derive_offline_stage.py` was recovered intact and had completed generation. Its12 source files and two completed clean builds passed integrity checks; the generator and builds were reused.

## Modeled sequence

`BF ->81 ->8300 ->2701 ->2702 ->wait200ms ->108502 ->wait100ms ->baud15625 ->clearTX7 ->clearRX8 ->wait200ms ->one34 ->15fixed36(each exact76 ACK) ->STOP ->cleanup`

There are22 protocol requests: six admission requests, one declaration and15 transfers. The first14 blocks carry128bytes each; the last carries16. All are fixed and hash-pinned.

## Results

- Qualification:287/287 passed (28positive,259negative), including every transfer failure boundary. No automatic retry.
- Independent native/model review:PASS. Independent runner/journal audit:PASS,906unique pins and3402transmissions checked;9mutated journals rejected.
- An earlier285/287 attempt exposed a runner-only service-name/index matching error; its report and runner snapshot remain preserved. Native source and executables did not change.
- Both clean executables:328704bytes, SHA256 `602f2b0835d8e39d37af9b1eddead0223cd7ba5411970645e1ebc7e78dc1c7a5`.
- Both canonical build manifests: SHA256 `f4ee846486a79e4c0ed500af8d9baca27011c171ca614ab887d7d9d7a823f764`. Volatile timestamps/output-directory fields are excluded explicitly.
- Current-ROM instruction replay:476281instructions,452aligned four-byte RAM stores, exact current/stock instruction-memory-MMIO prefix match.
- Final modeled plaintext RAM:1808bytes, SHA256 `3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581`; byte-identical to the preserved owned kernel image.
- Kernel start is unreachable within the compiled entry points:bounded stage0..21 dispatcher, fifteen exactACK exchanges, then cleanup. The reference handoff frame is excluded. No physical-provider, kernel-version, ROM-read, flash or arbitrary input path exists.
- Generic CRT loader imports remain in the executable; they are not an application physical-provider loader.

## Fixed upload chunks

Hashes below identify transmitted ciphertext payloads. FIXED_UPLOAD_MANIFEST.json also records each complete-frame hash/checksum and expected plaintext block hash. Equal payload hashes at different addresses reflect identical bytes in the fixed image, not repeated frames.

|Chunk|Address|Bytes|Payload SHA256|
|---:|---|---:|---|
|1|`FFFF3000`|128|`b27c4fe47f71a7c96881891c73002084f3dbc5ebe977ec7e7e857b5dc4c44413`|
|2|`FFFF3080`|128|`07e0a7591c2664cad999b2ef96cc8531bb1251e221575e7c87de26ede4763abf`|
|3|`FFFF3100`|128|`100d6ec33fc5faa7b65efb3288816bc417b8faadf44ac757e1dd024dd8a328e9`|
|4|`FFFF3180`|128|`b81dfc437e0265ea95bee53c3c1e4f1fb858628b780c8d04dd734b27bf878f41`|
|5|`FFFF3200`|128|`c1f913fa9be870c84ec384eaadeb5021e425b0a68ad0aff8367af7b789a88348`|
|6|`FFFF3280`|128|`98196e7717170d0648aad05bce25d684019cf9aeba1f7671b05d40912c22786c`|
|7|`FFFF3300`|128|`65006edfa7ce69a2dedceca722fead4c5fde054b7819c799230c28d3e2dd500f`|
|8|`FFFF3380`|128|`3452edc6a17f072160fbe6afab0864eafd55dd03475e2a2a1ec7ce54affd7235`|
|9|`FFFF3400`|128|`3452edc6a17f072160fbe6afab0864eafd55dd03475e2a2a1ec7ce54affd7235`|
|10|`FFFF3480`|128|`3452edc6a17f072160fbe6afab0864eafd55dd03475e2a2a1ec7ce54affd7235`|
|11|`FFFF3500`|128|`3452edc6a17f072160fbe6afab0864eafd55dd03475e2a2a1ec7ce54affd7235`|
|12|`FFFF3580`|128|`3452edc6a17f072160fbe6afab0864eafd55dd03475e2a2a1ec7ce54affd7235`|
|13|`FFFF3600`|128|`3452edc6a17f072160fbe6afab0864eafd55dd03475e2a2a1ec7ce54affd7235`|
|14|`FFFF3680`|128|`3452edc6a17f072160fbe6afab0864eafd55dd03475e2a2a1ec7ce54affd7235`|
|15|`FFFF3700`|16|`650e747209d3aad9ba1f26fc45f7eb2cf2c325e64bfeec652463825f4d202995`|

## Remaining gaps and next milestone

This is an offline-only release. Physical chunks2..15, provider/electrical behavior and recovery after a full unstarted upload are not yet demonstrated. Final RAM equality is a CPU-model result under explicit admission/peripheral assumptions, not a vehicle RAM readback.

Next recommended milestone: separately design and qualify `RK03_FULL_UPLOAD_NO_START_PHYSICAL`. The future design plan is prepared in FUTURE_PHYSICAL_RELEASE_PLAN.md; it does not create or authorize a physical binary. Retain IGNITION OFF ->TEST MODE ON ->new explicit software authorization ->one future test ->IGNITION OFF ->NORMAL MODE ON ->passive OEM return. No individual component gates.

Current physical ECU image analysis is reused unchanged: authoritative current.bin, edited calibration, executable code byte-identical to verified stock. It is not factory stock.

Qualification SHA256: `cca85ff256dc86c7f88e3f3baa48c0868a51ff0617096455071086b5b54c2660`.
