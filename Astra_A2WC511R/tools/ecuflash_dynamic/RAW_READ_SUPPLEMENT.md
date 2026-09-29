# Virtual-only raw read supplement

`raw_read_supplement.py` demonstrates a bounded protocol remedy for the installed ECUFlash CRC-substitution shortcut. It is a local virtual-model client, not a physical J2534 backend. It imports no provider DLL and has no vehicle/device API. Its sole transport destination is the literal loopback address`127.0.0.1` with the authenticated port/token from an existing isolated session.

The command takes only an isolated session name:

```powershell
py -3.14 -B C:\Dev\Astra_A2WC511R\tools\ecuflash_dynamic\raw_read_supplement.py SESSION_NAME
```

The session must have completed its installed-host Read successfully, saved its1MiB output, closed the provider and application, and left the virtual model at`KERNEL`. The script pins the installed executable and three isolation/fake-provider binaries, validates the API-attachment mapping and isolation trace, verifies the original trace sequence, and checks the session's loopback association. A changed binary requires an explicit reviewed pin update. These are local project evidence associations, not signed attestation.

Before any RPC, it creates`SESSION/post_read_snapshot/` and copies the original trace, saved image and supporting records. It refuses to reuse an existing snapshot/output directory. It then performs only this fixed sequence:

1. Open the fake provider and connect protocol3, flags`0200`, baud62500.
2. Install a`BE EF` pass filter and validate the exact`OpenECU Subaru SH7058 DUAL  Kernel V1.07` version plusNUL.
3. Request command03 for every ascending512-byte block over`[0,0x100000)`.
4. Stop the filter, disconnect and close the fake provider.

An independent finite-state allowlist rejects any other RPC, opcode, address, transfer size or order. No CRC, upload, security, reset, voltage, periodic or flash-control operation is exposed. Wire replies must have the exact framing, declared length, positive opcode, checksum, message boundary and explicit virtual provenance. The first failure closes the socket and prevents any further RPC from that client. Because a failed client does not send extra cleanup commands, its virtual provider state can remain open; that failure is recorded rather than reported as a clean close.

Output goes to`reports/local/ecuflash_dynamic/raw_read_supplement/SESSION_NAME/`: raw returned bytes, a hash for each512-byte block, the client intent/result journal, an immutable combined provider-trace copy, and`RESULT.json`. The result records differences from the unchanged native ECUFlash saved image. Closing the fake host channel does not reset the virtual ECU.

The completed`coverage_v2_04` demonstration requested all2048 blocks, returned exactly1MiB with SHA256`c777be6d9e0e3de2a1abc263a26c91ec2e1f421d09acb6fbe09c3ca81021180b`, and matched the synthetic model. It recovered37 bytes omitted by native Read, in`[0x86000,0x86021)` and`[0x86FFC,0x87000)`. The original4753-event trace is preserved with SHA256`db91fac527cda20b2d7572f045fab45bf07e24198204bf9aeb7a7c878a4f5680`. An additional4104 RPCs belong to this separately identified Python prototype, not to installed ECUFlash.

This result does not make the installed Read exact. It does not prove execution of the uploaded kernel, physical timing, a usable hardware session handoff, or cleanup/reset behavior. Those remain separate gates.

Offline adversarial tests make no connections:

```powershell
py -3.14 -B C:\Dev\Astra_A2WC511R\tools\ecuflash_dynamic\raw_read_supplement_test.py
```

The seven groups cover asymmetric returned data, malformed/checksum/length/opcode/provenance replies, unsupported outbound commands and addresses, exact version and end-of-range handling, network failure latching, calls after terminal state, and revocation of a PASS result if the original provider-trace prefix changes. That final check was hardened after the successful demonstration; its actual unchanged-prefix result was independently confirmed. `EXECUTED_CLIENT_SOURCE.py` preserves the exact earlier source used for the demonstration, while the current script includes the fail-closed hardening.

Reconstruct the demonstration image independently from both recorded journals, without network access:

```powershell
py -3.14 -B C:\Dev\Astra_A2WC511R\tools\ecuflash_dynamic\raw_read_supplement_verify.py coverage_v2_04
```
