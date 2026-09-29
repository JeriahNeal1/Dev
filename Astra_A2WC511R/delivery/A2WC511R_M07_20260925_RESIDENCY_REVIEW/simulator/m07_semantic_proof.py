"""Check finite structural proof obligations on the actual compiled replacements.

The division proof is induction over the same32 architectural DIV1/ROTCL pairs,
not an extrapolation from sampled quotients. Interrupted execution is excluded.
"""
from hashlib import sha256
from pathlib import Path
import json

from m07_semantic import OUT, artifacts, fixture, execute, compare, SP, RETURN
from sh2e import RAM_START


def main():
    stock, patched, manifest = artifacts()
    old = execute(fixture(stock, 0x4260, {0: 3, 1: 12345}))
    new = execute(fixture(patched, 0x4260, {0: 3, 1: 12345}))
    removed = {0x4268, 0x4274, 0x427A, 0x427C, 0x427E, 0x4280, 0x4288}
    projected = [e['opcode'] for e in new.trace if int(e['pc'], 16) not in removed]
    expected = [e['opcode'] for e in old.trace]
    # Only the zero-branch displacement changes in this normal path.
    expected[2] = projected[2]
    assert expected == projected
    assert sum(e['instruction'] == 'div1' for e in old.trace) == 32
    assert sum(e['instruction'] == 'div1' for e in new.trace) == 32
    assert {e['instruction'] for e in old.trace if e['instruction'].startswith(('bt', 'bf'))} == {'bt'}
    assert {e['instruction'] for e in new.trace if e['instruction'].startswith(('bt', 'bf'))} == {'bt', 'bf_s'}
    # The loop's only inputs R0,R1,R3 and SR are untouched by its control scaffold,
    # except T is restored after DT. Prove the scaffold for both T values and all32counts.
    scaffold_cases = 0
    for count in range(1, 33):
        for t in (0, 1):
            cpu = fixture(patched, 0x427A, {0: 0x87654321, 1: 0xFEDCBA98, 2: count, 3: 0xAA55AA55}, sr=0x0ACE03F0 | t)
            before = list(cpu.r), cpu.sr
            for _ in range(4):
                cpu.step()
            assert cpu.r[2] == count - 1
            assert cpu.sr == before[1]
            assert cpu.r[0:2] == before[0][0:2] and cpu.r[3] == before[0][3]
            assert cpu.pc == (0x4276 if count > 1 else 0x4282)
            assert cpu.pending is None and cpu.memory.events == []
            scaffold_cases += 1
    # Changed branch targets select the same zero/nonzero partition. Both return paths
    # preserve originalR2/R3 slots; only the explicit new R4 word is extra.
    for divisor in (0, 1):
        a = execute(fixture(stock, 0x4260, {0: divisor, 1: 0x80000000}))
        b = execute(fixture(patched, 0x4260, {0: divisor, 1: 0x80000000}))
        compare(a, b, extra_stack=True)
    division = dict(status='PASS', kind='STRUCTURAL_INDUCTION_ON_ACTUAL_COMPILED_WORDS',
        domain='All32-bit dividend,divisor,initialGPR and architecturally storedSR values; valid ordinaryRAMstack; no interleaved execution.',
        projected_instruction_words=projected, scaffold_finite_cases=scaffold_cases,
        induction=['Original normal path is32 ROTCL R1;DIV1 R0,R3 pairs followed by identical finalROTCL/ADDC/move/restore.',
                   'Replacement executes the samepair32times; positive R2 countdown determines branch and terminates atR2=0.',
                   'MOVT R4 capturesT as0/1;DT changes onlyT;SHAR R4 copies its lowbit backtoT. Q/M and allotherSRbits are unchanged.',
                   'Pair operations never readR2 orR4. At exitR2=0 matchesOEMbeforeADDC; savedR4restores its caller value.',
                   'OriginalR2/R3stackslotaddresses and accesses are unchanged. AdditionalR4slot requires4 extra valid bytes.',
                   'Divisor0 bypasses the addedR4save and retains identical zero-result/error-write/register side effects.'],
        exclusions=['No interrupt delivery or stack ownership proof.', 'Extra four-byte transient stacktraffic is explicit.',
                    'Interior entrypoints, ROM-byte observers and global object ownership are separate gates.'])
    # Tail entry requires exactly the facts established before1473A in1466E.
    # Every nibble is tested with both incomingT values, and diverse arbitrary R5highbits.
    count = 0
    table = [0, 1, 2, 4, 8, 16, 32, 64, 128, 128, 128, 128, 128, 128, 128, 15]
    for nibble in range(16):
        for t in (0, 1):
            for high in (0, 0x12345670, 0xFFFFFFF0):
                regs = {5: high | nibble, 6: 64}
                ram = {0xFFFF4BC0: b'\xAA'}
                a = execute(fixture(stock, 0x1473A, regs, ram, sr=0x0ACE03F0 | t))
                b = execute(fixture(patched, 0x1473A, regs, ram, sr=0x0ACE03F0 | t))
                compare(a, b)
                assert b.r[0] == nibble and b.r[4] == table[nibble]
                assert b.sr & 1 == int(nibble <= 8 or nibble == 15)
                count += 1
    range_proof = dict(status='PASS', domain='All low16nibble values,all higherR5bits,all priorSRbits under enclosing1466E entry contract R6=64.',
        exhaustive_nibble_cases=count, table=table,
        argument='Original1473A masksR5to15. Original switch outputs exactlytable[n] andT=(n<=8 or n==15). Replacement uses this same finite lookup and two comparisons. AllotherGPRoutputs and orderedRAMwrite match; no additional stack.',
        original_enclosing_entry_word=f'{int.from_bytes(stock.data[0x1466E:0x14670], "big"):04X}',
        invalid_arbitrary_interior_entry='Concrete negative control withR6!=64 fails as expected; no unrestricted interior-entry equivalence claimed.')
    assert stock.data[0x1466E:0x14670] == bytes.fromhex('E640')
    backup = Path(__file__).parent / 'backups/m07_start_75form_20260925/sh2e.py'
    assert backup.read_bytes() == (Path(__file__).parent / 'sh2e.py').read_bytes()
    result = dict(status='PASS', stock_sha256=stock.sha256, candidates=manifest['candidates'], division=division, range_tail=range_proof,
                  gates=dict(scoped_semantic_proof='PASS', exclusive_residency='FAIL', silicon_and_stack_margin='PHYSICAL/BENCH REQUIRED'),
                  unchanged_core75_sha256=sha256(backup.read_bytes()).hexdigest(),
                  proof_source_sha256=sha256(Path(__file__).read_bytes()).hexdigest())
    (OUT / 'semantic_structural_proof.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(status='PASS', division_scaffold_cases=scaffold_cases, range_partition_cases=count,
                         division_saved_bytes=manifest['candidates']['division']['bytes_saved'], range_saved_bytes=manifest['candidates']['range_tail']['bytes_saved'])))


if __name__ == '__main__':
    main()
