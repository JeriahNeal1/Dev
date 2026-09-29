"""Independent bounded ELF envelope/closure audit; read-only."""
import hashlib,json,pathlib,struct,sys
build=pathlib.Path(sys.argv[1]);manifest=json.loads((build/'manifest.json').read_text())
elf=next(build.glob('*.elf'));blob=elf.read_bytes();header=struct.unpack_from('>16sHHIIIIIHHHHHH',blob)
assert header[0][:6]==b'\x7fELF\x01\x02' and header[2]==42
assert header[7]&15==11
sections=[]
for i in range(header[12]):sections.append(struct.unpack_from('>IIIIIIIIII',blob,header[6]+i*header[11]))
names=sections[header[13]];ns=blob[names[4]:names[4]+names[5]]
def name(table,pos):return table[pos:table.find(b'\0',pos)].decode()
alloc=[];symbols=[]
for s in sections:
    if s[2]&2:alloc.append(dict(name=name(ns,s[0]),address=s[3],size=s[5],flags=s[2]))
    if s[1]==2:
        st=sections[s[6]];strings=blob[st[4]:st[4]+st[5]]
        for pos in range(s[4],s[4]+s[5],s[9]):
            n,v,size,info,other,ndx=struct.unpack_from('>IIIBBH',blob,pos)
            if n:symbols.append(dict(name=name(strings,n),value=v,size=size,kind=info&15,section=ndx))
undefined=[s for s in symbols if s['section']==0]
payload=next(build.glob('*.code.bin')).read_bytes();m0=[s for s in sections if name(ns,s[0])=='.m0'][0]
assert len(alloc)==1 and alloc[0]['name']=='.m0'
assert payload==blob[m0[4]:m0[4]+m0[5]] and not undefined
artifact_matches={p:hashlib.sha256((build/p).read_bytes()).hexdigest()==h for p,h in manifest['artifacts'].items()}
assert all(artifact_matches.values())
output=dict(build=str(build),elf=str(elf),elf_sha256=hashlib.sha256(blob).hexdigest(),elf32_big_endian=True,machine='EM_SH',sh_flags=header[7],entry=header[4],alloc_sections=alloc,symbols=symbols,undefined_symbols=undefined,payload_exact_m0=True,all_manifest_artifacts_match=True,limit='Section/symbol envelope and bytes only; does not prove address ownership or interrupt/timing safety')
(pathlib.Path(__file__).parent/('elf_review_'+build.name+'.json')).write_text(json.dumps(output,indent=2),encoding='utf-8')
print(json.dumps(output,indent=2))
