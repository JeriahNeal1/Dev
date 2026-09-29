"""Read-only PE/string/resource inventory; never load the executable or provider."""
import json
import re
import sys
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, r'C:\Dev\Astra_A2WC511R\work\tools\m07_binary_audit')
import pefile

EXE = Path(r'C:\Program Files (x86)\OpenECU\EcuFlash\ecuflash.exe')
data = EXE.read_bytes()
pe = pefile.PE(data=data, fast_load=False)
strings = []
for codec, regex in [('ascii', rb'[\x20-\x7e]{5,}'), ('utf-16le', rb'(?:[\x20-\x7e]\0){5,}'), ('utf-16be', rb'(?:\0[\x20-\x7e]){5,}')]:
    for m in re.finditer(regex, data):
        s = m.group().decode(codec)
        if re.search(r'kernel|sti05|7058|ssm2|upload|read memory|read.*block|flash.*init|readrom|read_rom|memmodel|unlock|seed|key|download|reset ecu|enableflash|disableflash', s, re.I):
            try:
                va = pe.OPTIONAL_HEADER.ImageBase + pe.get_rva_from_offset(m.start())
            except pefile.PEFormatError:
                va = None
            strings.append(dict(offset=m.start(), va=va, codec=codec, text=s))
resources = []
def walk(directory, path=()):
    for entry in directory.entries:
        key = str(entry.name) if entry.name else entry.id
        if hasattr(entry, 'directory'):
            walk(entry.directory, path+(key,))
        else:
            r = entry.data.struct
            payload = pe.get_data(r.OffsetToData, r.Size)
            resources.append(dict(path=path+(key,), rva=r.OffsetToData, size=r.Size, sha256=sha256(payload).hexdigest()))
if hasattr(pe, 'DIRECTORY_ENTRY_RESOURCE'):
    walk(pe.DIRECTORY_ENTRY_RESOURCE)
out = dict(executable=str(EXE), sha256=sha256(data).hexdigest(), size=len(data),
           machine=pe.FILE_HEADER.Machine, image_base=pe.OPTIONAL_HEADER.ImageBase,
           sections=[dict(name=s.Name.decode().rstrip('\0'), rva=s.VirtualAddress,
                         raw_offset=s.PointerToRawData, raw_size=s.SizeOfRawData,
                         virtual_size=s.Misc_VirtualSize) for s in pe.sections],
           strings=strings, resources=resources,
           imports=[dict(dll=d.dll.decode(), names=[i.name.decode() if i.name else i.ordinal for i in d.imports]) for d in pe.DIRECTORY_ENTRY_IMPORT])
(HERE/'inventory.json').write_text(json.dumps(out, indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('strings','imports','resources')},indent=2))
print(json.dumps(dict(strings=len(strings), resources=resources),indent=2))
for s in strings:
    if re.search(r'sti05|7058|kernel',s['text'],re.I):
        print(f"{s['offset']:08X} {s['va']:08X} {s['codec']} {s['text'][:180]}")
