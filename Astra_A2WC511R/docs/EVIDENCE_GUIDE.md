# v3 precedence note

Current host authorization and run order are in `../AGENTS.md`, `../state/RUN_CONTRACT.md` and `CLI_SETUP.md`. Actual uploaded source/binary identities superseding older unknowns are in `DEV_SNAPSHOT_AUDIT.md`. Keep the technical details below, but do not reimpose historical per-action host permission requests or stop after the first milestone. Physical actions remain human-controlled.

---

# Evidence guide and provenance

`state/EVIDENCE_MANIFEST.json` is the exhaustive list of original **mounted files** copied for this handoff, with exact size/hash. `evidence/original/` is immutable reference, not a build output folder. `definitions/` contains convenient identical working references to the latest logger XML, editor ECU definitions, and loggerDTD.

## Highest-value originals
- `Pasted text(20260823-200955).txt`: full historicalHEWbuildoutput; target/version/post-buildfailure.
- `Pasted text(20260824-000257).txt`,000616,001045,002404: intermediateIDAexploration.
- `Pasted text(20260824-195706).txt`: mixed console/earlierassistantmaterial; do not treat every paragraph asrawmachineoutput.
- `Pasted text(20260824-202747).txt`,203429: geardecoder/callerwork.
- `Pasted text(20260824-214919).txt`: broadliteral/usertrace,sourcecopy,resetandconsumers.
- `Pasted text(20260824-220054).txt`: snapshot/status trace, counter paths and callsites.
- `romraiderlog_20260823_193409.csv`: initialE8/E9-only15101samples.
- `romraiderlog_20260824_131151.csv`: headeronly,notnegativeevidence.
- `romraiderlog_20260824_131619.csv`: rawBC2plusnormalizedoutputs4996samples.
- `romraiderlog_20260824_143124.csv`: packed/nibble/normalized/RPM/speed6453samples.
- OtherAug17/Aug18CSVs: engine-calibration/logginghistory; notcurrentvalidityexperiment.
- `ECUFlashReadRaw(1).bin` and `ECUFlashReadRR(1).bin`: historicalreadssameCALID,uncertainmodificationstate. Do notflash.
- `MerpMod_A2WC511R_Starter.zip`: historicalplannedpins/templates. Anextractedcopyisunderlegacy_unvalidated;neverautorunitssetup.
- `A2WC511R_R3_*` tables/summary: historicalproposals,notapprovedcurrentcalibration.
- Photos/screenshots: retainedasoriginals; manyhavenon-descriptnamesandmayincludeoldsettings. Viewselectivelywithoutassumingallarecurrent.

## Local-only / missing
No completeIDB/I64orlateststock-labelledROMwasmounted. No latestsix-channelvalidityCSV. NocompleteSubaruOEMmanual/PCBcircuitdiagram. No licensedIDAorcompilerbinary. No literalcompletechattranscript. The supplied reconstructedhistoryandledgerdo notsubstituteforcheckingthosehostfiles.

## Library additions, segregated
`library_unmerged/STEP1_LOG_REVIEW_AND_NEXT_STEP.md`, `STEP1_2_LOG_REVIEW_AND_NEXT_STEP.md`, and `PART1_STABLE_CHANGE_GUIDE.md` were found in the user'sLibraryduringhandoffresearch. Theyconcernsamecarbutbaseline/timelineintegrationisunknown. Oneclaimsstockhash22d52a... andfolderunderJeriahN;earlierHEWusesJeriah Neal. Theyreportproblematicboostmeasurementsandnoauthorizationtotune. Readandcompare,don'tapplychangeswithoutreconciliation.

## Evidence citation convention for Codex
Cite local path, line range orCSVrow/time, binaryoffset/length/hash, and sourcerepocommit:path. Preserveoriginalterminaloutputandwriteinterpretationseparately. Whenanimagetargetisnecessary,recorditsfilenameandwhatwasvisible;donotinventOCRtext. AttachrawoutputJSON/CSVreportsoncepernewexperiment.
