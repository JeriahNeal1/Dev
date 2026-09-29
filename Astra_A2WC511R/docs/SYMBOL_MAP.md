# Symbol map

Machine-readable source: `state/SYMBOLS.json`. All addresses are hexadecimal physical SH/ROM addresses, not shortened SSM addresses.

| Address | Name | Kind | Confidence |
|---|---|---|---|
| `0x000147AC` | `sDecodePackedGearRangeByte` | function | USER_REPORTED_RECOVERED_AND_SAVED |
| `0x00024950` | `sUpdateNormalizedGearState` | function | USER_REPORTED_RECOVERED_AND_SAVED |
| `0x00024A9C` | `sSetGearStateE8To6` | function | USER_REPORTED_RECOVERED_AND_SAVED |
| `0x00015A02` | `sTestTcuStatusMask02` | function | USER_REPORTED_RECOVERED_AND_SAVED |
| `0x00015A2C` | `sUpdateTcuDerivedSnapshot` | function | USER_REPORTED_RECOVERED_AND_SAVED |
| `0x00015D46` | `sResetTcuDerivedSnapshot` | function | STATIC_SUPPORTED |
| `0xFFFF4C8D` | `pPackedTargetCurrentGearRange` | RAM:uint8 | STATIC_AND_LIVE_SUPPORTED |
| `0xFFFF4BC1` | `pTargetGearRangeCode` | RAM:uint8 | STATIC_AND_LIVE_SUPPORTED |
| `0xFFFF4BC2` | `pCurrentGearRangeCode` | RAM:uint8 | STATIC_AND_LIVE_SUPPORTED |
| `0xFFFF52E8` | `pNormalizedCurrentGearState` | RAM:uint8 | STATIC_AND_LIVE_SUPPORTED |
| `0xFFFF52E9` | `pNormalizedCurrentGearIndex` | RAM:uint8 | STATIC_AND_LIVE_SUPPORTED |
| `0xFFFF4C75` | `pPackedTargetCurrentGearRangeSource` | RAM:uint8 | STATIC_COPY_VERIFIED |
| `0xFFFF4CA1` | `pTcuDerivedDataValid` | RAM:uint8 | SEMANTICS_UNRESOLVED |
| `0xFFFF4C50` | `pTcuStatusFlags_candidate` | RAM:uint8 | BIT_TEST_VERIFIED_MEANING_UNRESOLVED |
| `0xFFFF4C74` | `pTcuSourceByte74` | RAM:candidate | STATIC_ACCESS_VERIFIED_SEMANTICS_UNRESOLVED |
| `0xFFFF4C76` | `pTcuSourceByte76` | RAM:candidate | STATIC_ACCESS_VERIFIED_SEMANTICS_UNRESOLVED |
| `0xFFFF4C8C` | `pTcuSnapshotByte8C` | RAM:candidate | STATIC_ACCESS_VERIFIED_SEMANTICS_UNRESOLVED |
| `0xFFFF4C8E` | `pTcuSnapshotByte8E` | RAM:candidate | STATIC_ACCESS_VERIFIED_SEMANTICS_UNRESOLVED |
| `0xFFFF4BC0` | `pTcuStateBC0_unknown` | RAM:candidate | STATIC_ACCESS_VERIFIED_SEMANTICS_UNRESOLVED |
| `0xFFFF4BC3` | `pTcuStateBC3_unknown` | RAM:candidate | STATIC_ACCESS_VERIFIED_SEMANTICS_UNRESOLVED |
| `0xFFFF4C95` | `pTcuCopiedSequenceCandidate` | RAM:candidate | STATIC_ACCESS_VERIFIED_SEMANTICS_UNRESOLVED |
| `0xFFFF4CA0` | `pTcuPreviousByteCandidate` | RAM:candidate | STATIC_ACCESS_VERIFIED_SEMANTICS_UNRESOLVED |
| `0xFFFF4C9C` | `pTcuCounter9C_candidate` | RAM:candidate | STATIC_ACCESS_VERIFIED_SEMANTICS_UNRESOLVED |
| `0xFFFF4C9D` | `pTcuCounter9D_candidate` | RAM:candidate | STATIC_ACCESS_VERIFIED_SEMANTICS_UNRESOLVED |
| `0xFFFF4C9E` | `pTcuCounter9E_candidate` | RAM:candidate | STATIC_ACCESS_VERIFIED_SEMANTICS_UNRESOLVED |
| `0xFFFF4C9F` | `pTcuCounter9F_candidate` | RAM:candidate | STATIC_ACCESS_VERIFIED_SEMANTICS_UNRESOLVED |
| `0xFFFF4C60` | `pTcuStatusWord60_candidate` | RAM:candidate | STATIC_ACCESS_VERIFIED_SEMANTICS_UNRESOLVED |
| `0xFFFF4C62` | `pTcuStatusWord62_candidate` | RAM:candidate | STATIC_ACCESS_VERIFIED_SEMANTICS_UNRESOLVED |
| `0xFFFF51E8` | `pEngineSpeed` | RAM:float | PRIOR_IDENTIFICATION_REQUIRES_HOST_RECHECK |
| `0xFFFF51D8` | `pVehicleSpeed` | RAM:float | PRIOR_IDENTIFICATION_REQUIRES_HOST_RECHECK |
| `0xFFFF4F30` | `pManifoldAbsolutePressure` | RAM:float | PRIOR_IDENTIFICATION_REQUIRES_HOST_RECHECK |
| `0xFFFF4FC0` | `pThrottlePlate` | RAM:float | PRIOR_IDENTIFICATION_REQUIRES_HOST_RECHECK |
| `0xFFFF4D54` | `pBrakeCruiseFlags` | RAM:uint8 | PRIOR_IDENTIFICATION_REQUIRES_HOST_RECHECK |
| `0x00018012` | `sGetCruiseCoastFlags` | function | PRIOR_IDENTIFICATION_REQUIRES_HOST_RECHECK |
| `0x00018026` | `sGetCruiseResumeFlags` | function | PRIOR_IDENTIFICATION_REQUIRES_HOST_RECHECK |
| `0x0001804E` | `sGetBrakeFlags` | function | PRIOR_IDENTIFICATION_REQUIRES_HOST_RECHECK |
| `0x0000209C` | `sPull2DFloat` | function | PRIOR_IDENTIFICATION_REQUIRES_HOST_RECHECK |
| `0x00002150` | `sPull3DFloat` | function | PRIOR_IDENTIFICATION_REQUIRES_HOST_RECHECK |
| `0x000079A8` | `sMafCalc` | function | PRIOR_IDENTIFICATION_REQUIRES_HOST_RECHECK |
| `0x00014B20` | `sWgdc` | function | PRIOR_IDENTIFICATION_REQUIRES_HOST_RECHECK |
| `0x00014DC6` | `sTargetBoost` | function | PRIOR_IDENTIFICATION_REQUIRES_HOST_RECHECK |
| `0x000151DC` | `sWgdc_loc` | function | PRIOR_IDENTIFICATION_REQUIRES_HOST_RECHECK |
| `0x000317D8` | `sRevLimStart` | function | PRIOR_IDENTIFICATION_REQUIRES_HOST_RECHECK |
| `0x0003180E` | `sRevLimEnd` | patch_marker | PRIOR_IDENTIFICATION_REQUIRES_HOST_RECHECK |
| `0xFFFF5A30` | `pFlagsRevLim_candidate` | RAM:uint8 | PRIOR_IDENTIFICATION_REQUIRES_HOST_RECHECK |
| `0x0000F928` | `sMemoryReset` | function | PRIOR_IDENTIFICATION_REQUIRES_HOST_RECHECK |
| `0x00000AAC` | `ResetEntry` | function | PRIOR_IDENTIFICATION_REQUIRES_HOST_RECHECK |
| `0x00007A04` | `hMafCalc` | ROM:pointer32be | OLD_VALUE_MATCHES_HISTORICAL_READS |
| `0x000122B4` | `hWgdc` | ROM:pointer32be | OLD_VALUE_MATCHES_HISTORICAL_READS |
| `0x000127E8` | `hRevLimDelete` | ROM:pointer32be | OLD_VALUE_MATCHES_HISTORICAL_READS |
| `0x0000D324` | `hMemoryReset` | ROM:pointer32be | OLD_VALUE_MATCHES_HISTORICAL_READS |
| `0x0000FFF8` | `hMemoryResetLimit` | ROM:pointer32be | OLD_VALUE_MATCHES_HISTORICAL_READS |
| `0x000114E0` | `hTiming_candidate` | ROM:pointer32be | OLD_VALUE_MATCHES_HISTORICAL_READS |
| `0x0001281C` | `hPolf_candidate` | ROM:pointer32be | OLD_VALUE_MATCHES_HISTORICAL_READS |
| `0x00035C3C` | `hTimingPull3D_candidate` | ROM:pointer32be | OLD_VALUE_MATCHES_HISTORICAL_READS |
| `0x00035C40` | `hBaseTimingTable_candidate` | ROM:pointer32be | OLD_VALUE_MATCHES_HISTORICAL_READS |
| `0x0002E538` | `hPolfPull3D_candidate` | ROM:pointer32be | OLD_VALUE_MATCHES_HISTORICAL_READS |
| `0x0002E544` | `hPolfTable_candidate` | ROM:pointer32be | OLD_VALUE_MATCHES_HISTORICAL_READS |
| `0x00002000` | `dCalId` | ROM:string | IDENTITY_VERIFIED_IN_ARCHIVED_READS |
| `0x000CDAD8` | `dEcuId` | ROM:5bytes | IDENTITY_VERIFIED_IN_ARCHIVED_READS |
| `0x000FFFF8` | `RomEndPointer_F60C` | ROM:pointer32be | PRIOR_RAW_BYTES_VERIFIED |
| `0x000FFFFC` | `CalIdPointer` | ROM:pointer32be | PRIOR_RAW_BYTES_VERIFIED |
| `0x000E1000` | `pRomHole_candidate` | ROM:allocation_candidate | NOT_PROVEN_FREE |
| `0xFFFF7400` | `pRamHole_candidate` | RAM:allocation_candidate | NOT_PROVEN_FREE |

See each JSON entry for provenance, scaling and qualifications. No current live values are encoded by this map.
