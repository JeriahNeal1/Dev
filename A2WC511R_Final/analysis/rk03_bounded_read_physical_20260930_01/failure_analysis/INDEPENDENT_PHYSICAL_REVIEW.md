# Independent review of failed bounded read

**Physical result: FAIL.** The single run exited1 with cleanup confirmed. The prior24 transmissions, all15 upload acknowledgements, kernel start, and identity passed. All91 preceding API calls match the successful identity session in function/order/status; normalized content differences are the new seed and derived key.

The final fixed TX was `beef00080300000000000200ba` at API sequence91, status0/count1. Subsequent receives were:

| API sequence | Status/count | Record | API elapsed |
|---|---|---|---|
|92|0 /1|Empty START_OF_MESSAGE|4.7857 ms|
|93|0 /1|228 data bytes, ExtraDataIndex228|32.4303 ms|
|94|16 /0|No additional bytes|1005.3896 ms|

The first227 frame bytes match the expected523-byte response. At zero-based frame offset227, actual `F8` differs from expected `28` (candidate ROM payload offset217). Thus217 payload-prefix bytes match current.bin, one following byte differs, and295 expected frame bytes remain unobserved. The trailing `F8` is not a valid checksum for the preceding227 bytes; their additive checksum would be `39`. No complete response or validated512-byte read was produced.

The first observed byte divergence is sequence93, raw log line189. The host treats this record as a permissible incomplete fragment, so its actual stopping condition is sequence94, raw line191: `ERR_BUFFER_EMPTY` (16), defined by the pinned Tactrix header at line252. `ERR_TIMEOUT` is9 at line245. The receive observation window was 1042.7533 ms; the terminal was caused by the nonzero provider status, not expiration of the2000 ms whole-frame deadline.

The five initial SETs and GET readback, broad filter, requested200/100/200 ms waits,15625 baud SET, TX/RX clears7/8, then62500 baud SET and BEEF filter are retained. Baud SET acceptance is recorded; no effective baud GET is claimed. Stop-filter/disconnect/close each returned0, with no retry or later TX.

The sealed static model and retained instruction replay expect the same fixed request and523-byte response (response SHA256 `796f64cefcd2b81c5c7662b2bdacad828c0a948c55bfdc5d002ac5c8da7f898e`). The instruction replay recorded512 ROM loads and10327 instructions under declared simulated UART/peripheral timing. It was not rerun. It does not establish the physical cause of the divergence.

Raw log SHA256: `42c900bbfae9e2537615eb3fd0967e013d7d603d315968c1d59bbd0de701ba1f`. The JSON review preserves complete final request/receive records, configuration, timing, source line pointers, expected/observed bytes, prefix differences, and source hashes. It distinguishes observed bytes from a validated ROM read.

**No root cause is proven. No correction, retry, or full two-pass physical release is qualified by this failed result.** Further work remains offline; operator recovery is handled separately.
