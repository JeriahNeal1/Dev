"""Classify emitted NOP padding outside the RK02 executable interval."""
import sys
sys.dont_write_bytecode=True
import hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PIN='3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581'
def pin(p):
    b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def main():
    build=ROOT/'build/rk02_01';m=json.loads((build/'manifest.json').read_text());b=(build/'kernel.bin').read_bytes()
    assert hashlib.sha256(b).hexdigest()==PIN
    base=m['load_address'];s=m['symbols'];code=set(m['instruction_addresses'])
    assert m['entry']==base+4==0xffff3004 and len(code)==335
    assert code==set(range(0xffff3004,0xffff32a2,2))
    padding={0xffff3000,0xffff3002,0xffff32a2}
    assert all(b[p-base:p-base+2]==b'\x00\x09' for p in padding)
    assert not code&padding
    edges=[];calls=[];rts=[];pr_restores=[]
    for i in m['instructions']:
        a=i['address'];op=struct.unpack_from('>H',b,a-base)[0];assert op==i['opcode']
        if op>>12 in (0xa,0xb):
            d=op&0xfff;d=d-4096 if d&2048 else d;t=(a+4+2*d)&0xffffffff
            assert t in code and a+2 in code;edges.append([a,t])
            if op>>12==0xb:assert a+4 in code;calls.append({'pc':f'{a:08X}','target':f'{t:08X}','return':f'{a+4:08X}'})
        if op&0xff00 in (0x8900,0x8b00):
            d=op&255;d=d-256 if d&128 else d
            assert a+2 in code and a+4+2*d in code;edges.extend(([a,a+2],[a,a+4+2*d]))
        assert op&0xf0ff not in (0x400b,0x402b,0x0003,0x0023) # no computed call/jump
        assert op!=0x002b and op&0xff00!=0xc300 # no RTE or TRAPA
        if op==0x000b:rts.append(a)
        if op&0xf0ff==0x402a:pr_restores.append(a)
    assert pr_restores==[0xffff327a] and struct.unpack_from('>H',b,0x27a)[0]==0x4e2a
    assert rts==[0xffff31b8,0xffff31d4,0xffff31f8,0xffff327c,0xffff3292]
    assert b[0x29e:0x2a2]==bytes.fromhex('affe0009') # final BRA self and its delay slot
    vectors=b[s['vector_table']-base:s['upload_checksum_word']-base]
    assert vectors==struct.pack('>I',0xffff3296)*256
    static=ROOT/'evidence/contracts/BINARY_REVIEW_rk02_01.json';review=json.loads(static.read_text())
    assert review['kernel_sha256']==PIN and review['computed_executable_calls']==0
    assert review['all_GPR_definition_sites']['14']==['FFFF31FC']
    upload=ROOT/'evidence/contracts/UPLOAD_WIRE_CONTRACT_RK02.json';wire=json.loads(upload.read_text())
    assert wire['actual_upload_sha256']==PIN
    result={'schema':1,'status':'PASS_UNREACHABLE_EMITTED_PADDING','kernel_sha256':PIN,
      'inputs':[pin(build/'manifest.json'),pin(build/'kernel.bin'),pin(static),pin(upload),pin(Path(__file__))],
      'executable_instruction_count':335,'executable_interval':['FFFF3004','FFFF32A2'],
      'padding':[{'address':f'{a:08X}','bytes':'0009','decodes_as':'NOP','classification':'NON_EXECUTED_UPLOAD_HEADER' if a<0xffff3004 else 'NON_EXECUTED_CODE_ALIGNMENT'} for a in sorted(padding)],
      'entry_proof':'The fixed OEM start path jumps to FFFF3004. The header at3000/3002 participates in upload/checksum as data and is never the entry.',
      'alignment_proof':'The last executable pair is BRA FFFF329E at329E with NOP delay slot32A0. Its successor is329E, so it cannot fall through to32A2.',
      'direct_control_proof':'All decoded direct branch targets, conditional fallthroughs, BSR targets and BSR return PCs lie in the335-word executable interval and exclude all three padding words.',
      'direct_edge_count':len(edges),'calls_and_return_addresses':calls,
      'return_proof':'All five RTS sites are called helpers. Leaves preservePR; tx_frame receives a BSR-setPR, saves it inR14 at31FC, and restores onlythatR14 at327A. The completeR14 definition set contains only31FC. Main and exception paths do notRTS. This is the bounded fixed-object call contract from the independent binary review.',
      'exception_proof':'All256 private vectors contain FFFF3296, which ends in the329E self-loop. NoRTE and no computed jump/call are present. Pre-private-VBR/asynchronous corruption remain outside the admitted contract.',
      'padding_words_not_in_coverage_denominator':3,'physical_operations':0,
      'limits':['These are intentionally nonexecuted emitted words, not extra uncovered executable instructions.',
        'Arbitrary corrupted code/PR, unexpected initial entry or uncontrolled asynchronous execution are not claimed safe.',
        'Other literal, identity, vector and checksum bytes may decode as instructions under a raw disassembler; their data classification is separately pinned by artifact_review and the executable interval.']}
    out=ROOT/'evidence/contracts/UNREACHABLE_PADDING_RK02.json'
    with out.open('x',encoding='utf-8') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'report':str(out),'sha256':pin(out)['sha256']}))
if __name__=='__main__':main()
