# Diagnostic observation scaffold — not an ECU port
This pure C99 helper has no MCU addresses, scheduling, RAM placement, hooks, calibration or output control. It provides a small deterministic test target for nibble decoding and reason-code reporting. It does not implement or prove the unknown TCU freshness signal; unknown remains an explicit reason.

The `freshness` input must never be supplied as FRESH merely because 4CA1==1 or status02 is set. Those semantics are the unresolved engineering question. Source/snapshot agreement is also not freshness. The observer does not decide whether the vehicle can launch.

The full256x256 decoder-input/previous-value domain and all256 packed bytes are tested on the host. These tests do not prove ECU ABI/runtime/physical behavior. Codex may reuse or replace this scaffold when integrating M0 with the actual target, but must establish the hardware bindings, startup, scheduling, types, stack and exact allocation separately. Host .o/executables are not firmware artifacts.
