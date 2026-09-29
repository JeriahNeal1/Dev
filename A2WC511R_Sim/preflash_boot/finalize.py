"""Publish compact evidence pointers for a completed immutable boot regression run."""
from pathlib import Path
from hashlib import sha256
import json
import sys

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
OUT=Path(r'C:\Dev\Astra_A2WC511R\reports\local\prehardware\boot')


def main():
    run=Path(sys.argv[1]).resolve()
    if run.parent != OUT.resolve():raise SystemExit('Run must be in the authorized new boot reports subtree')
    r=json.loads((run/'regressions.json').read_text());s=json.loads((run/'stock.json').read_text())
    c=json.loads((run/'stock_vs_frozen_m07.json').read_text())
    if r['status']!='PASS' or c['status']!='CONDITIONAL':raise SystemExit('Unexpected evidence status')
    for dep in s['dependencies']:
        if sha256(Path(dep['path']).read_bytes()).hexdigest()!=dep['sha256']:raise SystemExit('Dependency changed after run')
    report=dict(schema=1,status='CONDITIONAL',scope='Actual reset prefix; incomplete boot/SSM/timing validation',
                regression_checks_passed=r['check_count'],run_directory=str(run),stock=s['image'],candidate=c['candidate']['image'],
                reset=s['reset'],milestones=s['milestones'],stop=s['stop'],coverage=s['coverage'],
                equal_stock_candidate_prefix=c['equal_frontier'] and not c['differences'],explicit_allowlist=c['explicit_allowlist'],
                gates={'reset_prefix':'PASS_UNDER_DECLARED_SCENARIO','complete_boot':'CONDITIONAL','SSM_readiness_from_reset':'CONDITIONAL',
                       'invalid_sensor_recovery':'CONDITIONAL_NOT_REACHED','admissible_ISR_execution':'CONDITIONAL_MODEL_FRONTIER',
                       'silicon_watchdog_clock_timing':'PHYSICAL/BENCH REQUIRED','frozen_M07_residency':'FAIL_UNCHANGED'},
                faults=r['faults'],dependencies=s['dependencies'],assumptions=s['assumptions'],
                next_offline_step='Close actual4B3E SYSCR2 CKSEL transition CPU/peripheral clock model and four following NOPs, then extend only reached peripheral paths.',
                physical_operations=False)
    (OUT/'BOOT_CONTRACT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    (OUT/'BOOT_AUDIT.md').write_text('''# Prehardware reset harness â€” CONDITIONAL

The actual stock1MiB ROM retires **57,658 instructions at801unique PCs** from reset before the explicit clock-change boundary at`4B4C` (`SYSCR2=3C88`). Bus/PFC setup, both HCAN configuration paths, boot-buffer setup, the OEM boot wait, application entry, VBR/FPSCR setup and SP relocation have executed under the declared virtual scenario. Application SCI/SSM readiness and later OEM RAM initialization have not been reached.

All64new regression checks passed. The frozen checksum-corrected M07 one-page image has equal ordered RAM/MMIO writes, control transfers and terminal architectural state up to the same stop, with an empty allowlist. This prefix equality does not approve residency or unexecuted feature behavior. M07 ownership remains FAIL.

The run uses explicit NMI/port inputs, power-on RAMA5, idle CAN/no traffic, and16synthetic CPU cycles per instruction. These are deterministic assumptions, not physical telemetry or verified silicon timing. WDT is in interval mode for this prefix. NMI admission is detected, then execution stops before an unmodeled exception; sensor recovery and SCI startup remain untested from reset. Unknown MMIO/opcodes, wrong ROM identity, invalid SP and unexpected branch mutations fail visibly.

Reproduction, API and limitations: [simulator README](C:/Dev/A2WC511R_Sim/preflash_boot/README.md). Machine evidence: [BOOT_CONTRACT.json](BOOT_CONTRACT.json). Immutable run: [regressions.json]('''+run.name+'''/regressions.json). Primary evidence: [Renesas SH7058 hardware manual](https://www.renesas.com/en/document/mah/sh-2e-sh7058-f-ztat-tm-hardware-manual), sections5.2,6.2,7,13,16,21,22. The independent new layer adds ten reached ISA forms; the frozen75-form core retains its original hash.

Next bounded offline step: model the actual CKSEL transition at4B3E using verified CPU/peripheral phase and settling constraints, then admit only subsequently reached peripheral initialization. No provider, hardware, original IDB, earlier ROM candidate or frozen report was changed.
''',encoding='utf-8')
    paths=[*HERE.glob('*.py'),HERE/'manual_evidence.json',HERE/'README.md',OUT/'BOOT_CONTRACT.json',OUT/'BOOT_AUDIT.md']
    paths += [p for p in run.rglob('*') if p.is_file()]
    files=[dict(path=str(p.resolve()),sha256=sha256(p.read_bytes()).hexdigest(),size=p.stat().st_size) for p in sorted(paths)]
    (OUT/'BOOT_FILES.json').write_text(json.dumps(dict(schema=1,files=files),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='CONDITIONAL',files=len(files),report=str(OUT/'BOOT_CONTRACT.json'))))


if __name__=='__main__':main()
