"""Generate and verify a STRICT, unapproved M0 experimental offline patch.

This program only edits fresh disposable copies. It emits no release approval.
All actual application/removal uses the source-built SharpTune implementation.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, os, shutil, struct, subprocess, xml.etree.ElementTree as ET
from build import parse_elf
ROOT=Path(__file__).resolve().parent
BASE=Path(r'C:\Dev\Astra_A2WC511R')
BASELINE=Path(r'C:\Dev\SubaruRoms\OEM\A2WC511R.bin')
BASESHA='22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218'
IDENT='A2WC511R.M0.EXPERIMENTAL.v1'
EXE=BASE/'work/tooling/sharptune_offline_ecabea8/SharpTune.exe'
def sha(data):return hashlib.sha256(data).hexdigest()
def u32(*args):return struct.pack('>'+'I'*len(args),*args)
def string(s):
    b=s.encode('ascii')+b'\0';return b+b'\0'*((-len(b))%4)
def srecords(address,data):
    lines=[]
    for off in range(0,len(data),32):
        chunk=data[off:off+32];raw=bytes([len(chunk)+5])+u32(address+off)+chunk
        lines.append('S3'+raw.hex().upper()+('%02X'%((~sum(raw))&255)))
    return lines
def diffranges(a,b):
    spans=[];start=None
    for i,(x,y) in enumerate(zip(a,b)):
        if x!=y and start is None:start=i
        if x==y and start is not None:spans.append((start,i));start=None
    if start is not None:spans.append((start,len(a)))
    return spans
def logger_fragment(out):
    fields=[('sequence',0,4,'Software publication sequence, even when complete; NOT a TCU heartbeat. Wraps modulo 2^32.'),
      ('magic',4,4,'M0D1 observer cookie. Does not establish power-cycle identity.'),('samples',8,4,'Observer-call count modulo 2^32, NOT a CAN receive count.'),
      ('reasons',12,4,'Diagnostic rejection bits; freshness and coherence remain unproven.'),('transitions',16,4,'Observed packed-snapshot changes, modulo 2^32. No physical gear-engagement claim.'),
      ('source',20,1,'Raw FFFF4C75 sampled byte.'),('snapshot',21,1,'Raw FFFF4C8D sampled byte.'),('latch',22,1,'Raw FFFF4CA1; not a freshness guarantee.'),('flags',23,1,'Raw FFFF4C50; bit02 not a CAN-health guarantee.'),
      ('target_nibble',24,1,'High nibble of snapshot, requested working interpretation.'),('current_nibble',25,1,'Low nibble of snapshot, reported working interpretation.'),
      ('decoded_target',26,1,'Observer reconstruction with local hold behavior. NOT direct OEM FFFF4BC1; first invalid nibble can differ from OEM retained value.'),
      ('decoded_current',27,1,'Observer reconstruction with local hold behavior. NOT direct OEM FFFF4BC2; first invalid nibble can differ from OEM retained value.'),
      ('freshness',28,1,'Hardware binding always 0 UNKNOWN. Does not authorize controls.'),('previous_snapshot',29,1,'Observer previous snapshot, same as latest after publication.'),
      ('initialized',30,1,'Observer initialized cookie flag; lazy init does not prove warm-reset detection.'),('capture_changed',31,1,'Raw values differed between two reads. Zero does not prove coherent sampling.')]
    root=ET.Element('ecuparams')
    root.append(ET.Comment('EXPERIMENTAL UNAPPROVED RAM allocation FFFF7400..741F. Fragment only; not installed. SSM addresses are low 24 bits.'))
    for ix,(name,off,size,desc) in enumerate(fields,9100):
        p=ET.SubElement(root,'ecuparam',id='E'+str(ix),name='M0 Experimental '+name,desc=desc+' Allocation unapproved; offline emulator review only.')
        e=ET.SubElement(p,'ecu',id='2F12515306');ET.SubElement(e,'address',length=str(size)).text='0x%06X'%((0xffff7400+off)&0xffffff)
        c=ET.SubElement(p,'conversions');ET.SubElement(c,'conversion',units='raw',expr='x',format='0')
    ET.indent(root);ET.ElementTree(root).write(out/'A2WC511R_M0.EXPERIMENTAL.logger.fragment.xml',encoding='utf-8',xml_declaration=True)
    (out/'logger_offsets.json').write_text(json.dumps([{'field':n,'offset':o,'bytes':z,'cpu_address':hex(0xffff7400+o),'description':d} for n,o,z,d in fields],indent=2)+'\n')
def main(build,out):
    build=build.resolve();out=out.resolve();out.mkdir(parents=True,exist_ok=False)
    baseline=BASELINE.read_bytes();assert sha(baseline)==BASESHA and len(baseline)==0x100000
    manifest=json.loads((build/'manifest.json').read_text());assert manifest['status']=='COMPILED_EXPERIMENTAL_UNAPPROVED'
    for filename,expected_sha in manifest['artifacts'].items():
        assert sha((build/filename).read_bytes())==expected_sha, 'Build artifact hash mismatch: '+filename
    for filename,expected_sha in manifest['sources'].items():
        assert sha((ROOT/filename).read_bytes())==expected_sha, 'Current source differs from built input: '+filename
    elf=parse_elf(build/'A2WC511R_DiagnosticM0.EXPERIMENTAL_UNAPPROVED.elf')
    payload=(build/'m0.EXPERIMENTAL_UNAPPROVED.code.bin').read_bytes()
    assert payload==elf['payload'], 'Extracted payload differs from actual ELF .m0 section'
    assert {n:hex(v) for n,v in elf['symbols'].items()}==manifest['symbols'], 'Manifest differs from ELF symbols'
    start=int(manifest['code_base'],16);end=start+len(payload);hook=0x11adc
    entry=int(manifest['symbols']['_m0_decoder_hook'],16);identaddr=int(manifest['symbols']['_m0_identifier'],16)
    assert start==elf['base']==0xe1000 and int(manifest['ram_base'],16)==elf['symbols']['_m0_state']==0xffff7400
    assert len(payload)==manifest['code_bytes'] and payload[identaddr-start:].startswith(IDENT.encode()+b'\0')
    assert baseline[start:end]==b'\xff'*len(payload) and baseline[hook:hook+4]==u32(0x147ac)
    assert baseline[0x2000:0x2008]==b'A2WC511R' and baseline[0xcdad8:0xcdadd]==bytes.fromhex('2F12515306')
    meta=u32(0x12340000,9,0x12340001,0x2000,8)+b'A2WC511R'+b'\0'*8+b'A2WC511R'+b'\0'*8
    meta+=u32(0x1234000f,identaddr)+string(IDENT)
    meta+=u32(0x1234000b,0xcdad8,10)+string('2F12515306')+u32(0x1234000c)+string('2F12515306')
    meta+=u32(0x12340008)+string('M0 source port')+u32(0x12340009)+string('M0_Offline_Debug')
    meta+=u32(0x1234000d)+string('EXPERIMENTAL diagnostic observer; allocation/stack/cadence unapproved; NEVER FLASH')
    meta+=u32(0x12340003,hook,0x147ac,entry)+string('OEM decoder observer pointer')
    meta+=u32(0x12340002,start,end-1)+string('M0 experimental strict code payload')+u32(0x00090009,0x00090009)
    patch=out/(IDENT+'.patch')
    # Strict OpPatch embeds expected original bytes; no permissive NewPatch removal.
    lines=srecords(start,payload)+srecords(0x80001000,meta)+srecords(start+0xff000000,baseline[start:end])
    patch.write_text('\n'.join(lines)+'\n',encoding='ascii')
    env=os.environ.copy();env['SHARPTUNE_OFFLINE_HOME']=str(out);env['SHARPTUNE_OFFLINE_LOCAL_APPLY']='1'
    commands=[]
    def run(args,label,expected=0):
        cmd=[str(EXE),*map(str,args)]
        p=subprocess.run(cmd,cwd=out,env=env,capture_output=True,text=True,timeout=60)
        (out/(label+'.log')).write_text('ARGV '+json.dumps(cmd)+'\nEXIT '+str(p.returncode)+'\n'+p.stdout+p.stderr)
        commands.append({'argv':cmd,'exit':p.returncode,'expected':expected,'log':label+'.log'})
        if p.returncode!=expected:raise RuntimeError(label+' exit='+str(p.returncode)+' '+p.stdout[-2000:]+p.stderr)
    candidate=out/'A2WC511R.M0.EXPERIMENTAL_UNAPPROVED.raw.bin';candidate.write_bytes(baseline)
    run(['rommod','dump','MISSING.intentional'],'negative_missing_file',1)
    run(['rommod','test',patch,candidate],'validate_before')
    run(['rommod','apply',patch,candidate],'apply')
    actual=candidate.read_bytes();expected=bytearray(baseline);expected[start:end]=payload;expected[hook:hook+4]=u32(entry)
    assert actual==expected, 'SharpTune output differs from independently built exact-byte expectation'
    run(['rommod','applied',patch,candidate],'validate_applied')
    reverted=out/'A2WC511R.M0.EXPERIMENTAL.reverted.bin';reverted.write_bytes(actual)
    run(['rommod','remove',patch,reverted],'remove')
    assert reverted.read_bytes()==baseline
    bad=out/'negative_bad_hook.bin';bad_data=bytearray(baseline);bad_data[hook]^=1;bad.write_bytes(bad_data)
    run(['rommod','apply',patch,bad],'negative_bad_hook',1);assert bad.read_bytes()==bad_data
    bad_payload=out/'negative_bad_payload.bin';bp=bytearray(actual);bp[start]^=1;bad_payload.write_bytes(bp)
    run(['rommod','remove',patch,bad_payload],'negative_bad_payload',1);assert bad_payload.read_bytes()==bp
    spec=importlib.util.spec_from_file_location('checksum_audit',BASE/'reports/local/interfaces/checksum_audit.py');checksum=importlib.util.module_from_spec(spec);spec.loader.exec_module(checksum)
    fixed=checksum.correction(actual);fixedpath=out/'A2WC511R.M0.EXPERIMENTAL_UNAPPROVED.checksum_corrected.bin';fixedpath.write_bytes(fixed)
    assert [x for x in diffranges(actual,fixed) if not (0xffb88<=x[0]<x[1]<=0xffb8c)]==[]
    assert fixed[0xffc4c:0xffc50]==baseline[0xffc4c:0xffc50]
    fixed_reverted=out/'A2WC511R.M0.EXPERIMENTAL.corrected_then_removed.bin';fixed_reverted.write_bytes(fixed)
    run(['rommod','remove',patch,fixed_reverted],'remove_corrected')
    assert checksum.correction(fixed_reverted.read_bytes())==baseline
    normalized=out/'A2WC511R.M0.EXPERIMENTAL.corrected_roundtrip_baseline.bin';normalized.write_bytes(checksum.correction(fixed_reverted.read_bytes()))
    logger_fragment(out)
    spans=[{'start':hex(a),'end_exclusive':hex(b),'bytes':b-a,'class':'hook_pointer' if a>=hook and b<=hook+4 else 'diagnostic_payload' if a>=start and b<=end else 'UNEXPECTED','before_sha256':sha(baseline[a:b]),'after_sha256':sha(actual[a:b])} for a,b in diffranges(baseline,actual)]
    assert all(s['class']!='UNEXPECTED' for s in spans)
    report={'status':'EXPERIMENTAL_UNAPPROVED_OFFLINE_ONLY','production_release_allowed':False,'flash_or_vehicle_actions':False,'input_baseline_sha256':BASESHA,
      'code_allocation_accepted':False,'ram_allocation_accepted':False,'abi_timing_accepted':False,'code_span':[hex(start),hex(end)],'ram_span':['0xffff7400','0xffff7420'],'hook':{'address':hex(hook),'before':'000147ac','after':u32(entry).hex()},
      'commands':commands,'sharpTune_sha256':sha(EXE.read_bytes()),'build_manifest_sha256':sha((build/'manifest.json').read_bytes()),'changed_ranges':spans,'changed_bytes':sum(s['bytes'] for s in spans),
      'strict_roundtrip':'PASS exact raw baseline bytes','checksum_policy':'Raw and corrected derivatives distinct. Removal from corrected derivative leaves corrected checksum; applying checksum.correction after removal restores exact baseline. No editor stamp normalized or added.',
      'raw_checksums_valid':all(r['valid'] for r in checksum.records(actual)),'corrected_checksums_valid':all(r['valid'] for r in checksum.records(fixed)),
      'output_hashes':{p.name:sha(p.read_bytes()) for p in out.iterdir() if p.suffix in ('.bin','.patch','.xml')},
      'counter_notes':'samples/transitions/sequence wrap modulo2^32. One transition check is skipped when samples is0 after wrap. Cookie-based lazy init is not power-cycle detection; a warm reset preserving valid cookie preserves counters and reconstructed holds.',
      'decoder_notes':'decoded_target/current are observer reconstructions, not OEM4BC1/4BC2 reads; initial invalid nibbles can differ from OEM held values.',
      'publication_reader_contract':'One nonreentrant writer. Read sequence-before, reject odd; read all32 state bytes; read sequence-after. Require equal even sequence values plus magic4D304431 and initialized1. Counter wrap can cause ABA. Individual logger parameters alone do not provide this aggregate check.',
      'blocking_gates':['code/RAM indirect and DMA ownership','task stack headroom and ISR nesting','hook call cadence and added latency','current installed tune identity','physical validation']}
    (out/'roundtrip_review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('status','changed_bytes','strict_roundtrip','raw_checksums_valid','corrected_checksums_valid')}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();main(a.build,a.out)
