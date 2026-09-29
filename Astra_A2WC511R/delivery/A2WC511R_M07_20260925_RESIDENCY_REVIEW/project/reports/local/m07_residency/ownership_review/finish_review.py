"""Independent ownership synthesis. PASS subclaims never promote unresolved closure."""
import json
from hashlib import sha256
from pathlib import Path

HERE=Path(__file__).parent
ROOT=HERE.parents[3]
rom=Path(r'C:\Dev\SubaruRoms\OEM\A2WC511R.bin').read_bytes()
expected='22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218'
assert sha256(rom).hexdigest()==expected
inventory=json.loads((HERE/'inbound_inventory.json').read_text())
uses=json.loads((HERE/'classified_uses.json').read_text())
tests=json.loads((HERE/'verification.json').read_text())
semantic=HERE.parent/'semantic'
proof=json.loads((semantic/'semantic_structural_proof.json').read_text())
assert proof['status']=='PASS' and tests['status']=='PASS'

# Target-specific RTOS exclusion: do not require valid task-state assumptions merely
# to prove that this bounded table lookup cannot select either modified object.
rtos_expected={0x395A:'62e0',0x3972:'d308',0x3974:'61d0',0x3976:'323c',0x397A:'611c',0x397C:'3218',0x397E:'6022',0x3980:'402b'}
for a,h in rtos_expected.items():assert rom[a:a+2].hex()==h
assert rom[0x3994:0x3998].hex()=='00004a7c'
targets={};unaligned=0
for state_byte in range(256):
    signed=state_byte-256 if state_byte&128 else state_byte
    for index_byte in range(256):
        address=0x4A7C+signed-index_byte
        if address&3:
            unaligned+=1
            continue
        target=int.from_bytes(rom[address:address+4],'big')
        assert not 0x4260<=target<0x430A and not 0x1466E<=target<0x147AC
        targets[address]=target
mutated=dict(targets);mutated[0x4A7C]=0x42A4
assert any(0x4260<=t<0x430A for t in mutated.values())
rtos=dict(status='PASS_TARGET_SPECIFIC_EXCLUSION',site='00003980',
    source_formula='target = BE32(ROM[0x4A7C + sign8(byte@R14) - zero8(byte@R13)])',
    contract='Actual395A/3972..3980 path, immutable ROM, normal aligned SH longword loads; no arbitrary interior entry.',
    input_pairs=65536,aligned_addresses=len(targets),unaligned_pairs=unaligned,
    read_address_span=['000048FD','00004AFF'],read_address_span_note='All computed starts48FD..4AFB; last aligned read4AF8..4AFB.',
    actual_aligned_read_span=['00004900','00004AFC'],
    target_words={f'{a:08X}':f'{t:08X}' for a,t in sorted(targets.items())},
    negative_control='Replacing table word4A7C with42A4 is detected.',
    exclusions='Does not establish valid task indices or general table validity. Misaligned loads take architectural exception, whose context remains separate.')
(HERE/'rtos_target_exclusion.json').write_text(json.dumps(rtos,indent=2)+'\n')

common_pass={
    'external_encoded_direct_branch':'PASS: all524287 aligned ROM words scanned; none target the full original object from outside.',
    'external_PC_relative_read_of_changed_bytes':'PASS: all raw MOV.W/MOV.L/MOVA forms scanned; none overlap changed span from outside.',
    'literal_function_entry_classification':'PASS: every aligned raw pointer into the full original object points at its ordinary entry; actual literal-load/JSR/delay-slot sequences verified.',
    'external_call_manufactured_interior_return':'PASS: no BSR/BSRF/JSR outside the object has architectural returnPC inside it.',
    'original_internal_calls':'PASS: original executed division and range paths contain no calls, so no original nested callee retains a legitimate returnPC into reclaimed instructions.',
    'transparent_ROM_readback':'PASS_AS_ALLOWED_BEHAVIOR: native A0/A8 may expose changed bytes. No virtualization or claim of original byte identity.',
    'semantic_replacement':'PASS_CONDITIONAL: reviewed structural induction / complete nibble partition argument, not finite sample extrapolation.'}
