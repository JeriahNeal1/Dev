"""Read-only final input/inventory review; never invokes collector or provider."""
from pathlib import Path
import hashlib
import json
import stat

ROOT=Path(r'C:\Dev\Astra_A2WC511R')
OUT=Path(__file__).resolve().parent
VIRTUAL=ROOT/'integrations/romraider/virtual'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    mp=VIRTUAL/'collector_runtime_manifest.json'
    manifest=json.loads(mp.read_text())
    hashes=[]
    for row in manifest['artifacts']:
        path=Path(row['path'])
        actual=sha(path)
        assert actual==row['sha256'],str(path)
        hashes.append(dict(path=str(path),sha256=actual))
    directories=[]
    for row in manifest['runtime_directories']:
        p=Path(row['path'])
        entries=[p,*p.rglob('*')]
        assert not any(getattr(x.lstat(),'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT for x in entries)
        actual=sorted(str(x).lower() for x in entries[1:] if x.is_file())
        assert actual==sorted(str(x).lower() for x in row['files']),str(p)
        directories.append(dict(path=str(p),files=len(actual),reparse_points=0))
    assert all('*' not in x and '?' not in x for x in manifest['classpath'])
    source=VIRTUAL/'src/a2wc/virtualrr/ReadOnlySSMCollector.java'
    launcher=VIRTUAL/'Invoke-ReadOnlySSM.ps1'
    s=source.read_text();p=launcher.read_text()
    assert 'ReparsePoint' in p and '-Force' in p and '$manifest.classpath' in p
    assert 'Arrays.copyOfRange(rom,0x2000,0x2008),pilot' in s
    assert 'initialize(gate,initQ,10000)' in s and 'setDaemon(true)' in s
    assert 'if(manager!=null)manager.close()' in s and 'cleanup_failure' in s
    assert s.index('try{\n  if(virtual)')<s.index('J2534TransportFactory.getManager')
    native=OUT/'independent_j2534_iso9141_bytecode.txt'
    text=native.read_text(encoding='utf-8-sig')
    ctor=text.split('  private void initJ2534(',1)[1].split('  private void version(',1)[0]
    assert 'J2534.open:' in ctor and 'J2534.connect:' in ctor and 'J2534.startPassMsgFilter:' in ctor
    assert not any(x in ctor for x in ['writeMsg:','fiveBaudInit:','fastInit:','clearLine:','setProgrammingVoltage:'])
    log=OUT/'independent_collector_gate_test.log'
    assert 'PASS 285 independent gate checks' in log.read_text(encoding='utf-8-sig')
    evidence=[source,launcher,mp,native,OUT/'independent_serial_manager_bytecode.txt',
              OUT/'IndependentCollectorGateCheck.java',log,
              ROOT/'work/gate_closure/virtual_rr/classes/a2wc/virtualrr/ReadOnlySSMCollector$ReadOnlyGate.class']
    result=dict(status='PASS_SCOPED_OFFLINE_REVIEW_PHYSICAL_USE_UNVALIDATED',
                provider_loaded=False,physical_device_calls=False,collector_main_invoked_by_this_review=False,
                reviewed_artifact_hashes=len(hashes),exact_runtime_directories=directories,
                policy_checks=285,manifest_sha256=sha(mp),
                issues_resolved=['unlisted class/resource input accepted','constructor/cleanup evidence loss',
                                 'full image CALID not compared with pilot','unbounded BF initialization quiet wait'],
                review_files=[dict(path=str(x),sha256=sha(x)) for x in evidence],
                limitations=['Native DLL and actual device behavior untested.',
                             'OEM A0 support, valid RAM addressing and physical response timing are still unproven.',
                             'Native provider cleanup hang/forced process termination are not a graceful-abort guarantee.',
                             'Read acquisition success is not firmware checksum/flash/release acceptance.'])
    dest=OUT/'independent_collector_review.json'
    dest.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],manifest_sha256=sha(mp),artifacts=len(hashes),
                         result_path=str(dest),result_sha256=sha(dest))))


if __name__=='__main__':
    main()
