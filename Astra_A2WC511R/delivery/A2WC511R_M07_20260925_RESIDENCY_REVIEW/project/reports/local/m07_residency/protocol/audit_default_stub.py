"""Raw encoded-reference audit of the live 12-byte default branch replacement."""
from pathlib import Path
from hashlib import sha256
import json
ROOT=Path('C:/Dev/Astra_A2WC511R')
rom=Path('C:/Dev/SubaruRoms/OEM/A2WC511R.bin').read_bytes()
assert sha256(rom).hexdigest()=='22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218'
lo,hi=0x484B0,0x484BC
assert rom[lo:hi].hex()=='84e1cb0180e160e0c97f2e00'
branches=[]; reads=[]; returns=[]; aligned_pointers=[]
for a in range(0,len(rom)-1,2):
    w=int.from_bytes(rom[a:a+2],'big');target=None;kind=None
    if w>>12 in (10,11):
        d=w&4095;d=d-4096 if d&2048 else d
        target=a+4+2*d;kind='BRA' if w>>12==10 else 'BSR'
    elif w&0xFF00 in (0x8900,0x8B00,0x8D00,0x8F00):
        d=w&255;d=d-256 if d&128 else d
        target=a+4+2*d;kind='conditional'
    if target is not None and lo<=target<hi and not lo<=a<hi:
        branches.append({'from':a,'target':target,'kind':kind,'encoded_word':w})
    address=None;width=0
    if w>>12==9:address=a+4+2*(w&255);width=2
    elif w>>12==13:address=((a+4)&~3)+4*(w&255);width=4
    elif w&0xFF00==0xC700:address=((a+4)&~3)+4*(w&255);width=1
    if address is not None and address<hi and address+width>lo and not lo<=a<hi:
        reads.append({'from':a,'address':address,'width':width,'encoded_word':w})
    if (w>>12==11 or w&0xF0FF in (0x0003,0x400B)) and lo<=a+4<hi and not lo<=a<hi:
        returns.append({'from':a,'return_address':a+4})
for a in range(0,len(rom)-3,4):
    target=int.from_bytes(rom[a:a+4],'big')
    if lo<=target<hi:aligned_pointers.append({'source':a,'target':target})
assert branches==[{'from':0x48314,'target':lo,'kind':'BRA','encoded_word':0xA0CC}],branches
assert not reads and not returns and not aligned_pointers
result={'status':'PASS_ENCODED_REFERENCE_SCOPE_ONLY','changed_span':[lo,hi],
    'branches':branches,'external_PC_relative_read_encodings':reads,
    'external_manufactured_return_PC':returns,'aligned_pointer_literals':aligned_pointers,
    'fallthrough':'Original preceding address484AE is a decoded literal inside the dispatcher pool, not an entry contract; calculated entry is unclosed.',
    'complete_ownership_status':'FAIL','remaining':'Caller-directed or otherwise unresolved computed entries/internal data consumers are not excluded by this scan.',
    'intentional_behavior':'Exact project requests extend live default behavior. All other default requests execute the original flag/reject operations then rejoin484BC.',
    'stock_sha256':sha256(rom).hexdigest()}
(Path(__file__).parent/'DEFAULT_STUB_REFERENCES.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'incoming_branches':len(branches),'complete_ownership_status':result['complete_ownership_status']}))
