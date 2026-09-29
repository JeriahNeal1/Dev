"""A2WC511R-only read-only checksum audit derived from installed RomRaider.

No input file is written.  correction() returns a bytes value for separately
reviewed callers; it does not add RomRaider edit stamps or disable checksums.
"""
import hashlib, json, pathlib, struct

SIZE=0x100000
TABLE=0xFFB80
TABLE_BYTES=168
CHECK_TOTAL=0x5AA5A55A
BASELINE_SHA='22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218'
BASELINE=pathlib.Path(r'C:\Dev\SubaruRoms\OEM\A2WC511R.bin')

def digest(data):return hashlib.sha256(data).hexdigest()
def records(data):
    if len(data)!=SIZE or data[0x2000:0x2008]!=b'A2WC511R':raise ValueError('Expected exact A2WC511R 1MiB layout')
    rows=[]
    for pos in range(TABLE,TABLE+TABLE_BYTES,12):
        start,end,stored=struct.unpack_from('>III',data,pos)
        if start%4 or start>end or end>SIZE:raise ValueError('Malformed checksum region')
        effective_end=start+((end-start+3)//4)*4
        if effective_end>SIZE:raise ValueError('Checksum final word exceeds image')
        disabled=start==end==0
        if not disabled and start<=pos+8<end:raise ValueError('Self-overlapping checksum region')
        summed=sum(struct.unpack_from('>I',data,i)[0] for i in range(start,end,4))&0xffffffff
        expected=(CHECK_TOTAL-summed)&0xffffffff
        rows.append(dict(index=len(rows),descriptor_offset=pos,start=start,end_parameter=end,effective_end_exclusive=effective_end,disabled=disabled,stored=stored,expected=expected,valid=stored==expected))
    return rows

def correction(data, expected_descriptors=None):
    rows=records(data)
    if rows[0]['disabled']:raise ValueError('First checksum disabled: native validator treats all checksums disabled')
    if expected_descriptors is None:
        baseline=BASELINE.read_bytes()
        if digest(baseline)!=BASELINE_SHA:raise ValueError('Immutable baseline mismatch')
        expected_descriptors=[(r['start'],r['end_parameter']) for r in records(baseline)]
    if [(r['start'],r['end_parameter']) for r in rows]!=expected_descriptors:raise ValueError('Checksum descriptor geometry differs from immutable baseline')
    out=bytearray(data)
    for r in rows:struct.pack_into('>I',out,r['descriptor_offset']+8,r['expected'])
    if not all(r['valid'] for r in records(out)):raise ValueError('Checksum correction did not validate')
    return bytes(out)

def main():
    out=pathlib.Path(__file__).parent
    baseline=BASELINE.read_bytes();assert digest(baseline)==BASELINE_SHA
    native=json.loads((out/'native_checksum_mutation.json').read_text())
    mutation=bytearray(baseline);mutation[0x2100]^=1
    fixed=correction(mutation)
    assert digest(fixed)==native['repaired_sha256'],'Independent implementation differs from installed native checksum routine'
    descriptors=records(baseline)
    first_disabled=bytearray(baseline);struct.pack_into('>III',first_disabled,TABLE,0,0,CHECK_TOTAL)
    rejected=False
    try:correction(first_disabled)
    except ValueError:rejected=True
    assert rejected
    inputs=[]
    for p in [BASELINE,pathlib.Path(r'C:\Dev\SubaruRoms\OEM\A2WC511R_STOCK_ROMRAIDER.bin'),*pathlib.Path(r'C:\Users\Jeriah Neal\Desktop').glob('*.bin')]:
        b=p.read_bytes();rr=records(b)
        inputs.append(dict(path=str(p),sha256=digest(b),valid=all(r['valid'] for r in rr),first_disabled=rr[0]['disabled'],invalid_indices=[r['index'] for r in rr if not r['valid']],edit_stamp=b[TABLE+204:TABLE+208].hex()))
    sources=[]
    for rel in ['maps/RomChecksum.java','maps/Rom.java','Settings.java','xml/RomAttributeParser.java']:
        p=pathlib.Path(r'C:\Program Files\RomRaider\src\main\java\com\romraider')/rel
        sources.append(dict(path=str(p),sha256=digest(p.read_bytes())))
    result=dict(baseline_sha256=digest(baseline),table_hex=hex(TABLE),table_bytes=TABLE_BYTES,constant_hex=hex(CHECK_TOTAL),descriptors=descriptors,inputs=inputs,native_match_sha256=digest(fixed),disabled_first_rejected=rejected,sources=sources,note='Modulo 2^32 sum of big-endian uint32 words for i=start; i<end_parameter; i+=4, plus stored correction equals 0x5AA5A55A. On A2WC511R end_parameter=0xFFAF7, final word starts FFAF4 and covers through FFAF7: effective byte span [0x2000,0xFFAF8). Verified against installed native JAR. Native edit stamp +204 is separate. SharpTune subarudbw name alone implements no arithmetic; proprietary ECUFlash module not directly executed.')
    (out/'checksum_audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
