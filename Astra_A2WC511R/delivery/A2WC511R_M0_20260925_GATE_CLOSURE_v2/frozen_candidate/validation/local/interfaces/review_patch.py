"""Independent read-only strict patch/binary/checksum review."""
import hashlib,json,pathlib,struct,sys
from checksum_audit import records, correction, BASELINE, BASELINE_SHA
build=pathlib.Path(sys.argv[1]);folder=pathlib.Path(sys.argv[2]);out=pathlib.Path(__file__).parent
manifest=json.loads((build/'manifest.json').read_text());review=json.loads((folder/'roundtrip_review.json').read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
baseline=BASELINE.read_bytes();assert sha(baseline)==BASELINE_SHA
elf=next(build.glob('*.elf')).read_bytes();header=struct.unpack_from('>16sHHIIIIIHHHHHH',elf)
sections=[struct.unpack_from('>IIIIIIIIII',elf,header[6]+i*header[11]) for i in range(header[12])]
allocated=[s for s in sections if s[2]&2];assert len(allocated)==1
s=allocated[0];code=elf[s[4]:s[4]+s[5]];start=s[3];end=start+len(code);entry=header[4]
assert start==0xe1000 and sha(code)==manifest['artifacts']['m0.EXPERIMENTAL_UNAPPROVED.code.bin']
raw=(folder/'A2WC511R.M0.EXPERIMENTAL_UNAPPROVED.raw.bin').read_bytes()
expected=bytearray(baseline);expected[start:end]=code;struct.pack_into('>I',expected,0x11adc,entry)
assert raw==expected
fixed=(folder/'A2WC511R.M0.EXPERIMENTAL_UNAPPROVED.checksum_corrected.bin').read_bytes();assert fixed==correction(raw)
assert all(r['valid'] for r in records(fixed)) and not all(r['valid'] for r in records(raw))
assert (folder/'A2WC511R.M0.EXPERIMENTAL.reverted.bin').read_bytes()==baseline
assert (folder/'A2WC511R.M0.EXPERIMENTAL.corrected_roundtrip_baseline.bin').read_bytes()==baseline
assert correction((folder/'A2WC511R.M0.EXPERIMENTAL.corrected_then_removed.bin').read_bytes())==baseline
assert fixed[0xffc4c:0xffc50]==baseline[0xffc4c:0xffc50]
records_seen=[];memory={}
for line in next(folder.glob('*.patch')).read_text().splitlines():
    assert line.startswith('S3');rec=bytes.fromhex(line[2:]);assert rec[0]==len(rec)-1 and sum(rec)&255==255
    address=int.from_bytes(rec[1:5],'big');data=rec[5:-1]
    kind='code' if start<=address and address+len(data)<=end else 'baseline' if 0xff000000+start<=address and address+len(data)<=0xff000000+end else 'metadata' if 0x80001000<=address<0x80010000 else 'unexpected'
    assert kind!='unexpected'
    for i,b in enumerate(data):assert address+i not in memory;memory[address+i]=b
    records_seen.append(dict(address=hex(address),bytes=len(data),kind=kind))
assert bytes(memory[a] for a in range(start,end))==code
assert bytes(memory[a+0xff000000] for a in range(start,end))==baseline[start:end]
assert all(sha((folder/n).read_bytes())==h for n,h in review['output_hashes'].items())
assert sha((build/'manifest.json').read_bytes())==review['build_manifest_sha256']
result=dict(status='PASS',build=str(build),patch_folder=str(folder),raw_sha256=sha(raw),corrected_sha256=sha(fixed),elf_sha256=sha(elf),actual_entry=hex(entry),code_span=[hex(start),hex(end)],raw_changed_bytes=sum(a!=b for a,b in zip(baseline,raw)),corrected_extra_changed_addresses=[hex(i) for i,(a,b) in enumerate(zip(raw,fixed)) if a!=b],srecords=records_seen,checks=['Raw candidate equals ELF-only section plus verified hook pointer','All patch S3 counts/checksums/address ranges valid and disjoint','Strict original bytes embedded at SharpTune baseline offset','No metadata/simulator bytes flattened into 1MiB image','Raw removal exact baseline','Checksum derivative exactly independent native-matched arithmetic','Corrected removal + checksum normalization exact baseline','Edit stamp unchanged','Manifest and output hashes all match'],limit='Serialization and integrity only. ROM/RAM ownership and task timing remain unapproved.')
(out/('patch_review_'+folder.name+'.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='srecords'},indent=2))
