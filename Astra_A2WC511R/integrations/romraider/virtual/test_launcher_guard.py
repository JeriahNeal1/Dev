import ctypes,json,pathlib,subprocess
src=pathlib.Path(__file__).parent;root=src.parents[2];classes=root/'work/gate_closure/virtual_rr/classes';out=root/'reports/local/gate_closure/interfaces'
probe=classes/'_UNREVIEWED_GUARD_TEST.class';assert not probe.exists();failedout=out/'must_not_exist_hidden_runtime_guard';assert not failedout.exists()
try:
    probe.write_bytes(b'Acceptance probe: never loaded')
    assert ctypes.windll.kernel32.SetFileAttributesW(str(probe),2)
    r=subprocess.run([r'C:\Program Files\PowerShell\7\pwsh.exe','-NoProfile','-File',str(src/'Invoke-ReadOnlySSM.ps1'),'-Mode','Virtual','-OutputDirectory',str(failedout)],capture_output=True,text=True)
    assert r.returncode!=0 and 'Runtime directory inventory changed' in r.stderr and not failedout.exists(),r.stdout+r.stderr
    (out/'runtime_guard_test.json').write_text(json.dumps({'status':'PASS','hidden_unreviewed_class_rejected_before_Java':True,'output_created':False},indent=2))
finally:
    if probe.exists():ctypes.windll.kernel32.SetFileAttributesW(str(probe),128);probe.unlink()
print('PASS hidden class inventory rejection; probe removed')
