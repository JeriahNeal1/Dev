# reproducible_build

PASS. Final05 and repeat06 fresh output trees have bit-identical ELF, objects, assembly, stack-usage and code payload without functional normalization. Only linker-map absolute output directory prefixes differ. Sources/tools/flags/commands are pinned in validation/final_build/manifest.json. Build CLI rejects dirty payload/source associations and fails native command errors. SharpTuneRC2-12 source was built side-by-side; private offline hardening diffs and original RC2-10 provenance are retained.
