package rombridge;

import java.util.*;
import java.lang.reflect.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.io.StringWriter;
import javax.xml.transform.*;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import javax.swing.SwingUtilities;
import org.w3c.dom.Document;

/** Adapter to RomRaider's actual loaded model, not a second ECU-definition parser.
 * API inspected at RR dafe0c36c1a68efadbeedb2825f3855463fdbc35. Local smoke test required.
 * All calls from the agent run on Swing's EDT. No ECU/J2534 or debugger interface.
 */
public final class RomAccess {
    public interface EditorProvider { Object editor() throws Exception; }
    public interface Approval { boolean approve(String message); }
    private final EditorProvider provider;
    private final Approval approval;
    private final boolean applyEnabled;
    private final Path work;
    private final IdentityHashMap<Object,String> ids=new IdentityHashMap<Object,String>();
    private final Map<String,Pending> pending=new LinkedHashMap<String,Pending>();
    public final String session=UUID.randomUUID().toString();
    private static final int MAX_CELLS=65536;
    private long requestDeadline=Long.MAX_VALUE;
    public Object dispatchBefore(String op,Map<String,Object> q,long deadline)throws Exception {
        requestDeadline=deadline;
        try { checkDeadline(); return dispatch(op,q); }
        finally { requestDeadline=Long.MAX_VALUE; }
    }
    private void checkDeadline() {
        if (System.nanoTime()>=requestDeadline) throw new IllegalStateException("Request expired; no delayed commit is permitted");
    }

