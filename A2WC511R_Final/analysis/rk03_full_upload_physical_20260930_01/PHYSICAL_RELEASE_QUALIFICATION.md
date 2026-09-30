# Physical full upload/no start: separately qualified, not executed

Branch `rk03/full-upload-no-start-physical`; commit `41b01141ab2aaa8f001f993b245e09cb1756f5b5`.

311/311 same-executable offline tests passed, plus36 mocked launcher,14 recovery and38 result-validation checks. Independent reviews passed. No hardware was accessed.

Executable SHA256: `6c7571ece71bb6c29feae9fbfa873cca9635e41cabe269ebc7fa21b1e2fc0d51`.
Certificate SHA256: `dbfe169cbe89f4ab23318cb79dec1dbafcaa49dbdea48397dc4ec0f16de95399`.
Fixed plaintext image SHA256: `3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581`.

The fixed protocol remains unchanged from the sealed offline artifact. Only physical entry, locked provider binding, one-shot authorization/session controls and physical result labels were added. Every15 fixed transfer requires its exact76 ACK. After the final ACK only filter/channel/provider cleanup is possible. There is no kernel-start, custom-kernel version, ROM-read, flash, arbitrary input or retry path.

Next human state: IGNITION OFF. Then TEST MODE ON. Only after displaying the required release details and checking competing clients may the new exact authorization token be requested.

Physical result, recovery and any later offline identity-stage qualification will be reported separately. Historical reports are unchanged.
