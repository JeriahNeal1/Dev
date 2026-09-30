# Independent physical full-upload review

PASS: one authorized session, 22 transmissions, one declaration and fifteen fixed transfers with fifteen exact `76` acknowledgements. All 85 logged calls (82 provider API calls and three host waits) returned zero. Cleanup ended with StopMsgFilter, Disconnect and Close; the child exited0 and the post-exit client scan passed.

The actual seed was `b99d2bfd` and the independently recomputed key was `51f7b537`. All fifteen frame bytes, checksums, addresses and payload order match the pinned upload contract: fourteen128-byte chunks plus one16-byte chunk. Offline decryption of the transmitted ciphertext matches the pinned1,808-byte kernel. No physical RAM readback is claimed.

The five SET_CONFIG calls and immediate GET_CONFIG, broad four-zero filter, requested200/100/200ms waits, accepted15625baud SET and TX-then-RX queue clears match the qualified sequence. Actual measured waits were 200.5473ms, 102.8275ms, 205.7765ms. All API arguments, raw provider records, timing order, output guards and cleanup records were checked.

Authorization, session, certificate, executable, provider and source/copy hashes agree. No later kernel-start/version request, ROM request, flash request or retry appears. This read-only review invoked no provider or executable. OEM-return recovery is outside this report.

Exact frame and evidence hashes are in PHYSICAL_REVIEW.json.
