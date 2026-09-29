# Host-only facade alternative

`host_facade.py` translates the exact two RAW4 project requests into whitelisted
OEM A8 reads, then computes the page 1 reason and FE frame locally. It requires
**zero firmware changes**. It is an alternative host architecture, not the
ECU-resident BE extension and not evidence that an ECU accepted a BE request.

The injected native exchange sees only these requests:

| Project page | Native A8 request | OEM addresses |
| --- | --- | --- |
| 0 | `8010F00EA800FF4C75FF4C8DFF4CA1FF4C5055` | source, snapshot, latch, flags |
| 1 | `8010F00BA800FF4BC1FF4BC2FF4C8D22` | actual OEM target, actual OEM current, snapshot |

The encoder is bound to the actual installed RomRaider 1.1.0 `SSMProtocol`
framing: the isolated native Java probe confirms both requests byte-for-byte,
with fast polling disabled. No transport or provider is created by that probe.
The facade admits no caller-supplied addresses or continuous-read controls.

`HostFacade(native_exchange).exchange_project(request_frame(page))` returns an
immutable `FacadeResult`, containing `mode=HOST_FACADE_NO_ECU_EXTENSION`, the
original project request, actual native A8 request and echo/response bytes,
**local** FE response, and decoded observation. It never reports local framing
as a received ECU FE response. The native exchange callable must independently
isolate and bound I/O; this module supplies no physical backend.

Strict native echo, E8 command, source/destination, exact length, and checksum
checks run before a local response is generated. One native transaction may be
outstanding; failures permanently fault the facade instance, with no retries.
Neither a new instance nor an exact echo proves transport resynchronization or
data freshness. Both pages retain the same noncoherence and unknown-validity
meaning as the ECU prototype, and the reason's `80` bit is always set.

The facade returns actual OEM target/current values even for invalid packed
nibbles; it does not reconstruct the decoder's held history. Page 1 makes one
ordinary three-address A8 request, then computes the predicates from those
returned values. It does not claim the sequential OEM reads are atomic.

From `C:\Dev`, run the independent synthetic suite and native framing probe:

```powershell
py -3 C:\Dev\Astra_A2WC511R\integrations\m06\run_validation.py --suite facade
& C:\Dev\Astra_A2WC511R\reports\local\m06_architecture\protocol\Invoke-NativeProbe.ps1 -Facade
```

The seven synthetic test groups exercise exact request admission and mutations,
fixed address/control policy, all packed snapshots with retained OEM decoded
values, native echo/frame/checksum failures, reentrancy, and terminal I/O faults.
These tests generate fixture bytes. Actual compiled OEM A8 response replay is
separate evidence. No installation, frozen collector, or ECU memory is changed.

This architecture removes new ROM allocation, new RAM allocation, injected ABI,
and changed firmware scheduling from its own implementation. It does not resolve
current-calibration identity, physical transport support, TCU freshness/fault
semantics, or whether a host-only facade fulfills the requested ECU port scope.
