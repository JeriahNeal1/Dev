import datetime,hashlib,json,pathlib,subprocess
src=pathlib.Path(__file__).parent;root=src.parents[2];work=root/'work/gate_closure/virtual_rr'
out=root/'reports/local/gate_closure/interfaces'/('collector_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
snap=pathlib.Path(r'C:\Dev\A2WC511R_Sim\runs\20260925T210127.390057Z_gate_scenarios\virtual_ram_snapshots.json');rom=root/'work/patches/m0_final_05/A2WC511R.M0.EXPERIMENTAL_UNAPPROVED.raw.bin'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cp=';'.join([str(work/'classes'),r'C:\Program Files\RomRaider\RomRaider.jar',str(root/'integrations/romraider/dist/romraider-bridge.jar'),r'C:\Program Files\RomRaider\lib\common\*',r'C:\Program Files\RomRaider\i18n'])
java=pathlib.Path(r'C:\Program Files (x86)\Java\jre1.8.0_503\bin\java.exe')
args=[str(java),'-Duser.home='+str(work/'home'),'-cp',cp,'a2wc.virtualrr.ReadOnlySSMCollector','virtual',str(out),str(snap),sha(snap),str(rom),sha(rom)]
r=subprocess.run(args,cwd=work,capture_output=True,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
out.mkdir(exist_ok=True);(out/'native.log').write_text(r.stdout+r.stderr);(out/'command.txt').write_text(subprocess.list2cmdline(args));(out/'runtime.json').write_text(json.dumps({'path':str(java),'sha256':sha(java)},indent=2))
print(out);print(r.stdout+r.stderr);r.check_returncode()
v=json.loads((out/'acquisition_result.json').read_text());assert v['classification']=='VIRTUAL_SOFTWARE_SCENARIO_NOT_VEHICLE_TELEMETRY' and v['two_full_reads_identical'] and v['java_arch']=='32'
assert v['rom_hashes']==[sha(rom),sha(rom)]
rows=json.loads((out/'raw_six_channel_samples.json').read_text());assert len(rows)>100 and all(all(k in row for k in ['FFFF4C75','FFFF4C8D','FFFF4CA1','FFFF4C50','FFFF4BC1','FFFF4BC2']) for row in rows)
assert sum(row['phase']=='initial_burst' for row in rows)==60 and sum(row['phase']=='final_burst' for row in rows)==60
assert [row['sample_index'] for row in rows]==list(range(len(rows)))
assert all(b['host_elapsed_ms']>=a['host_elapsed_ms'] for a,b in zip(rows,rows[1:]))
badargs=args.copy();badargs[-3]='0'*64;badout=out/'negative_constructor_hash';badargs[badargs.index('virtual')+1]=str(badout)
bad=subprocess.run(badargs,cwd=work,capture_output=True,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
(out/'negative_constructor.log').write_text(bad.stdout+bad.stderr)
negative=json.loads((badout/'acquisition_result.json').read_text());assert bad.returncode!=0 and negative['status']=='BLOCKED_ABORTED_NO_FALLBACK' and negative['requests']==0
