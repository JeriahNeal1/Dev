# Fixed upload chunks

SHA256 values identify the transmitted ciphertext payload, excluding address, framing and checksum. Plaintext and full-frame hashes are also recorded in FIXED_UPLOAD_MANIFEST.json.

| Chunk | Address | Bytes | Payload SHA256 |
|---:|---|---:|---|
| 1 | `FFFF3000` | 128 | `b27c4fe47f71a7c96881891c73002084f3dbc5ebe977ec7e7e857b5dc4c44413` |
| 2 | `FFFF3080` | 128 | `07e0a7591c2664cad999b2ef96cc8531bb1251e221575e7c87de26ede4763abf` |
| 3 | `FFFF3100` | 128 | `100d6ec33fc5faa7b65efb3288816bc417b8faadf44ac757e1dd024dd8a328e9` |
| 4 | `FFFF3180` | 128 | `b81dfc437e0265ea95bee53c3c1e4f1fb858628b780c8d04dd734b27bf878f41` |
| 5 | `FFFF3200` | 128 | `c1f913fa9be870c84ec384eaadeb5021e425b0a68ad0aff8367af7b789a88348` |
| 6 | `FFFF3280` | 128 | `98196e7717170d0648aad05bce25d684019cf9aeba1f7671b05d40912c22786c` |
| 7 | `FFFF3300` | 128 | `65006edfa7ce69a2dedceca722fead4c5fde054b7819c799230c28d3e2dd500f` |
| 8 | `FFFF3380` | 128 | `3452edc6a17f072160fbe6afab0864eafd55dd03475e2a2a1ec7ce54affd7235` |
| 9 | `FFFF3400` | 128 | `3452edc6a17f072160fbe6afab0864eafd55dd03475e2a2a1ec7ce54affd7235` |
| 10 | `FFFF3480` | 128 | `3452edc6a17f072160fbe6afab0864eafd55dd03475e2a2a1ec7ce54affd7235` |
| 11 | `FFFF3500` | 128 | `3452edc6a17f072160fbe6afab0864eafd55dd03475e2a2a1ec7ce54affd7235` |
| 12 | `FFFF3580` | 128 | `3452edc6a17f072160fbe6afab0864eafd55dd03475e2a2a1ec7ce54affd7235` |
| 13 | `FFFF3600` | 128 | `3452edc6a17f072160fbe6afab0864eafd55dd03475e2a2a1ec7ce54affd7235` |
| 14 | `FFFF3680` | 128 | `3452edc6a17f072160fbe6afab0864eafd55dd03475e2a2a1ec7ce54affd7235` |
| 15 | `FFFF3700` | 16 | `650e747209d3aad9ba1f26fc45f7eb2cf2c325e64bfeec652463825f4d202995` |

Final expected plaintext RAM: **1,808 bytes**, SHA256 `3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581`.

No handoff/start command follows chunk15.
