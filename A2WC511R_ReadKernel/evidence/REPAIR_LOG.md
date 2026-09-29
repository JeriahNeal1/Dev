# Acquisition-tool repair journal

All experiments in this tree use local files and the separately named fake provider. The real ECUFlash application and OpenPort DLL have not been executed by this project.

| Symptom | Cause | Narrow fix | Retest |
| --- | --- | --- | --- |
| First assembly rejected PC-relative expressions and distant MOV.W constants | The SH assembler requires the literal pool in the same section; MOV.W reaches only 510 bytes | Keep the pool after the executable body in `.text`; use MOV.L for distant constants | `build/attempt_03` assembled 319 SH-2E instructions |
| Linker rejected `elf32-shbig` | This pinned KPIT build names its ELF output `elf32-sh` | Remove the unsupported format name; retain big-endian assembler and `-EB` linker options; inspect ELF bytes | ELF32 MSB, EM_SH=42, SH2E flags=11 |
| Initial native fake host compilation rejected warnings | Strict MSVC warning/ABI checks exposed local host code issues | Preserve failed native_01; repair in the host source and rebuild native_02 | Native offline controls and identity rejection passed |
| Fake message boundaries were stronger than the J2534 stream contract | A single complete message hid possible fragmentation and status events | Qualify bounded receive assembly using fragmented replies and documented status events before deriving a physical variant | See final host qualification; no physical provider loaded |

`build/reproducibility_01` independently rebuilt the object from the same source and pinned tools. Its binary and ELF match `attempt_03` byte-for-byte. Source/build hashes and the complete overwritten RAM map are in `evidence/build/ARTIFACT_REVIEW.json`.

No error was repaired by suppressing an unsupported instruction, returning a made-up kernel reply, relaxing the fixed upload/read ranges, or substituting data based on a CRC.
