# Offline compiled OEM wire replay

`replay_wire.py` consumes the retained four OEM software-event fixtures. It has
no physical transport, provider loading, firmware write, or automatic fallback.
Both modes verify the selected ROM hash and fixture event hashes. Every reply
byte after the first header byte must agree with an executed OEM SCI transmit
register write. The first byte is released by the fixture from the OEM-built
FIFO; the first-byte timer/electrical behavior remains outside this model.

Run the ECU-resident prototype's two BE requests:

```powershell
py -3 C:\Dev\Astra_A2WC511R\integrations\m06\replay_wire.py --mode ecu --fixture C:\Dev\Astra_A2WC511R\reports\local\m06_architecture\wire\compiled_wire_fixtures.json --rom C:\Dev\Astra_A2WC511R\work\builds\m06_04\A2WC511R_M06.EXPERIMENTAL_NOT_FLASH_READY.raw.bin
```

Run the host facade against unchanged stock OEM A8 replies:

```powershell
py -3 C:\Dev\Astra_A2WC511R\integrations\m06\replay_wire.py --mode facade --fixture C:\Dev\Astra_A2WC511R\reports\local\m06_architecture\wire\compiled_wire_fixtures.json --rom C:\Dev\SubaruRoms\OEM\A2WC511R.bin
```

Add `--output path.json` to retain the report. Facade results separate native E8
responses from locally generated FE responses and carry
`HOST_FACADE_NO_ECU_EXTENSION`. The replay asserts the exact A8 request was sent,
the stock and patched native response/state/write sequences agree, and the
facade interpretation matches the compiled ECU prototype for identical virtual
inputs. This is not a claim that the stock ECU implements BE.

The underlying fixture executes OEM RX entry 47E24 for received request bytes
and active-TX echo bytes, including routing to the byte parser or transmitter.
It supplies explicit SCI status events, preserving the request buffer during
TX. It does not simulate real serial echo, interrupt delivery, timer scheduling,
silicon timing, or TCU freshness. The host's exact request echo remains modeled.
Each page is a separate observation, never an atomic six-variable sample.

The six replay/guard regression groups also reject altered ROM identity, a
physical-mode request, event/response tampering, changed intermediate native
writes despite identical final state, different input cohorts, and duplicate
page records:

```powershell
py -3 -m unittest discover -s C:\Dev\Astra_A2WC511R\integrations\m06 -p test_replay_wire.py -v
```

Full-ROM acquisition is independently blocked by OEM FF-substitution behavior.
The local status entry fails closed without opening anything:

```powershell
py -3 C:\Dev\Astra_A2WC511R\integrations\m06\acquisition_status.py --require-full-rom-attestation
```

Its expected exit code is 2, with a link to the superseding coverage advisory.
It does not inhibit either offline replay mode. No additional passive TCU
addresses are needed for RAW4; the old full-image acceptance claim is withdrawn.
