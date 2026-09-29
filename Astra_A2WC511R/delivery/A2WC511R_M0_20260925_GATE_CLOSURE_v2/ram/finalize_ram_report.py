"""Package the RAM investigation's scoped status; never change a release gate."""
from pathlib import Path
import hashlib
import json

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    # Editorial spacing in the report only; machine addresses remain integers.
    p = OUT/'RAM_OWNERSHIP_REVIEW.md'
    s = p.read_text(encoding='utf-8')
    for old,new in [
        ('about23.2%', 'about 23.2%'), ('plus18', 'plus 18'), ('passes65,536', 'passes 65,536'),
        ('every65,536-state', 'every 65,536-state'), ('allocates32', 'allocates 32'),
        ('offset31', 'offset 31'), ('Whole1MiB', 'Whole 1 MiB'), ('all32', 'all 32'),
        ('the147-byte', 'the 147-byte'), ('called by F928 with FFF4/FFF8', 'called by F928 with FFF4/FFF8'),
        ('executes0x24BF', 'executes 0x24BF'), ('both5AA5A55A andA55A5AA5', 'both 5AA5A55A and A55A5AA5'),
        ('programs DMA0', 'programs DMA0'), ('destination315A', 'destination 315A'),
        ('source310A', 'source 310A'), ('destinationSCI1', 'destination SCI1'),
        ('caller45D3A', 'caller 45D3A'), ('TX6368', 'TX 6368'), ('RX6390', 'RX 6390'),
        ('count20', 'count 20'), ('ROM4880', 'ROM 4880'), ('containsFFFF119C', 'contains FFFF119C'),
        ('below119C', 'below 119C'), ('state+4', 'state + 4'), ('there; F928', 'there; F928'),
        ('with12-byte', 'with 12-byte'), ('leafFA58', 'leaf FA58'), ('helpers2088', 'helpers 2088'),
        ('indices; producer', 'indices; producer'), ('at100', 'at 100'), ('covers80', 'covers 80'),
        ('Its1,024', 'Its 1,024'), ('sentinels2CFC andBFFC', 'sentinels 2CFC and BFFC'),
        ('Descriptor4968', 'Descriptor 4968'), ('task9', 'task 9'), ('stateFFFF11E4', 'state FFFF11E4'),
        ('entry6580', 'entry 6580'), ('priority2', 'priority 2'), ('capacity2', 'capacity 2'),
        ('calls3A28', 'calls 3A28'), ('ID9', 'ID 9'), ('entry101A4', 'entry 101A4'),
        ('index2', 'index 2'), ('at1019C', 'at 1019C'), ('handler5EA0', 'handler 5EA0'),
        ('atFFFFF718', 'at FFFFF718'), ('toD936', 'to D936'), ('index0', 'index 0'),
        ('byte31F2', 'byte 31F2'), ('word31F0', 'word 31F0'), ('modulo4', 'modulo 4'),
        ('equals2', 'equals 2'), ('every8', 'every 8'), ('calls3,11,19', 'calls 3, 11, 19'),
        ('atDABA andDBF0', 'at DABA and DBF0'), ('indices21 and23', 'indices 21 and 23'),
        ('divider8', 'divider 8'), ('compare2499', 'compare 2499'), ('yields20,000', 'yields 20,000'),
        ('and160,000', 'and 160,000'), ('At3BCC/3BCE', 'At 3BCC/3BCE'),
        ('is2', 'is 2'), ('returns0', 'returns 0'), ('dispatch,3DC8', 'dispatch, 3DC8'),
        ("state4", "state 4"), ('Dispatcher3930', 'Dispatcher 3930'),
        ('at43E8', 'at 43E8'), ('at43DE', 'at 43DE'), ('above64', 'above 64'),
        ('take447C', 'take 447C'), ('sizes0..64', 'sizes 0..64'), ('select17', 'select 17'),
        ('at4438', 'at 4438'), ('exactly4432,442E,...43F2', 'exactly 4432, 442E, ... 43F2'),
        ('toE1000', 'to E1000'), ('records94', 'records 94'), ('same7400/E1000', 'same 7400/E1000'),
        ('the32-byte', 'the 32-byte'), ('sections9.2.2,10.2,14.2/14.4 and24.1/24.2',
                                         'sections 9.2.2, 10.2, 14.2/14.4 and 24.1/24.2'),
        ('at71CA0/71CC4/71CE4', 'at 71CA0/71CC4/71CE4'), ('end736D', 'end 736D'),
        ('then4BBE', 'then 4BBE'), ('atBFF8', 'at BFF8'), ('useB4E0', 'use B4E0'),
        ('wrap at100', 'wrap at 100'), ('stackBFF8', 'stack BFF8')
    ]:
        s = s.replace(old,new)
    p.write_text(s, encoding='utf-8')
    inputs = [OUT/'ram_path_audit.json', OUT/'ram_path_audit.py', OUT/'static_inventory.json',
              OUT/'ram_static_inventory.py', p,
              OUT.parent/'rom/reachability.json',
              OUT.parent/'runtime/20260925T211558.608898Z_gate_closure_runtime/ram_pattern_FA58.json',
              OUT.parent/'runtime/20260925T211558.608898Z_gate_closure_runtime/dma_setup_C31E.json']
    assert all(x.is_file() for x in inputs)
    report = dict(target='A2WC511R', exact_required_span=[0xffff7400,0xffff7420],
                  required_bytes=32, frozen_build='m0_final_05',
                  identified_software_paths='PASS_SCOPED',
                  exclusive_ram_ownership='FAIL_TO_ESTABLISH',
                  physical_validation='NOT_PERFORMED',
                  production_release_allowed=False,
                  approved_alternative_ram_location=None,
                  software_gap='Unresolved CPU indirect control/address paths and full interrupt/context invariants; literal/DMA bounds are insufficient for exclusive ownership.',
                  smallest_physical_observation='Candidate32 and boundary access/writer-PC observation after boot/lazy-init across qualified operating/reset modes, plus actual stack nesting, DMA destinations and timer service intervals; finite observation does not close software gaps.',
                  artifacts=[dict(path=str(x),sha256=sha(x)) for x in inputs])
    dest=OUT/'ram_gate_status.json'
    dest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(path=str(dest),sha256=sha(dest),exclusive_ram_ownership=report['exclusive_ram_ownership'],
                         identified_paths=report['identified_software_paths'])))


if __name__=='__main__':
    main()
