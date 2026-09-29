"""Hash-check frozen final build against executed bytes and publish local handoff."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
HANDOFF = Path(r"C:\Dev\Astra_A2WC511R\reports\local\simulator")
BUILDS = Path(r"C:\Dev\Astra_A2WC511R\work\builds")
ANCHOR = ROOT / "runs/20260925T202126.230415Z/coverage.json"
DIFFERENTIAL = ROOT / "runs/20260925T201917.102870Z_differential/coverage.json"


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    name = datetime.now(timezone.utc).strftime("final_%Y%m%dT%H%M%S.%fZ")
    out = ROOT / "runs" / name
    out.mkdir(parents=True, exist_ok=False)
    anchor = json.loads(ANCHOR.read_text())
    differential = json.loads(DIFFERENTIAL.read_text())
    if anchor["status"] != "PASS" or differential["status"] != "PASS":
        raise RuntimeError("Cannot summarize a failed validation as passing")
    builds = {}
    for build_name in ("m0_experimental_02", "m0_experimental_03", "m0_final_05", "m0_final_repeat_06"):
        build = BUILDS / build_name
        manifest = json.loads((build / "manifest.json").read_text())
        artifacts = {}
        for artifact, expected in manifest["artifacts"].items():
            if artifact.endswith((".bin", ".elf", ".o")):
                actual = digest(build / artifact)
                if actual != expected:
                    raise RuntimeError(f"Build manifest mismatch: {build_name}/{artifact}")
                artifacts[artifact] = actual
        builds[build_name] = dict(path=str(build), manifest_sha256=digest(build / "manifest.json"),
                                  artifacts=artifacts)
    payload_name = "m0.EXPERIMENTAL_UNAPPROVED.code.bin"
    elf_name = "A2WC511R_DiagnosticM0.EXPERIMENTAL_UNAPPROVED.elf"
    for artifact in (payload_name, elf_name):
        if len({build["artifacts"][artifact] for build in builds.values()}) != 1:
            raise RuntimeError(f"Executed/final binary identity differs: {artifact}")
    final_payload = builds["m0_final_05"]["artifacts"][payload_name]
    if final_payload != differential["code_sha256"]:
        raise RuntimeError("Frozen payload is not the executed payload")
    if digest(ROOT / "sh2e.py") != differential["source_hashes"]["sh2e.py"]:
        raise RuntimeError("Interpreter changed since differential execution")
    # Supplemental whole-state assertion for the four scripted changes, on final05.
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_differential.py", "-k", "scripted", "-v"]
    check = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (out / "supplemental_test_log.txt").write_text("Command: " + repr(command) + "\n" + check.stdout, encoding="utf-8")
    if check.returncode:
        raise RuntimeError("Supplemental scripted change checks failed")
    report = {
        "schema": 1, "status": "PASS_WITH_EXPLICIT_COVERAGE_LIMITS",
        "classification": "OFFLINE_FUNCTION_AND_EXPERIMENTAL_WRAPPER_VALIDATION; NOT_READY_TO_FLASH",
        "authoritative_build": str(BUILDS / "m0_final_05"), "authoritative_payload_sha256": final_payload,
        "authoritative_elf_sha256": builds["m0_final_05"]["artifacts"][elf_name],
        "build_provenance": builds,
        "identity_conclusion": "Executed02, reviewed03, frozen05 and repeat06 payload and ELF are byte-identical. 1024-pair execution is reused by exact SHA-256 identity; no claim of four distinct execution runs.",
        "stock_rom_sha256": anchor["rom"]["sha256"],
        "anchor_report": str(ANCHOR), "differential_report": str(DIFFERENTIAL),
        "anchor_tests": anchor["tests"], "differential_tests": differential["tests"],
        "stock_decoder_cases": 1792, "stock_status_cases": 256,
        "differential_pairs": 1024, "publication_init_cases": 10, "scripted_second_read_changes": 4,
        "observed_max_extra_stack_bytes": 124, "extra_executed_instructions_range": [291, 483],
        "source_provenance": {str(p.relative_to(ROOT)): digest(p) for p in ROOT.rglob("*.py")},
        "coverage": ["43/43 stock decoder PCs and8/8 conditional outcomes", "10/10 status helper PCs",
                     "all51 supported opcode forms exercised by architecture/anchor tests",
                     "all16 GPRs,SR,MACH,MACL,PR and continuation equal to stock at each paired boundary",
                     "OEM decoder traces/data effects identical; all other RAM checked outside declared diag32/transient stack",
                     "observer32byte state independently checked; odd/even publication verified at every state store",
                     "incorrect register restoration, unknown opcode and publication-order mutations fail visibly"],
        "limitations": differential["limitations"] + [
            "No FPU/interrupt/peripheral/cycle behavior is modeled; unknown opcodes/MMIO and uninitialized RAM fail",
            "Reset PC/SP bytes decoded, not full reset execution",
            "No virtual logger transport or actual RomRaider/J2534 access",
            "No physical timing, mechanical engagement, calibration safety or communication freshness acceptance"],
        "reproduce": ["cd C:\\Dev\\A2WC511R_Sim", "py -3.14 run_validation.py", "py -3.14 run_differential.py"],
    }
    (out / "final_validation.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    destination = HANDOFF / name
    destination.mkdir(parents=True, exist_ok=False)
    for source in (out / "final_validation.json", out / "supplemental_test_log.txt", ROOT / "README.md"):
        shutil.copy2(source, destination / source.name)
    summary = f"""# Simulator final handoff

The isolated simulator at `C:\\Dev\\A2WC511R_Sim` validates actual stock bytes and the frozen experimental diagnostic payload. It does not accept a real ECU allocation or flash.

- 31 core/anchor tests pass; all51 supported integer/system-transfer forms exercised.
- Stock decoder:1792 cases, all43 instruction addresses and both outcomes of all4 conditional branches. Status helper:256 cases, all10 instructions.
- Frozen build: `{BUILDS / 'm0_final_05'}`. Payload SHA-256 `{final_payload}`.
- 1024 stock/compiled-wrapper pairs pass at direct and actual1193A→11940 callsite boundaries. All16 general registers, SR/MACH/MACL/PR, continuation and OEM data effects match.
- All diagnostic state writes obey odd/even publication;10 explicit init/reinit cases and4 explicitly modeled second-read changes pass. Observer freshness stays UNKNOWN.
- Observed extra stack124bytes;291..483 extra executed instructions. Separate task/dispatcher frames add8bytes; RTOS/interrupt headroom and cycle/scheduler timing remain unproven.

Executed02, reviewed03, frozen05 and repeat06 payload/ELF identities were checked byte-for-byte by SHA-256. The full pair test is reused by identical binary identity. The final JSON records exact manifests, logs and source hashes.

Reproduce from the simulator directory with `py -3.14 run_validation.py` and `py -3.14 run_differential.py`. Each run preserves reports under a new UTC directory. Unsupported opcodes, peripherals, uninitialized RAM and memory-policy violations stop visibly.

Final manifest: `{destination / 'final_validation.json'}`

Anchor report: `{ANCHOR}`

Differential report: `{DIFFERENTIAL}`

No physical device or real RomRaider/J2534 provider was accessed. Full boot, FPU, interrupts, watchdog, DMA, analog behavior, transmission mechanics and active-control safety remain outside coverage.
"""
    (destination / "HANDOFF.md").write_text(summary, encoding="utf-8")
    print(json.dumps({"status": report["status"], "handoff": str(destination / "HANDOFF.md"),
                      "manifest": str(destination / "final_validation.json"), "payload_sha256": final_payload}))


if __name__ == "__main__":
    main()
