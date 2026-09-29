import csv,hashlib,json,pathlib
root=pathlib.Path(__file__).resolve().parents[3];base=root/'reports/local/gate_closure/interfaces'
gui=base/'logger_gui_20260925T213026Z';native=base/'virtual_20260925T213111Z'
snap=pathlib.Path(r'C:\Dev\A2WC511R_Sim\runs\20260925T210127.390057Z_gate_scenarios\virtual_ram_snapshots.json')
samples=json.loads(snap.read_text())['snapshots'];defs=json.loads((native/'native_loaded_definitions.json').read_text());byname={d['name']:d for d in defs}
def value(sample,name):
    n=0
    for address in byname[name]['addresses']:n=(n<<8)|sample['bytes'][f'{int(address,16)|0xff000000:08X}']
    return n
views=json.loads((gui/'native_gui_views.json').read_text());assert len(views)==15;checks=0
for view in views:
    s=samples[view['sample_index']];assert len(view['native_live_rows'])==20
    for name,current,unit in view['native_live_rows']:
        assert unit=='raw' and int(current)==value(s,name),(view['sample_index'],name,current,value(s,name));checks+=1
csvpath=next((gui/'VIRTUAL_NATIVE_CSV').glob('*.csv'))
with csvpath.open(newline='',encoding='utf-8-sig') as f:
    reader=csv.DictReader(f);fields=reader.fieldnames[1:];names=[n.removesuffix(' (raw)') for n in fields]
    valid={tuple(value(s,name) for name in names):i for i,s in enumerate(samples)}
    count=0;seen=set();last=-1;unmatched=[]
    for row in reader:
        timestamp=int(row['Time (msec)']);assert timestamp>=last;last=timestamp
        values=tuple(int(row[k]) for k in fields)
        if values not in valid:unmatched.append(count)
        else:seen.add(valid[values])
        count+=1
assert not unmatched,unmatched[:20]
assert len(seen)==15
result={'status':'PASS','classification':'VIRTUAL_SOFTWARE_SCENARIO_NOT_VEHICLE_TELEMETRY','native_GUI_display_checks':checks,'native_CSV_rows':count,'every_CSV_row_equals_one_compiled_snapshot':True,'compiled_samples_seen':len(seen),'native_CSV_sha256':hashlib.sha256(csvpath.read_bytes()).hexdigest(),'snapshot_sha256':hashlib.sha256(snap.read_bytes()).hexdigest(),'time_semantics':'CSV timestamps are host logger milliseconds; simulator10ms scenario indexes are explicitly virtual, neither is measured ECU cadence. Repeated rows are not independent physical observations.'}
(gui/'display_and_csv_verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