gaps=[
 dict(id='computed_control_source_contracts',status='FAIL',ranges=['[00004260,0000430A)','[0001466E,000147AC)'],
      sources=[dict(pc='00000042',instruction='JMP @R4',source='Entry0040 changesSP then jumps to suppliedR4; complete caller-supplied R4 domain is not established.'),
               dict(pc='0000DE3E',instruction='JSR @R1',source='DE3C loadsR1 from descriptor+4. Descriptor=BE32(ROM[1023C+4*u8(entryR4)])+8*u16(entryR5), afterDDF4 setup; executable descriptor case requires leadingu16==FFFF. Complete caller index domains and descriptor provenance are not proved.')],
      requirement='Establish target-sensitive contracts for these and all remaining calculated control sources. No actual witness into either candidate is claimed. The broad analyzer has TOP frontiers and unfinished worklist, so it cannot supply this closure.'),
 dict(id='internal_code_as_data_consumers',status='FAIL',ranges=['[00004260,0000430A)','[0001473C,000147AC)'],
      requirement='Exclude or preserve firmware-internal byte/word reconstruction, computed code-table reads, and DMA that consume changed instruction bytes as data with behavior beyond transparent diagnostic readback. PC-relative reads and aligned absolute literals are closed; computed dataflow is not.'),
 dict(id='interrupt_context_and_stack',status='FAIL',ranges=['division initialSP-12..initialSP-8','IRQ/exception savedPC and register frames'],
      requirement='Replacement must start after reset/quiescent programming, never resume a pre-patch execution frame. Prove ISR context transparency and exclusive additional division stack word inclnested interrupts/DMA; added131instructions need caller-specific deadline margin. Existing noninterleaved semantic theorem excludes these contexts.')]
objects={}
for name,o in inventory['objects'].items():
    objects[name]=dict(entry=o['entry'],changed_span=o['changed_span'],proposed_tail=o['tail'],
        proposed_bytes=102 if name=='division' else 60,provably_owned_bytes=0,
        bounded_subclaims=common_pass.copy(),complete_inbound_ownership='FAIL',remaining_obligations=[x['id'] for x in gaps])
objects['division']['ordinary_calls']=[x for x in uses['calls'] if x['target']=='00004260']
objects['division']['old_literal_pool']='430A NOP and430C..4314 literals remain outside changedspan. No original linker/object identity established.'
objects['division']['semantic_conditions']=['R0divisor,R1dividend; arithmeticpair induction32 iterations; DT altersT then SHAR restorescapturedT; otherSRbits unchanged.',
    'ExtraR4store/load at[initialSP-12,initialSP-8) onnonzerodivisor only. Contents of this word are not restored to pre-call contents; ownership/private assumption is necessary.',
    'Divisorzero retains originalR2save,errorwrite44E toFFFF130C,R0zero and registersideeffects.']
objects['range_tail']['ordinary_calls']=[x for x in uses['calls'] if x['target']=='0001466E']
objects['range_tail']['semantic_conditions']=['Entry1466E dominates withR6=64; original1473A setsR0=15 beforemask.',
    'All16low-nibble classes preserveR4output,R0nibble,R3destination,R7=128,R6=64,allotherregisters andT=(n<=8 or n==15).',
    'Sharedliteralpool146B4..14730 is read by preceding functions; it is not exclusive to this function and remains unchanged.',
    'Arbitrary interior entry bypassingR6setup has a known negative equivalence counterexample.']
report=dict(classification='INDEPENDENT_BOUNDED_OBJECT_REVIEW_NOT_ACCEPTED_RESIDENCY',rom_sha256=expected,
    objects=objects,proposed_bytes_total=162,provably_owned_bytes_total=0,remaining_obligations=gaps,
    raw_pointer_classification=uses['counts'],raw_pointer_interpretation='No unaligned hit is an alignedSHlongword function pointer.13literalfloatcrossings and80typedfloatcrossings have positive data-use evidence.846othercrossings andoneodddatawordcrossing have no complete consumer contract; they are not falsely reported as reachable code entries.',
    rtos_target_exclusion=rtos['status'],
    local_library_provenance='477storedarchives searched: nofullroutine or12-byteheader match;12libgccarchives contain genericunrolledROTCL/DIV1pairs only. RenesasPAKcompressedruntimeobjects notdecompressed/identified. Nooriginalsymbol/linkermetadata proof.',
    review_of_SEMANTIC_REPLACEMENTS='PASS_WITH_EXPLICIT_SCOPE: induction and range partition are sound under their entry/private-stack/noninterleaving domains. GenericROMreads should be reported as transparentmodified-image behavior, not an automaticownershipfailure.',
    verification=dict(checks=len(tests['checks']),status=tests['status'],additional_rtos_pairs=65536),
    evidence={str(p):sha256(p.read_bytes()).hexdigest() for p in [HERE/'inbound_inventory.json',HERE/'classified_uses.json',HERE/'verification.json',HERE/'rtos_target_exclusion.json',HERE/'local_library_search.json',semantic/'candidate_manifest.json',semantic/'semantic_structural_proof.json',semantic/'SEMANTIC_REPLACEMENTS.md']})
(HERE/'ownership_peer_review.json').write_text(json.dumps(report,indent=2)+'\n')
print('ownership peerreview: conditional162 bytes; provedowned0;31encodingchecks +65536RTOSpairsPASS')
