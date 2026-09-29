"""Side-by-side native RomRaider SSM acceptance. No device or provider setup."""
import hashlib,json,pathlib,subprocess,datetime,xml.etree.ElementTree as ET
src=pathlib.Path(__file__).parent
root=src.parents[2]
work=root/'work/gate_closure/virtual_rr';work.mkdir(parents=True,exist_ok=True)
out=root/'reports/local/gate_closure/interfaces'/('virtual_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'));out.mkdir()
stock=pathlib.Path(r'C:\Tuning\Romraider\Logger\logger_STD_EN_v370_A2WC511R_tcu_gear_debug.xml')
fragment=root/'work/patches/m0_final_05/A2WC511R_M0.EXPERIMENTAL.logger.fragment.xml'
snapshots=pathlib.Path(r'C:\Dev\A2WC511R_Sim\runs\20260925T210127.390057Z_gate_scenarios\virtual_ram_snapshots.json')
rom=root/'work/patches/m0_final_05/A2WC511R.M0.EXPERIMENTAL_UNAPPROVED.raw.bin'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Insertion only: existing definition byte text remains unchanged; no global configuration.
text=stock.read_text(encoding='utf-8');frag=fragment.read_text(encoding='utf-8');inner=frag[frag.index('<ecuparams>')+len('<ecuparams>'):frag.rindex('</ecuparams>')]
merged=work/'logger_existing_plus_final05.VIRTUAL_ONLY.xml';merged.write_text(text.replace('</ecuparams>',inner+'\n</ecuparams>',1),encoding='utf-8')
assert merged.read_text(encoding='utf-8').replace(inner+'\n</ecuparams>','</ecuparams>',1)==text
a=ET.fromstring(stock.read_bytes());b=ET.fromstring(merged.read_bytes())
old=a.find("protocols/protocol[@id='SSM']")
if old is None:old=a.find(".//protocol[@id='SSM']")
new=b.find(".//protocol[@id='SSM']")
assert len(new.find('ecuparams'))-len(old.find('ecuparams'))==17
settings=work/'settings.xml'
if not settings.exists():settings.write_bytes(pathlib.Path(r'C:\Program Files\RomRaider\settings.xml').read_bytes())
(work/'home').mkdir(exist_ok=True)
jdk=pathlib.Path(r'C:\Renesas\e2_studio\eclipse\plugins\org.eclipse.justj.openjdk.hotspot.jre.full.win32.x86_64_21.0.11.v20260515-1531\jre\bin')
java=pathlib.Path(r'C:\Program Files\RomRaider\jdk-11.0.14.1+1-jre\bin\java.exe')
cp=';'.join([str(work/'classes'),r'C:\Program Files\RomRaider\RomRaider.jar',str(root/'integrations/romraider/dist/romraider-bridge.jar'),r'C:\Program Files\RomRaider\lib\common\*',r'C:\Program Files\RomRaider\i18n'])
cmd=[str(jdk/'javac.exe'),'--release','8','-cp',cp,'-d',str(work/'classes'),*[str(p) for p in (src/'src').rglob('*.java')]]
r=subprocess.run(cmd,capture_output=True,text=True);(out/'compile.log').write_text(r.stdout+r.stderr);r.check_returncode()
args=[str(java),'-Duser.home='+str(work/'home'),'-cp',cp,'a2wc.virtualrr.NativeLoggerAcceptance',str(out),str(snapshots),sha(snapshots),str(rom),sha(rom),str(stock),str(merged)]
(out/'command.txt').write_text(subprocess.list2cmdline(args))
identities={str(p):sha(p) for p in [java,pathlib.Path(r'C:\Program Files\RomRaider\RomRaider.jar'),stock,fragment,snapshots,rom,merged,*sorted((src/'src').rglob('*.java'))]}
(out/'identities.json').write_text(json.dumps(identities,indent=2))
r=subprocess.run(args,cwd=work,capture_output=True,text=True,creationflags=subprocess.CREATE_NO_WINDOW);(out/'native.log').write_text(r.stdout+r.stderr)
assert all(sha(pathlib.Path(p))==h for p,h in identities.items())
print(out);print(r.stdout+r.stderr);r.check_returncode()