    public RomAccess(EditorProvider provider, Approval approval, boolean enabled, Path work)throws Exception {
        this.provider=provider;this.approval=approval;this.applyEnabled=enabled;
        Files.createDirectories(work);this.work=work.toRealPath();
    }
    public static Map<String,Object> map(Object... pairs){Map<String,Object> r=new LinkedHashMap<String,Object>();for(int i=0;i<pairs.length;i+=2)r.put((String)pairs[i],pairs[i+1]);return r;}
    static Object call(Object o,String method,Object...args)throws Exception{
        if(o==null)throw new IllegalArgumentException("Missing object for "+method);
        Class<?> c=(o instanceof Class)?(Class<?>)o:o.getClass();
        for(Method m:c.getMethods()){
            if(!m.getName().equals(method)||m.getParameterTypes().length!=args.length)continue;
            boolean ok=true;Class<?>[] ps=m.getParameterTypes();
            for(int i=0;i<args.length;i++){Class<?> p=ps[i];if(p==int.class)p=Integer.class;if(p==double.class)p=Double.class;if(p==boolean.class)p=Boolean.class;if(args[i]!=null&&!p.isInstance(args[i]))ok=false;}
            if(ok){try{return m.invoke(o instanceof Class?null:o,args);}catch(InvocationTargetException e){Throwable t=e.getCause();if(t instanceof Exception)throw (Exception)t;throw e;}}
        }
        throw new NoSuchMethodException(c.getName()+"."+method+"/"+args.length);
    }
    static Object optional(Object o,String method){try{return call(o,method);}catch(Exception e){return null;}}
    static Object field(Object o,String name)throws Exception{
        for(Class<?> c=o.getClass();c!=null;c=c.getSuperclass())try{Field f=c.getDeclaredField(name);f.setAccessible(true);return f.get(o);}catch(NoSuchFieldException e){}
        throw new NoSuchFieldException(name);
    }
    static double number(Object v){if(!(v instanceof Number)||!Double.isFinite(((Number)v).doubleValue()))throw new IllegalArgumentException("Expected finite number");return ((Number)v).doubleValue();}
    static int integer(Object v){double d=number(v);if(d!=(int)d)throw new IllegalArgumentException("Expected integer");return (int)d;}
    static String text(Object v){if(!(v instanceof String))throw new IllegalArgumentException("Expected string");return (String)v;}
    static String sha(byte[] b)throws Exception{byte[] d=MessageDigest.getInstance("SHA-256").digest(b);StringBuilder s=new StringBuilder();for(byte v:d)s.append(String.format("%02x",v&255));return s.toString();}
    static String jsonHash(Object o)throws Exception{return sha(Json.stringify(o).getBytes(StandardCharsets.UTF_8));}
    static void exact(Map<String,Object> q,String...keys){Set<String>s=new HashSet<String>(Arrays.asList(keys));if(!s.equals(q.keySet()))throw new IllegalArgumentException("Unexpected/missing fields; expected "+s);}
    private List<?> roms()throws Exception{Object e=provider.editor();if(e==null)throw new IllegalStateException("Open RomRaider ECU Editor first");return (List<?>)call(e,"getImages");}
    private String id(Object rom){if(!ids.containsKey(rom))ids.put(rom,"rom_"+(ids.size()+1));return ids.get(rom);}
    private Object rom(String id)throws Exception{for(Object r:roms())if(id(r).equals(id))return r;throw new IllegalArgumentException("ROM not open in this editor session");}
    private byte[] bytes(Object rom)throws Exception{return (byte[])call(rom,"getBinary");}
    private Map<String,Object> info(Object r)throws Exception{
        Object dp=optional(r,"getDefinitionPath");Object full=optional(r,"getFullFileName");
        return map("rom_id",id(r),"file_name",call(r,"getFileName"),"file_path",full==null?null:full.toString(),"calid",call(r,"getRomIDString"),"binary_sha256",sha(bytes(r)),"size_bytes",bytes(r).length,"definition_path",dp==null?null:dp.toString(),"faulty_tables",optional(r,"getFaultyTables"));
    }
    private LinkedHashMap<String,Object> tableObjects(Object r)throws Exception{
        LinkedHashMap<String,Object> ts=new LinkedHashMap<String,Object>();
        for(Object t:(List<?>)call(r,"getTables")){
            String name=text(call(t,"getName"));if(ts.put(name,t)!=null)throw new IllegalStateException("Duplicate table name");
            for(String[] pair:new String[][]{{"::x","getXAxis"},{"::y","getYAxis"},{"::axis","getAxis"}}){Object a=optional(t,pair[1]);if(a!=null){if(ts.put(name+pair[0],a)!=null)throw new IllegalStateException("Axis key collision");}}
        }
        return ts;
    }
    private Object[][] cells(Object t)throws Exception{
        Object three=optional(t,"get3dData");
        if(three!=null){int nx=Array.getLength(three);int ny=nx==0?0:Array.getLength(Array.get(three,0));if((long)nx*ny>MAX_CELLS)throw new IllegalArgumentException("Table too large");Object[][] rows=new Object[ny][nx];for(int x=0;x<nx;x++)for(int y=0;y<ny;y++)rows[y][x]=Array.get(Array.get(three,x),y);return rows;}
        Object one=call(t,"getData");int n=Array.getLength(one);if(n>MAX_CELLS)throw new IllegalArgumentException("Table too large");Object[][] rows=new Object[1][n];for(int i=0;i<n;i++)rows[0][i]=Array.get(one,i);return rows;
    }
    private Map<String,Object> scale(Object s){if(s==null)return map();return map("category",optional(s,"getCategory"),"units",optional(s,"getUnits"),"expression",optional(s,"getExpression"),"byte_expression",optional(s,"getByteExpression"),"format",String.valueOf(optional(s,"getFormat")));}
    private List<Object> presets(Object t)throws Exception{
        List<Object> out=new ArrayList<Object>();Object pm;
        try{pm=field(t,"presetManager");}catch(NoSuchFieldException e){return out;}
        if(pm!=null)for(Object p:(List<?>)call(pm,"getPresets"))out.add(map("name",field(p,"name"),"offset",field(p,"dataCellOffset"),"data",field(p,"data"),"bitmask",field(p,"isBitMask"),"active",call(pm,"isPresetActive",p)));
        return out;
    }
    private Map<String,Object> describe(String key,Object t,boolean withCells)throws Exception{
        Object[][] cs=cells(t);boolean stat=Boolean.TRUE.equals(call(t,"isStaticDataTable"));
        Map<String,Object>d=map("key",key,"name",call(t,"getName"),"class",t.getClass().getName(),"type",String.valueOf(call(t,"getType")),"category",call(t,"getCategory"),"description",call(t,"getDescription"),"rows",cs.length,"columns",cs.length==0?0:cs[0].length,"storage_address",call(t,"getStorageAddress"),"ram_offset",call(t,"getRamOffset"),"storage_type",call(t,"getStorageType"),"endian",String.valueOf(call(t,"getEndian")),"signed",call(t,"isSignedData"),"bitmask",optional(t,"getBitMask"),"layout",String.valueOf(optional(t,"getDataLayout")),"static",stat,"locked",call(t,"isLocked"),"user_level",call(t,"getUserLevel"),"log_param",optional(t,"getLogParam"),"scale",scale(call(t,"getCurrentScale")));
        List<Object> scales=new ArrayList<Object>();for(Object s:(List<?>)call(t,"getScales"))scales.add(scale(s));d.put("scales",scales);
        d.put("flip_x",optional(t,"getFlipX"));d.put("flip_y",optional(t,"getFlipY"));d.put("swap_xy",optional(t,"getSwapXY"));d.put("skip_cells",optional(t,"getSkipCells"));
        boolean checkpoint=String.valueOf(call(t,"getName")).toLowerCase(Locale.ROOT).contains("checksum fix");
        d.put("edit_capability",stat?"static_not_rom_backed":checkpoint?"checksum_special_read_only":Boolean.TRUE.equals(d.get("locked"))?"locked_read_only":"numeric_native_preview_required");
        if(withCells){
            List<Object> rows=new ArrayList<Object>();
            for(Object[] row:cs){List<Object> rr=new ArrayList<Object>();for(Object c:row){if(c==null){rr.add(map("error","unpopulated"));continue;}
                if(stat){String st=String.valueOf(optional(c,"getStaticText"));Double v=null;try{v=Double.valueOf(st);if(!Double.isFinite(v))v=null;}catch(Exception e){}rr.add(map("static_text",st,"real",v,"raw",null));}
                else {Object rv=call(c,"getRealValue");Object bv=call(c,"getBinValue");rr.add(map("real",finiteOrNull(rv),"raw",finiteOrNull(bv),"original_raw",finiteOrNull(optional(c,"getOriginalValue")),"storage_index",call(c,"getIndexInTable"),"bitmask",optional(c,"getBitMask"),"min_raw",finiteOrNull(optional(c,"getMinAllowedBin")),"max_raw",finiteOrNull(optional(c,"getMaxAllowedBin"))));}
            }rows.add(rr);}d.put("cells",rows);d.put("presets",presets(t));
        }
        return d;
    }
    private Map<String,Object> describeOrError(String key,Object t,boolean withCells) {
        try { return describe(key,t,withCells); }
        catch(Exception e) { return map("key",key,"name",String.valueOf(optional(t,"getName")),"class",t.getClass().getName(),"edit_capability","unsupported_read_only","error",e.getClass().getSimpleName()+": "+e.getMessage(),"rows",0,"columns",0,"cells",new ArrayList<Object>()); }
    }
    private void preflightModel(Object r)throws Exception {
        Object faulty=optional(r,"getFaultyTables");if(faulty instanceof Collection && !((Collection<?>)faulty).isEmpty())throw new IllegalStateException("RomRaider reported faulty tables; resolve definition coverage before preview");
        for(Map.Entry<String,Object> e:tableObjects(r).entrySet()) {
            Map<String,Object> d=describeOrError(e.getKey(),e.getValue(),true);
            if(d.containsKey("error")) throw new IllegalStateException("Native model coverage incomplete: "+e.getKey()+"; resolve before a transactional preview");
        }
    }
    private Object finiteOrNull(Object o){return o instanceof Number&&Double.isFinite(((Number)o).doubleValue())?o:null;}
    private String structureHash(Object r)throws Exception{List<Object>a=new ArrayList<Object>();for(Map.Entry<String,Object>e:tableObjects(r).entrySet())a.add(describeOrError(e.getKey(),e.getValue(),false));return jsonHash(a);}
    private Map<String,Object> snapshot(Object r)throws Exception{
        List<Object>a=new ArrayList<Object>();for(Map.Entry<String,Object>e:tableObjects(r).entrySet())a.add(describeOrError(e.getKey(),e.getValue(),true));
        String docHash=null;Object doc=optional(r,"getDocument");
        if(doc instanceof Document){TransformerFactory f=TransformerFactory.newInstance();f.setFeature(javax.xml.XMLConstants.FEATURE_SECURE_PROCESSING,true);Transformer tr=f.newTransformer();StringWriter sw=new StringWriter();tr.transform(new DOMSource((Document)doc),new StreamResult(sw));docHash=sha(sw.toString().getBytes(StandardCharsets.UTF_8));}
        return map("schema","rr-model-snapshot-v1","captured_utc",Instant.now().toString(),"bridge_session",session,"rom",info(r),"model_sha256",structureHash(r),"loaded_document_sha256",docHash,"tables",a);
    }
    private void refresh(Object r)throws Exception{
        Set<Object> seen=Collections.newSetFromMap(new IdentityHashMap<Object,Boolean>());
        for(Object t:tableObjects(r).values())if(seen.add(t)){
            if(!Boolean.TRUE.equals(call(t,"isStaticDataTable")))for(Object[]row:cells(t))for(Object c:row)if(c!=null)call(c,"updateBinValueFromMemory");
            if(!Boolean.TRUE.equals(call(t,"isStaticDataTable")))call(t,"calcCellRanges");
            Object view=optional(t,"getTableView");if(view!=null)call(view,"drawTable");
        }
    }
    private void restore(Object r,byte[] original)throws Exception{byte[] b=bytes(r);if(b.length!=original.length)throw new IllegalStateException("ROM size changed unexpectedly");System.arraycopy(original,0,b,0,b.length);refresh(r);if(!sha(bytes(r)).equals(sha(original)))throw new IllegalStateException("Rollback hash mismatch");}
    @SuppressWarnings("unchecked")
    private List<Map<String,Object>> executeChanges(Object r,List<Object> changes)throws Exception{
        if(changes.isEmpty()||changes.size()>MAX_CELLS)throw new IllegalArgumentException("Empty or oversized changeset");
        checkDeadline();preflightModel(r);LinkedHashMap<String,Object> ts=tableObjects(r);Set<String> seen=new HashSet<String>();List<Map<String,Object>> results=new ArrayList<Map<String,Object>>();
        for(Object ch:changes){checkDeadline();if(!(ch instanceof Map))throw new IllegalArgumentException("Change must be object");Map<String,Object> c=(Map<String,Object>)ch;
            exact(c,"table","row","column","expected_raw","value","tolerance","mode");String key=text(c.get("table"));Object t=ts.get(key);if(t==null)throw new IllegalArgumentException("Unknown table "+key);
            if(Boolean.TRUE.equals(call(t,"isStaticDataTable"))||Boolean.TRUE.equals(call(t,"isLocked")))throw new IllegalArgumentException("Static/locked table "+key);
            if(String.valueOf(call(t,"getName")).toLowerCase(Locale.ROOT).contains("checksum fix"))throw new IllegalArgumentException("Use dedicated checksum review, not ordinary cell writes");
            int row=integer(c.get("row")),col=integer(c.get("column"));Object[][] grid=cells(t);if(row<0||row>=grid.length||col<0||col>=grid[row].length)throw new IllegalArgumentException("Cell coordinate out of range");
            if(!seen.add(key+"/"+row+"/"+col))throw new IllegalArgumentException("Duplicate cell in proposal");Object cell=grid[row][col];if(cell==null)throw new IllegalArgumentException("Unpopulated cell");
            double before=number(call(cell,"getBinValue"));if(Double.compare(before,number(c.get("expected_raw")))!=0)throw new IllegalStateException("Cell changed since proposal: "+key);
            double v=number(c.get("value")),tol=number(c.get("tolerance"));if(tol<0)throw new IllegalArgumentException("Negative tolerance");String mode=text(c.get("mode"));
            if(mode.equals("real")){
                String s=Double.toString(v);Class<?> nu=Class.forName("com.romraider.util.NumberUtil",false,t.getClass().getClassLoader());Object separator=call(nu,"getSeperator");if(separator instanceof Character&&((Character)separator).charValue()==',')s=s.replace('.',',');
                call(cell,"setRealValue",s);
            }else if(mode.equals("raw"))call(cell,"setBinValue",Double.valueOf(v));else throw new IllegalArgumentException("Mode must be real or raw");
            double actual=number(call(cell,mode.equals("raw")?"getBinValue":"getRealValue"));
            if(Math.abs(actual-v)>tol)throw new IllegalStateException("Representable result/clamp exceeds tolerance: requested "+v+" got "+actual);
            results.add(map("table",key,"row",row,"column",col,"before_raw",before,"after_raw",call(cell,"getBinValue"),"requested",v,"achieved",actual,"mode",mode,"tolerance",tol));
        }
        // Modified numeric axes must remain finite and strictly monotonic. Do not infer a new map shape.
        Set<String> axes=new HashSet<String>();for(Map<String,Object> result:results){String key=text(result.get("table"));if(key.endsWith("::x")||key.endsWith("::y")||key.endsWith("::axis"))axes.add(key);}
        for(String key:axes){Object[][] axis=cells(ts.get(key));double previous=0;int direction=0,count=0;for(Object[] row:axis)for(Object cell:row){double v=number(call(cell,"getRealValue"));if(count++>0){int sign=Double.compare(v,previous);if(sign==0||(direction!=0&&sign!=direction))throw new IllegalStateException("Axis must remain strictly monotonic: "+key);direction=sign;}previous=v;}}
        refresh(r);return results;
    }
    private static List<Object> diff(byte[]a,byte[]b){List<Object>out=new ArrayList<Object>();for(int i=0;i<a.length;){if(a[i]==b[i]){i++;continue;}int start=i;while(i<a.length&&a[i]!=b[i])i++;out.add(map("start",start,"end_exclusive",i,"length",i-start));}return out;}
    private static final class Pending {String romId,beforeHash,modelHash,afterHash,reason;List<Object>changes;List<Map<String,Object>>result;long expires;Map<String,Object>committed;}
    private void saveAudit(String kind,Object data)throws Exception{Path p=work.resolve("rr_events.jsonl");Files.write(p,(Json.stringify(map("utc",Instant.now().toString(),"kind",kind,"data",data))+"\n").getBytes(StandardCharsets.UTF_8),StandardOpenOption.CREATE,StandardOpenOption.APPEND);}
    @SuppressWarnings("unchecked")
    public Object dispatch(String op,Map<String,Object> q)throws Exception{
        if(!SwingUtilities.isEventDispatchThread())throw new IllegalStateException("RomRaider model access must be on Swing EDT");
        if(op.equals("status")){exact(q);List<Object>out=new ArrayList<Object>();for(Object r:roms())out.add(info(r));return map("bridge_version","2.0.0","session",session,"apply_enabled",applyEnabled,"approval","local_dialog_each_changeset","roms",out);}
        if(op.equals("snapshot")){exact(q,"rom_id");return snapshot(rom(text(q.get("rom_id"))));}
        if(op.equals("table")){exact(q,"rom_id","table");Object r=rom(text(q.get("rom_id")));Object t=tableObjects(r).get(text(q.get("table")));if(t==null)throw new IllegalArgumentException("Table not found");return map("rom",info(r),"model_sha256",structureHash(r),"table",describe(text(q.get("table")),t,true));}
        if(op.equals("preview")){
            exact(q,"rom_id","expected_rom_sha256","expected_model_sha256","changes","reason","evidence");
            if(text(q.get("reason")).trim().isEmpty()||!(q.get("evidence") instanceof List)||((List<?>)q.get("evidence")).isEmpty())throw new IllegalArgumentException("Reason and evidence required");
            Object r=rom(text(q.get("rom_id")));String beforeHash=sha(bytes(r)),mh=structureHash(r);
            if(!beforeHash.equals(q.get("expected_rom_sha256"))||!mh.equals(q.get("expected_model_sha256")))throw new IllegalStateException("Stale ROM/model fingerprint");
            if(!(q.get("changes") instanceof List))throw new IllegalArgumentException("Changes must be array");
            Pending p=new Pending();p.reason=text(q.get("reason"));p.romId=id(r);p.beforeHash=beforeHash;p.modelHash=mh;p.changes=(List<Object>)q.get("changes");p.expires=System.nanoTime()+600000000000L;
            byte[]original=bytes(r).clone();List<Object>ranges;
            try{p.result=executeChanges(r,p.changes);p.afterHash=sha(bytes(r));ranges=diff(original,bytes(r));}finally{restore(r,original);}
            for(Iterator<Map.Entry<String,Pending>>it=pending.entrySet().iterator();it.hasNext();)if(it.next().getValue().expires<System.nanoTime())it.remove();
            if(pending.size()>=32)throw new IllegalStateException("Too many previews; let older previews expire");String pid=UUID.randomUUID().toString();pending.put(pid,p);
            Map<String,Object>result=map("preview_id",pid,"expires_seconds",600,"before_sha256",p.beforeHash,"after_sha256",p.afterHash,"changes",p.result,"binary_ranges",ranges,"reason",q.get("reason"),"evidence",q.get("evidence"),"rom_restored",true,"checksum_status","NOT_RECALCULATED_NOT_FLASH_READY");saveAudit("preview",result);return result;
        }
        if(op.equals("commit")){
            exact(q,"preview_id");if(!applyEnabled)throw new SecurityException("Restart reviewed editor launcher with -EnableEdits to apply; reads and previews are available");Pending p=pending.get(text(q.get("preview_id")));if(p==null)throw new IllegalArgumentException("Unknown preview");if(p.committed!=null)return p.committed;if(p.expires<System.nanoTime())throw new IllegalStateException("Preview expired");Object r=rom(p.romId);
            if(!sha(bytes(r)).equals(p.beforeHash)||!structureHash(r).equals(p.modelHash))throw new IllegalStateException("Stale ROM/model; regenerate preview");
            StringBuilder summary=new StringBuilder();int shown=0;for(Map<String,Object> c:p.result){if(shown++>=12){summary.append("\n... additional cells are listed in the preview report.");break;}summary.append("\n").append(c.get("table")).append(" [").append(c.get("row")).append(",").append(c.get("column")).append("] raw ").append(c.get("before_raw")).append(" -> ").append(c.get("after_raw")).append("; achieved ").append(c.get("achieved"));}
            if(!approval.approve("Apply "+p.changes.size()+" reviewed cells to the OPEN RomRaider model?\nReason: "+p.reason+summary+"\nPreview: "+q.get("preview_id")+"\nBefore SHA256: "+p.beforeHash+"\nExpected after: "+p.afterHash+"\nNo ECU write. No disk overwrite. Checksum review remains required."))throw new SecurityException("Operator cancelled");
            checkDeadline();if(p.expires<System.nanoTime())throw new IllegalStateException("Preview expired during approval");if(!sha(bytes(r)).equals(p.beforeHash)||!structureHash(r).equals(p.modelHash))throw new IllegalStateException("Model changed during approval");
            byte[] original=bytes(r).clone();
            try{executeChanges(r,p.changes);if(!sha(bytes(r)).equals(p.afterHash))throw new IllegalStateException("Commit differs from preview");Map<String,Object> committed=map("preview_id",q.get("preview_id"),"applied_to_editor",true,"binary_sha256",sha(bytes(r)),"disk_saved",false,"ecu_written",false,"checksum_status","NOT_RECALCULATED_NOT_FLASH_READY");saveAudit("commit",committed);p.committed=committed;return committed;}catch(Exception e){restore(r,original);throw e;}
        }
        if(op.equals("export_model")){
            exact(q,"rom_id","expected_rom_sha256");Object r=rom(text(q.get("rom_id")));byte[]b=bytes(r).clone();String h=sha(b);if(!h.equals(q.get("expected_rom_sha256")))throw new IllegalStateException("Stale ROM hash");Path path=work.resolve(h+".NOT_FLASH_READY.bin");if(!Files.exists(path))Files.write(path,b,StandardOpenOption.CREATE_NEW);else if(!sha(Files.readAllBytes(path)).equals(h))throw new IllegalStateException("Existing export hash conflict");Map<String,Object>out=map("path",path.toString(),"sha256",h,"size_bytes",b.length,"checksum_status","NOT_RECALCULATED_NOT_FLASH_READY","ecu_written",false);saveAudit("export",out);return out;
        }
        throw new IllegalArgumentException("Unknown operation");
    }
}
