"""Qualify the side-by-side passive receiver using offline evidence and fake I/O.

Never selects the physical backend. Original qualification inputs are read-only.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import datetime
import difflib
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT/'integrations/prehardware'
ORIGINAL = Path(r'C:\Dev\Astra_A2WC511R')
READKERNEL = Path(r'C:\Dev\A2WC511R_ReadKernel')
PROVIDER = Path(r'C:\Windows\SysWOW64\op20pt32.dll')
PROVIDER_SHA = 'f432084801762d919a3c31974616e097562424470003edc4f4fb843df34103cf'
ORIGINAL_BROKER_SHA = '75704175cf4993b7d8dba29ad66674da0c2c1ddae9b232bef9e40dc033fdfb96'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def record(path):
    return {'path': str(path.resolve()), 'sha256': sha(path), 'bytes': path.stat().st_size}


def write_json(path, data):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(data, handle, indent=2)
        handle.write('\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--som-report', type=Path, required=True)
    parser.add_argument('--output-directory', type=Path, required=True)
    args = parser.parse_args()
    output = args.output_directory.resolve()
    require(output.is_relative_to(ROOT), 'Evidence must stay in the side-by-side root')
    output.mkdir(parents=True, exist_ok=False)
    baseline_path = ROOT/'reports/local/prehardware/READ_ONLY_BACKEND_TESTS.json'
    baseline = json.loads(baseline_path.read_text())
    targeted = json.loads(args.som_report.read_text())
    for name, report in [('baseline', baseline), ('START_OF_MESSAGE', targeted)]:
        require(report.get('status') == 'PASS', name+' tests have not passed')
        require(report.get('real_provider_loaded') is False, name+' report lacks offline-only evidence')
    require(baseline.get('failures') == 0 and baseline.get('errors') == 0, 'Baseline failures exist')
    require(targeted.get('failures') == 0 and targeted.get('errors') == 0, 'Targeted failures exist')
    require(sha(SOURCE/'test_start_of_message.py') == targeted['source_sha256'], 'Targeted test changed')
    require(sha(SOURCE/'test_read_only.py') == baseline['source_sha256'], 'Baseline test changed')
    require(sha(SOURCE/'build/BUILD_MANIFEST.json') == baseline['build_manifest_sha256'], 'Tested build changed')
    require(sha(SOURCE/'build/BUILD_MANIFEST.json') == targeted['build_manifest_sha256'], 'Targeted tested build changed')
    require(targeted.get('full_capture', {}).get('status') == 'PASS_CAPTURE_ONLY', 'Missing complete fake capture')
    require(targeted['full_capture'].get('samples') == 120 and targeted['full_capture'].get('worker_exit') == 0,
            'Fake capture count or cleanup differs')
    for path, expected in baseline['host_dependency_sha256'].items():
        require(sha(path) == expected, 'Tested host dependency changed: '+path)

    original_manifest = ORIGINAL/'integrations/prehardware/build/BUILD_MANIFEST.json'
    original_build = json.loads(original_manifest.read_text())
    for path, expected in original_build['files'].items():
        require(sha(path) == expected, 'Sealed original changed: '+path)
    require(sha(ORIGINAL/'integrations/prehardware/build/broker.exe') == ORIGINAL_BROKER_SHA, 'Original executable changed')
    require(sha(PROVIDER) == PROVIDER_SHA, 'Real provider file changed')
    frozen_path = READKERNEL/'evidence/rk02/RELEASE_FREEZE.json'
    frozen = json.loads(frozen_path.read_text())
    for item in frozen['files']:
        require(sha(item['path']) == item['sha256'], 'Frozen RK02 file changed: '+item['path'])
    unchanged = ['integrations/prehardware/'+name for name in
                 ('capture.py','transport.py','j2534_abi.h','fake_j2534.def','build_broker.py','test_read_only.py')]
    unchanged += ['integrations/m07/'+name for name in ('protocol.py','backends.py','profile.json')]
    for relative in unchanged:
        require(sha(ROOT/relative) == sha(ORIGINAL/relative), 'Unexpected host/import change: '+relative)

    original_source = (ORIGINAL/'integrations/prehardware/broker.cpp').read_text()
    current_source = (SOURCE/'broker.cpp').read_text()
    prefix = '        std::vector<unsigned char> wire;'
    suffix = '        events+="]";'
    reviewed_prefix = current_source.split(prefix)[0]
    for declaration in ('// Tactrix j2534_tactrix.h RxStatus: START_OF_MESSAGE = 0x00000002.\n',
                        'constexpr U START_OF_MESSAGE_STATUS=0x00000002;\n',
                        'constexpr unsigned MAX_START_INDICATORS=4;\n'):
        require(reviewed_prefix.count(declaration) == 1, 'Reviewed RX declaration missing or repeated')
        reviewed_prefix = reviewed_prefix.replace(declaration, '', 1)
    require(original_source.split(prefix)[0] == reviewed_prefix, 'Change outside RX loop and reviewed declarations')
    require(original_source.split(suffix)[1] == current_source.split(suffix)[1], 'Change outside RX loop suffix')
    require(current_source.count('write(channel,&tx,&n,1000)') == 1, 'Transmit-call count changed')
    diff = ''.join(difflib.unified_diff(original_source.splitlines(True), current_source.splitlines(True),
                                      fromfile='sealed_original/broker.cpp', tofile='passive_som01/broker.cpp'))
    (output/'BROKER_SOURCE_DIFF.patch').write_text(diff, encoding='utf-8')

    build_manifest = SOURCE/'build/BUILD_MANIFEST.json'
    build = json.loads(build_manifest.read_text())
    for path, expected in build['files'].items():
        require(sha(path) == expected, 'Candidate build manifest mismatch: '+path)
    fresh = output/'fresh build with spaces'
    fresh.mkdir()
    build_run = subprocess.run(['cmd.exe','/d','/c',str(SOURCE/'build/build.cmd')], cwd=fresh,
                               capture_output=True, text=True, timeout=90,
                               creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    (fresh/'build.log').write_text(build_run.stdout+build_run.stderr, encoding='utf-8')
    require(build_run.returncode == 0, 'Fresh-directory compilation failed')
    reproduction = []
    for name in ('broker.exe','fake_j2534.dll'):
        reproduction.append({'name': name, 'qualified_build': sha(SOURCE/'build'/name), 'fresh_directory': sha(fresh/name)})
        require(sha(SOURCE/'build'/name) == sha(fresh/name), 'Fresh-directory binary differs: '+name)
    environment = dict(os.environ)
    environment.pop('A2WC_FAKE_FAULT', None)
    fake = subprocess.run([str(fresh/'broker.exe'),'--fake'], input=b'IDENTITY\nSNAPSHOT\nCLOSE\n',
                          capture_output=True, timeout=6, env=environment,
                          creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    (fresh/'fake.stdout.jsonl').write_bytes(fake.stdout)
    (fresh/'fake.stderr.log').write_bytes(fake.stderr)
    require(fake.returncode == 0, 'Reproduced broker fake exchange failed')
    require(b'FORBIDDEN_' not in fake.stderr, 'Forbidden fake export reached')
    frames = [line.removeprefix(b'FAKE WIRE ').decode() for line in fake.stderr.splitlines() if line.startswith(b'FAKE WIRE ')]
    require(frames == ['8010f001bf40','8010f014a800ff4c75ff4c8dff4ca1ff4c50ff4bc1ff4bc272'], 'Fixed transmitted frames changed')
    rows = [json.loads(line) for line in fake.stdout.splitlines()]
    require(rows[-1] == {'type':'closed'}, 'Fake cleanup not confirmed')

    inputs = [ROOT/'qualify_offline.py', baseline_path, args.som_report, build_manifest, original_manifest, frozen_path]
    inputs += [ROOT/relative for relative in unchanged]
    inputs += [SOURCE/'broker.cpp', SOURCE/'fake_j2534.cpp', SOURCE/'build/broker.exe', SOURCE/'build/fake_j2534.dll']
    inputs += sorted(SOURCE.glob('test_*message*.py'))
    result = {
        'schema': 1,
        'status': 'PASS_OFFLINE_PASSIVE_RECEIVER_QUALIFICATION',
        'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'artifact_class': 'FIXED_BF_A8_PASSIVE_OBSERVER',
        'real_provider_loaded': False,
        'physical_backend_executed': False,
        'physical_acceptance': 'NOT_TESTED_FOR_THIS_NEW_BUILD',
        'RK02_release_requalified': False,
        'RK02_frozen_files_unchanged': len(frozen['files']),
        'original_broker_unchanged': True,
        'unchanged_host_files': unchanged,
        'production_change_scope': 'Only copied broker RX loop and two RX constants; fixed transmit and post-RX validation source unchanged',
        'baseline_test_groups': baseline['test_groups'],
        'targeted_tests': record(args.som_report),
        'reproducible_builds': reproduction,
        'reproduced_fake_exchange': {'exit_code': fake.returncode, 'frames': frames, 'cleanup': rows[-1]},
        'provider_hash_read_only': PROVIDER_SHA,
        'files': [record(path) for path in inputs],
        'limitations': ['Offline fake cases are not vehicle observations.',
                       'Physical BF identity and all requested passive samples remain required before G11.',
                       'This report does not authorize RK02 or any flash operation.'],
    }
    write_json(output/'QUALIFICATION.json', result)
    print(json.dumps({'status': result['status'], 'report': str(output/'QUALIFICATION.json'),
                      'broker_sha256': sha(SOURCE/'build/broker.exe'), 'baseline_test_groups': baseline['test_groups']}))


if __name__ == '__main__':
    main()
