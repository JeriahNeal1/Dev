# Chronological project reconstruction

This is a reconstruction from the available conversation and artifacts, not a complete transcript. Filename timestamps are retained as labels; a filename date, upload date and conversation date may differ. Later evidence supersedes earlier hypotheses only when explicitly recorded below.

## 1 — Hardware setup and mechanical investigation
User developed the2005OBXT/5EAT around VF52,3-port boost control,3-inch MAF intake, aftermarket BOV and Innovate ECB-1. Investigated boost noise/leaks, repaired the stripped flange attachment with a through-bolt, and reported reaching16psi while smoke remained. Sensor installation, fuel-line identification, exhaust work and cosmetic work preceded the firmware effort. No final mechanical sign-off is archived.

## 2 — Logger/wideband and calibration experiments
Configured Innovate serial output, LM Programmer and RomRaider (Innovate AFR/MTS entries). Connectivity/scaling/channel-rate problems arose; AFR vs lambda display was discussed. Multiple engine logs were supplied, including shutdown and unintended stalls. User requested aggressive track-focused tuning and ALS. Historical R3 timing/POLF exports and summaries are bundled for provenance, not automatic application. Full earlier tuning changes/current ECU flash state cannot be reconstructed solely from the provided excerpts.

## 3 — MerpMod source-port decision
A2WC511R was absent from old Gratis prebuilt compatibility lists. The plan became reverse-engineering this exact ROM and building a source patch with HEW/GNUSH, SharpTune and SubaruDefs. A starter ZIP proposed source pins and non-flashable target templates. It contained guessed family addresses and explicit blockers; it was not an installed port.

## 4 — Windows build environment
User installedHEW and confirmedKPIT GNUSH visible; also hadGNUSH13.01,GNUH8,e2studio,SharpTune and IDAPro9.4Beta. The retained HEW log `Pasted text(20260823-200955).txt` reports MerpModv0.1-73-g8720d20 and SharpTune0.1.9-RC2-10-gfcf9fdb. It selectedA8DH202X/Gratis_Debug, linked, then failed to find the target ROM/patched.bin. The final0Errors banner was misleading about custom-phase success. No matchingA2WC511R firmware was thereby validated.

## 5 — IDA loading, identity and hooks
Loaded local `C:\Dev\SubaruRoms\OEM\A2WC511R_STOCK_ROMRAIDER.bin` as binary0..100000, RAMFFFF0000..FFFFC000, usingSH4B/SH7058S preset. Initially decoded CALID/data as instructions, producingMakeCode issues. Defined2000 as9-byteCALIDstring. Verified reset entryAAC, stackBFA0, tailF60C/2000 pointers. Corrected14B20 from mistakenrevlim name toWGDC;revlim317D8. User tested five key pointers and all matched. Identified brake/cruise bit tests, RPM/speed/MAP/throttle-family RAM. Function membership/name success was distinguished from semantics.

## 6 — First gear variables
Found many pointer-literal loads ofFFFF52E9 and adjacentE8. Code boundedE9 to a1–6table index despite five usable gears. Static calculated-gear paths wroteE8/E9 together for1–5 andE8=5/E9=6on another path. First E8/E9 live log showedP/N6/0 andReverse1/1, same asDrive1. User's alternate 'mode vsgear' hypothesis was tested and rejected. Names were made neutral normalized-gear state/index.

## 7 — Trace raw gear input
TracingR10 was initially hindered by undefined Pythonhelpers and absent persistent code. Narrowed to24972loadingFFFF4BC2 and24978mov.b@r3,r10 in aJSRdelay slot. Identified24950functionprologue and24A9Cend. AddedBC2rawloggerparameter (24-bitSSMFF4BC2). Corrected log20260824_131619 gave0P/N,7Reverse,1..5forward;131151washeader-only. Single-row mismatches were treated as scheduling/polling evidence, not new gearcodes.

## 8 — Packed source and target/current pair
Producer147AC readsFFFF4C8D. High nibbledecodesBC1,lowBC2:0..7stored,8->0,9..Fholdlast. Addedpacked/BC1/BC3/BC0channels. Log20260824_143124 contains6453rows and transitions supporting upperrequested/target vslowerreportedcurrent:32->33,43->44,54->55 and successive targetdownshiftswhilecurrent5. Packed88/77/00retainP/R/Ndistinction. Actual gear engagement and freshness remain separate.

## 9 — IDA database repair and callers
Persisted known entry instructions;add_func now succeeded for147AC,24950,24A9C. Added callerinstructions before manualxref to resolve 'no defined item at from'. Later recovered15A02and15A2Cexactbounds. Manual saves worked. Python `ida_kernwin.save_database()` did not; stopusingit. Data xrefs in literal pools were distinguished fromJSR callers.

## 10 — Snapshot and monitoring path
Scan output214919and220054located4C75->4C8Dcopy within15A2Cupdater; source4C74/75/76and downstream4C8C/8D/8E. Found reset pathzeroing snapshots, statusbit4C50:02, CA1set/test/clear, counter/sequence-related fields4C9C..4CA1. Earlier messages overpromotedCA1to'valid';thishandoffexplicitlydowngradesglobalfreshnesspendingfullflowproof. Preparedsix-channelvalidityXML; matchingnewCSVnotreceived.

## 11 — Scope preserved and transfer
User considered removing OEM exhaustO2s and using onlyexternalwideband, then deferred it. Wants allfutureworkinlocalCodexwithdirectIDA/toolaccess. Thisarchive preserveslatestlogger,rawartifacts,source-versiondistinctions,andcurrentknownunknowns. Nextworkislocalinventory/statusvalidation/memory-and-hookaudit,notenabledALSorflash.

## Additional separately retrieved records
`evidence/library_unmerged` includes same-car Part1/Step1 reports with a different baselinehash/path and concernsaboutimplausibleboostchannels. Their chronologicalrelationshiptocurrentportwasnotestablished. Reconcileagainstlocalwork;do notsilentlyapplyorignorenewmechanical/loggingblockers. SeeEVIDENCE_GUIDE.
