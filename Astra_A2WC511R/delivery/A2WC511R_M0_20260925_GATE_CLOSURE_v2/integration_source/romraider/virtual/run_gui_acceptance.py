import datetime,hashlib,json,pathlib,subprocess
src=pathlib.Path(__file__).parent;root=src.parents[2];work=root/'work/gate_closure/virtual_rr'
out=root/'reports/local/gate_closure/interfaces'/('logger_gui_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'));out.mkdir()
profile=work/'empty_VIRTUAL_profile.xml';profile.write_text('<profile protocol="SSM"/>')
jdk=pathlib.Path(r'C:\Renesas\e2_studio\eclipse\plugins\org.eclipse.justj.openjdk.hotspot.jre.full.win32.x86_64_21.0.11.v20260515-1531\jre\bin')
cp=';'.join([str(work/'gui_classes'),str(work/'classes'),r'C:\Program Files\RomRaider\RomRaider.jar',str(root/'integrations/romraider/dist/romraider-bridge.jar'),r'C:\Program Files\RomRaider\lib\common\*',r'C:\Program Files\RomRaider\i18n'])
r=subprocess.run([str(jdk/'javac.exe'),'--release','8','-cp',cp,'-d',str(work/'gui_classes'),*[str(p) for p in (src/'gui_src').rglob('*.java')]],capture_output=True,text=True);(out/'compile.log').write_text(r.stdout+r.stderr);r.check_returncode()
snap=pathlib.Path(r'C:\Dev\A2WC511R_Sim\runs\20260925T210127.390057Z_gate_scenarios\virtual_ram_snapshots.json');rom=root/'work/patches/m0_final_05/A2WC511R.M0.EXPERIMENTAL_UNAPPROVED.raw.bin'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
args=[r'C:\Program Files\RomRaider\jdk-11.0.14.1+1-jre\bin\java.exe','-Duser.home='+str(work/'home'),'-cp',cp,'a2wc.virtualrr.NativeLoggerGui',str(out),str(snap),sha(snap),str(rom),sha(rom),str(work/'logger_existing_plus_final05.VIRTUAL_ONLY.xml'),str(profile)]
(out/'command.txt').write_text(subprocess.list2cmdline(args))
with (out/'native.log').open('wb') as log:
    p=subprocess.Popen(args,cwd=work,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    try:rc=p.wait(timeout=65)
    except subprocess.TimeoutExpired:p.kill();p.wait();rc=124;(out/'timeout.txt').write_text('Bounded native GUI attempt timed out at65seconds; no success claimed')
print(out);print((out/'native.log').read_text()[-3000:]);raise SystemExit(rc)
