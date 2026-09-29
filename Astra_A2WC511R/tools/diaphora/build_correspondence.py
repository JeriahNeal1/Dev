"""Join Diaphora proposals to raw ROM, native chunks/xrefs and source provenance.

No IDA metadata import. A ratio of one alone never promotes semantic identity.
"""
from pathlib import Path
from hashlib import sha256
from difflib import SequenceMatcher
from collections import Counter
import json,sqlite3,argparse,re
ROOT=Path('C:/Dev/Astra_A2WC511R');WORK=ROOT/'work/diaphora'
def h(path):return sha256(Path(path).read_bytes()).hexdigest()
def decoded(value):
    if value is None:return None
    try:return json.loads(value)
    except (ValueError,TypeError):return value
def readonly(path):return sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True)
class Export:
    def __init__(self,path):
        self.path=Path(path);self.identity=json.loads(self.path.with_suffix('.identity.json').read_text())
        self.analysis=json.loads(self.path.with_suffix('.analysis.json').read_text())
        self.raw=Path(self.identity['rom']['path']).read_bytes();assert sha256(self.raw).hexdigest()==self.identity['rom']['sha256']
        self.native={f['start']:f for f in self.analysis['functions']}
        with readonly(path) as db:
            db.row_factory=sqlite3.Row;self.functions={int(r['address']):dict(r) for r in db.execute('select * from functions')}
            self.instruction_addresses={}
            for r in db.execute('select func_id,address from instructions'):
                self.instruction_addresses.setdefault(int(r['func_id']),[]).append(int(r['address']))
        self.extent_counts=Counter(self.bytes(f) for f in self.native.values())
    def bytes(self,f):return b''.join(self.raw[a:b] for a,b in f['chunks'])
    def side(self,ea):
        f=self.functions[ea];n=self.native[ea]
        literals=[]
        for pc in sorted(set(self.instruction_addresses.get(f['id'],[]))):
            op=int.from_bytes(self.raw[pc:pc+2],'big')
            if op>>12 in (9,13):
                width=2 if op>>12==9 else 4
                address=pc+4+(op&255)*2 if width==2 else ((pc+4)&~3)+(op&255)*4
                literals.append({'instruction':pc,'literal_address':address,'width':width,'value':int.from_bytes(self.raw[address:address+width],'big'),'bytes':self.raw[address:address+width].hex(),
                                 'inside_declared_chunks':any(a<=address and address+width<=b for a,b in n['chunks'])})
        return {'rom_sha256':self.identity['rom']['sha256'],'rom_path':self.identity['rom']['path'],
                'address':ea,'address_hex':f'0x{ea:08X}','name':f['name'],'function_span':n['end']-ea,
                'chunks':n['chunks'],'chunk_bytes':sum(b-a for a,b in n['chunks']),
                'exported_instruction_size':f['size'],'instruction_count':f['instructions'],
                'nodes':f['nodes'],'edges':f['edges'],'cyclomatic_complexity':f['cyclomatic_complexity'],
                'callers':[x for x in n['inbound'] if x['type'] in (16,17)],
                'all_static_inbound':n['inbound'],'callees':[x for x in n['references'] if x['type'] in (16,17)],
                'constants':decoded(f['constants']),'referenced_symbolic_names':decoded(f['names']),
                'strings':{'status':'not separately classified by structural exporter','named_references':decoded(f['names'])},
                'referenced_data':[x for x in n['references'] if not x['iscode']],'pc_relative_literal_dependencies':literals,
                'referenced_data_boundary_status':'xref targets only; no universal object bounds implied',
                'raw_chunk_sha256':sha256(self.bytes(n)).hexdigest(),'frame_size':n['frame_size'],'frame_regs':n['frame_regs']}

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    db=sqlite3.connect(a.output/'FUNCTION_CORRESPONDENCE.sqlite')
    db.executescript('create table correspondence(id integer primary key, comparison text, source_rom_sha256 text,target_rom_sha256 text,source_address integer,target_address integer, confidence text,ratio real,exact_chunk_bytes integer,source_bytes integer,target_bytes integer,evidence_json text); create index source_lookup on correspondence(source_rom_sha256,source_address); create index target_lookup on correspondence(target_rom_sha256,target_address); create table provenance(key text primary key,value_json text);')
    cache={};summary=[];density=[];queue=[];records=[]
    symbols=json.loads((ROOT/'reports/local/diaphora/merpmod_reference/A2WC510S_map_symbols.json').read_text())
    names={x['address_int']:x['name'] for x in symbols['symbols'] if x['name_category']!='other_label' or not x['name'].startswith(('sub_','loc_','off_','unk_','byte_','word_','dword_'))}
    current_names=ROOT/'reports/local/diaphora/idb_reopen_audit/CURRENT_METADATA_FROM_FORENSIC_COPY.json'
    existing={f['address']:f['name'] for f in json.loads(current_names.read_text())['functions']}
    reviewed_path=ROOT/'reports/local/diaphora/merpmod_mapping/REVIEWED_MATCHES.json'
    reviewed=json.loads(reviewed_path.read_text())
    crossrom_path=Path('C:/Dev/A2WC511R_Sim/diaphora_crossrom/runs/20260926T025326.453332Z/crossrom_regression.json')
    crossrom=json.loads(crossrom_path.read_text());assert crossrom['status']=='PASS'
    crossrom_mappings={r['rom']['sha256']:r for r in crossrom['ROM_mapping']}
    range_review=ROOT/'reports/local/diaphora/range_ownership_review/RANGE_OWNERSHIP.json'
    smaller_review=ROOT/'reports/local/diaphora/range_ownership_review/SMALLER_CANDIDATE_FACTS.json'
    chosen={}
    for candidate in sorted((WORK/'comparisons').glob('*/comparison.json')):
        label=candidate.parent.name
        if not label.startswith(('stock_','archive_')) or 'repeat' in label or 'determinism' in label:continue
        version=int(label.rsplit('_',1)[-1]);base=re.sub(r'_\d+$','',label)
        if version<3:continue # Earlier results predate the unmatched-side repair.
        if json.loads(candidate.read_text()).get('status')!='PASS':continue
        if base not in chosen or version>chosen[base][0]:chosen[base]=(version,candidate)
    for _,manifest in sorted(chosen.values(),key=lambda x:str(x[1])):
        report=json.loads(manifest.read_text())
        if report['status']!='PASS' or not report.get('left_rom') or not report.get('right_rom'):continue
        if 'repeat' in manifest.parent.name or 'determinism' in manifest.parent.name:continue
        exports=[]
        for side in ['left','right']:
            path=report[side+'_export']['path']
            if path not in cache:cache[path]=Export(path)
            exports.append(cache[path])
        left,right=exports;result=manifest.parent/'results.diaphora'
        with readonly(result) as conn:
            conn.row_factory=sqlite3.Row;matches=[dict(r) for r in conn.execute('select * from results')]
        result_hash=h(result);manifest_hash=h(manifest)
        counts=Counter()
        for match in matches:
            x,y=int(match['address'],16),int(match['address2'],16)
            lf,rf=left.functions[x],right.functions[y];ln,rn=left.native[x],right.native[y]
            lb,rb=left.bytes(ln),right.bytes(rn)
            exact=lb==rb;cfg=(lf['nodes'],lf['edges'],lf['cyclomatic_complexity'])==(rf['nodes'],rf['edges'],rf['cyclomatic_complexity'])
            clean1,clean2=lf['clean_assembly'] or '',rf['clean_assembly'] or ''
            similarity=1.0 if clean1==clean2 else SequenceMatcher(None,clean1.splitlines(),clean2.splitlines(),autojunk=False).ratio()
            unique=left.extent_counts[lb]==right.extent_counts[rb]==1
            confidence='HIGH_CONFIDENCE_HOMOLOG' if exact and unique and len(lb)>=24 and cfg else 'CANDIDATE_HOMOLOG'
            if float(match['ratio'])<0.6 or match['type'] in ('unreliable','multimatch'):confidence='LOW_CONFIDENCE'
            source_side,target_side=left.side(x),right.side(y)
            literal_values_equal=[(v['width'],v['value']) for v in source_side['pc_relative_literal_dependencies']]==[(v['width'],v['value']) for v in target_side['pc_relative_literal_dependencies']]
            validation=[];notes=['Static proposal only; live values, literal pointees, calculated entry paths and execution context remain separate obligations.']
            if source_side['rom_sha256']==crossrom['baseline']['sha256'] and target_side['rom_sha256'] in crossrom_mappings:
                mapping=crossrom_mappings[target_side['rom_sha256']]
                if x==y==0x4260 and exact and cfg and literal_values_equal:
                    confidence='VERIFIED_IDENTITY'
                    validation.append({'path':str(crossrom_path),'sha256':h(crossrom_path),'scope':'Identical routine bytes and external literal values; existing scoped GPR/SR/PR/SP/RAM differential regression. Not ownership or complete execution-context proof.'})
                if x==0x1466e and y==int(mapping['range_entry'],16):
                    confidence='HIGH_CONFIDENCE_HOMOLOG'
                    validation.append({'path':str(crossrom_path),'sha256':h(crossrom_path),'scope':'Normalized range CFG and ordered RAM differential contract; explicit source/flags/output role mapping required.','target_RAM_roles':mapping['range_roles']})
                    validation.append({'path':str(range_review),'sha256':h(range_review),'scope':'Ordinary entry proof; arbitrary interior entry and complete target domain are not closed.'})
            for review in reviewed:
                if manifest.parent.name.startswith(review['comparison_prefix']) and x==review['source_address'] and y==review['target_address']:
                    confidence='HIGH_CONFIDENCE_HOMOLOG' if review['confidence']=='HIGH_CONFIDENCE_STRUCTURAL_IDENTITY' else review['confidence']
                    validation.append({'path':review['evidence_path'],'sha256':h(review['evidence_path']),'scope':review['reason']});notes.append(review['reason'])
            if '510S' in right.identity['rom']['path'] and y in names:target_side['upstream_source_name']=names[y]
            evidence={'comparison':manifest.parent.name,'source':source_side,'target':target_side,'diaphora':match,
                      'exact_raw_chunk_bytes':exact,'normalized_assembly_similarity':similarity,'matching_cfg_counts':cfg,
                      'ordered_PC_relative_literal_values_equal':literal_values_equal,
                      'raw_chunk_unique_in_both_exported_function_sets':unique,'confidence':confidence,
                      'independent_validation':validation,'semantic_notes':notes,
                      'provenance':{'comparison_manifest':str(manifest),'comparison_manifest_sha256':manifest_hash,'result_database':str(result),'result_sha256':result_hash,
                                    'source_analysis':str(left.path.with_suffix('.analysis.json')),'target_analysis':str(right.path.with_suffix('.analysis.json'))},
                      'ownership_proven':False,'metadata_imported':False}
            counts[confidence]+=1;records.append(evidence)
            db.execute('insert into correspondence(comparison,source_rom_sha256,target_rom_sha256,source_address,target_address,confidence,ratio,exact_chunk_bytes,source_bytes,target_bytes,evidence_json) values(?,?,?,?,?,?,?,?,?,?,?)',
                       (manifest.parent.name,evidence['source']['rom_sha256'],evidence['target']['rom_sha256'],x,y,confidence,float(match['ratio']),int(exact),len(lb),len(rb),json.dumps(evidence,separators=(',',':'))))
            if lf['size']>=rf['size']+8 and 'stock_511R_vs_' in manifest.parent.name:
                density.append({'source':hex(x),'target':hex(y),'source_export':str(left.path),'target_export':str(right.path),'source_span':len(lb),'target_span':len(rb),'source_instructions':lf['instructions'],'target_instructions':rf['instructions'],'difference':len(lb)-len(rb),'ratio':float(match['ratio']),'confidence':confidence,'same_cfg':cfg,'comparison':manifest.parent.name,'review_status':'UNREVIEWED_NOT_SEMANTICALLY_EQUIVALENT'})
                if (x,y)==(0x195e8,0x17dfc):density[-1].update({'review_status':'REJECTED_EQUIVALENCE_CONCRETE_COUNTEREXAMPLE','evidence':str(smaller_review),'evidence_sha256':h(smaller_review),'reason':'Complete OEM entry/callee execution yields source counter4 versus target0; smaller sibling drops conditional increment behavior.'})
                elif x in (0x31fc,0x3214):density[-1].update({'review_status':'REJECTED_CONTIGUOUS_TAIL_INFERENCE','evidence':str(smaller_review),'evidence_sha256':h(smaller_review),'reason':'Instruction count sums noncontiguous shared interrupt/SCI chunks; altered callees and critical-section behavior. No equivalent owned contiguous tail.'})
            if '510S' in right.identity['rom']['path'] and y in names:
                proposed=names[y]
                if proposed.startswith(('sub_','loc_','off_','unk_')):continue
                evidence['target']['upstream_source_name']=proposed
                queue.append({'target_A2WC511R_address':x,'current_name_from_saved_export':existing.get(x,lf['name']),'proposed_name':proposed,'source_ROM_sha256':right.identity['rom']['sha256'],'source_address':y,'source_name_provenance':symbols['source'],
                              'structural_evidence':{'exact_raw_chunk_bytes':exact,'cfg_equal':cfg,'unique_within_exports':unique},'diaphora':match,'independent_simulator_static_evidence':validation,'confidence':confidence,
                              'decision':'HOLD_REQUIRES_SEMANTIC_REVIEW','authoritative_import':False,'current_name_provenance':str(current_names),'current_name_provenance_sha256':h(current_names),'note':'Upstream map label is a claim, not proof; current authoritative IDB separately has reopen defect.'})
        summary.append({'comparison':manifest.parent.name,'match_count':len(matches),'confidence_counts':dict(counts),'result_sha256':h(result)})
    density.sort(key=lambda d:(-d['ratio'],-d['difference']))
    provenance={'schema':1,'generator_sha256':h(__file__),'comparisons':summary,'export_identities':{k:v.identity for k,v in cache.items()},'no_verified_identity_by_score_alone':True,'no_authoritative_import':True}
    db.execute('insert into provenance values(?,?)',('generation',json.dumps(provenance)));db.commit();assert db.execute('pragma integrity_check').fetchone()[0]=='ok';db.close()
    for name,value in [('SUMMARY.json',provenance),('SMALLER_IMPLEMENTATION_CANDIDATES.json',density),('METADATA_IMPORT_REVIEW_QUEUE.json',queue)]:
        (a.output/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    with (a.output/'FUNCTION_CORRESPONDENCE.jsonl').open('w',encoding='utf-8') as stream:
        for record in records:stream.write(json.dumps(record,separators=(',',':'))+'\n')
    print(json.dumps({'comparisons':len(summary),'rows':len(records),'density_candidates':len(density),'metadata_review_items':len(queue)}))
if __name__=='__main__':main()
