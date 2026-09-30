# Final checkpoint: one remaining physical acquisition

RK03_BOUNDED_ROM_READ_128_PHYSICAL = PASS
OEM_RETURN_AFTER_BOUNDED_ROM_READ_128 = PASS

One valid139-byte physical frame contained128 exact current.bin bytes. There was one physical invocation, one ROMread, no retry, and clean cleanup. Passive recovery produced BF2F12515306 and120/120 six-variable PASS_CAPTURE_ONLY with clean observer/broker/provider exit.

The failed512 response is classified TRUNCATED_RESPONSE at the application protocol layer. Its header declares512 data bytes; F8 is not a valid trailer for a217-byte response. The physical cause is unresolved. Existing failed evidence remains unchanged.

The final release passed38/38 same-PE fake cases,65/65 validator checks,36/36 launcher and14/14 recovery checks, two byte-identical builds, and independent review. Final physical invocations=0.

Branch rk03/final-two-pass-128
Commit 62a261d977beb952d6a2393b6de179fea4b6fff0

Executable SHA256: 991492809897e3333fdc1422e70d70690906f59d722e1e99088fb55bd56432ce
Certificate SHA256: 7e3fd3de08872f2e6ad4327d344e0b580bd0f1f4996ca7683be05cdcd93b7ca9
Kernel SHA256: 808a5523d47de11881bfc2ea06a35278aedb5122ed51e8110f817b3210adb653

Fixed range[0,0x100000),128bytes/block,8192blocks/pass,exactly2passes. Each output1048576bytes; total2097152bytes. Pass1 is compared block-by-block immediately againstpass0. Both images must be byte-identical with equalSHA256; current.bin equality is reported separately. No arbitrary addresses,lengths,passes,kernel orentry; noflash; no retry or thirdpass.

Remaining physical milestone: RK03 FINAL TWO-PASS 128-BYTE ACQUISITION.

Future human states: IGNITION OFF -> TEST MODE ON -> PROCEED RK03 FINAL TWO PASS ACQUISITION -> acquisition/cleanup -> IGNITION OFF -> NORMAL MODE ON. Then automatic passiveOEMreturn,finalrawcomparison,integrityaudit,and localcompletioncheckpoint/tag. PROJECTCOMPLETE is emitted only after all required results and tag succeed. No final acquisition was executed during preparation.

See FINAL_RUN_PLAN.md for exact pinned launcher/recovery/finalizer commands and failure exits.
