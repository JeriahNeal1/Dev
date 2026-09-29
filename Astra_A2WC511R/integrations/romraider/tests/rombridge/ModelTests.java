package rombridge;
import java.nio.file.*;import java.util.*;import javax.swing.SwingUtilities;

/** Source-contract test doubles, NOT the real RomRaider binary. */
public final class ModelTests {
 static int checks=0;
 static void check(boolean x,String message){if(!x)throw new AssertionError(message);checks++;}
 public static final class Scale {public String getCategory(){return "Default";}public String getUnits(){return "unit";}public String getExpression(){return "x/2";}public String getByteExpression(){return "x*2";}public String getFormat(){return "0.0";}}
 public static class Table {
  String name;int addr;Rom rom;boolean locked,stat;DataCell[] data;Object presetManager=null;Scale scale=new Scale();
  Table(Rom r,String n,int a,int count){rom=r;name=n;addr=a;data=new DataCell[count];for(int i=0;i<count;i++)data[i]=new DataCell(this,i);}
  public String getName(){return name;}public String getType(){return "TABLE_1D";}public String getCategory(){return "Testing";}public String getDescription(){return "Test model";}
  public int getStorageAddress(){return addr;}public int getRamOffset(){return 0;}public int getStorageType(){return 1;}public String getEndian(){return "BIG";}public boolean isSignedData(){return false;}public int getBitMask(){return 0;}public String getDataLayout(){return "DEFAULT";}public boolean isStaticDataTable(){return stat;}public boolean isLocked(){return locked;}public int getUserLevel(){return 1;}public String getLogParam(){return "test";}public Scale getCurrentScale(){return scale;}public List<Scale>getScales(){return Arrays.asList(scale);}public DataCell[]getData(){return data;}public void calcCellRanges(){}public Object getTableView(){return null;}
 }
 public static final class Table3D extends Table {
  Table x,y;DataCell[][] grid;
  Table3D(Rom r,String n,int addr){super(r,n,addr,4);grid=new DataCell[][]{{data[0],data[2]},{data[1],data[3]}};x=new Table(r,"X",200,2);y=new Table(r,"Y",210,2);}
  public DataCell[][]get3dData(){return grid;}public Table getXAxis(){return x;}public Table getYAxis(){return y;}public String getType(){return "TABLE_3D";}public boolean getSwapXY(){return false;}public boolean getFlipX(){return false;}public boolean getFlipY(){return false;}public int getSkipCells(){return 0;}
 }
 public static final class DataCell {
  Table table;int index;double original;DataCell(Table t,int i){table=t;index=i;original=getBinValue();}
  public double getBinValue(){return table.rom.bin[table.addr+index]&255;}public double getRealValue(){return getBinValue()/2;}public int getIndexInTable(){return index;}public int getBitMask(){return 0;}public double getOriginalValue(){return original;}public double getMinAllowedBin(){return 0;}public double getMaxAllowedBin(){return 255;}
  public void setRealValue(String s){setBinValue(Math.round(Double.parseDouble(s)*2));}
  public void setBinValue(double x){if(table.locked)return;table.rom.bin[table.addr+index]=(byte)Math.min(255,Math.max(0,x));}
  public void updateBinValueFromMemory(){}public String getStaticText(){return "1";}
 }
 public static final class Rom {
  byte[]bin=new byte[1024];List<Table>tables=new ArrayList<Table>();
  public byte[]getBinary(){return bin;}public List<Table>getTables(){return tables;}public String getFileName(){return "scratch.bin";}public String getRomIDString(){return "A2WC511R";}public String getFullFileName(){return "scratch.bin";}public Object getDefinitionPath(){return null;}public Object getDocument(){return null;}public List<String>getFaultyTables(){return Collections.emptyList();}
 }
 public static final class Editor {Rom r;Editor(Rom r){this.r=r;}public List<Rom>getImages(){return Arrays.asList(r);}}
 static Map<String,Object>change(String t,int y,int x,double old,double val,double tol){return RomAccess.map("table",t,"row",y,"column",x,"expected_raw",old,"value",val,"tolerance",tol,"mode","real");}
 @SuppressWarnings("unchecked") static void run()throws Exception{
  Rom r=new Rom();r.bin[100]=10;r.bin[101]=20;Table numeric=new Table(r,"Numeric",100,2);r.tables.add(numeric);r.tables.add(new Table3D(r,"Surface",110));final Editor ed=new Editor(r);
  RomAccess a=new RomAccess(()->ed,msg->true,true,Files.createTempDirectory("rrmodeltest"));
  Map<String,Object>status=(Map<String,Object>)a.dispatch("status",RomAccess.map());check(((List<?>)status.get("roms")).size()==1,"ROM catalog");
  Map<String,Object>s=(Map<String,Object>)a.dispatch("snapshot",RomAccess.map("rom_id","rom_1"));check(((List<?>)s.get("tables")).size()==4,"numeric,3D and both axes captured");
  String initial=RomAccess.sha(r.bin);
  Map<String,Object>q=RomAccess.map("rom_id","rom_1","expected_rom_sha256",initial,"expected_model_sha256",s.get("model_sha256"),"changes",Arrays.asList(change("Numeric",0,0,10,5.5,0)),"reason","test","evidence",Arrays.asList("synthetic"));
  Map<String,Object>p=(Map<String,Object>)a.dispatch("preview",q);check(RomAccess.sha(r.bin).equals(initial),"preview rollback");check(!p.get("after_sha256").equals(initial),"preview real byte diff");
  Map<String,Object>comm=(Map<String,Object>)a.dispatch("commit",RomAccess.map("preview_id",p.get("preview_id")));check((r.bin[100]&255)==11,"native quantization/application");check(a.dispatch("commit",RomAccess.map("preview_id",p.get("preview_id")))==comm,"commit idempotency");
  boolean rejected=false;try{a.dispatch("preview",q);}catch(IllegalStateException e){rejected=true;}check(rejected,"stale hash rejected");
  s=(Map<String,Object>)a.dispatch("snapshot",RomAccess.map("rom_id","rom_1"));q.put("expected_rom_sha256",RomAccess.sha(r.bin));q.put("expected_model_sha256",s.get("model_sha256"));String before=RomAccess.sha(r.bin);
  q.put("changes",Arrays.asList(change("Numeric",0,0,11,6,0),change("Numeric",0,1,20,999,0)));
  rejected=false;try{a.dispatch("preview",q);}catch(IllegalStateException e){rejected=true;}check(rejected&&RomAccess.sha(r.bin).equals(before),"whole transaction restored on clamp/failure");
  q.put("changes",Arrays.asList(change("Numeric",0,0,11,5.6,0.01)));rejected=false;try{a.dispatch("preview",q);}catch(IllegalStateException e){rejected=true;}check(rejected&&RomAccess.sha(r.bin).equals(before),"quantization tolerance failure restores");
  q.put("changes",Arrays.asList(change("Surface",1,1,0,2.5,0)));p=(Map<String,Object>)a.dispatch("preview",q);a.dispatch("commit",RomAccess.map("preview_id",p.get("preview_id")));check((r.bin[113]&255)==5,"3D y/x coordinates");
  s=(Map<String,Object>)a.dispatch("snapshot",RomAccess.map("rom_id","rom_1"));q.put("expected_rom_sha256",RomAccess.sha(r.bin));q.put("expected_model_sha256",s.get("model_sha256"));q.put("changes",Arrays.asList(change("Surface::x",0,1,0,3,0)));p=(Map<String,Object>)a.dispatch("preview",q);check(RomAccess.sha(r.bin).equals(q.get("expected_rom_sha256")),"axis preview restored");
  Object ex=a.dispatch("export_model",RomAccess.map("rom_id","rom_1","expected_rom_sha256",RomAccess.sha(r.bin)));check(ex instanceof Map,"content addressed export");
  numeric.locked=true;s=(Map<String,Object>)a.dispatch("snapshot",RomAccess.map("rom_id","rom_1"));q.put("expected_model_sha256",s.get("model_sha256"));q.put("changes",Arrays.asList(change("Numeric",0,0,11,8,0)));rejected=false;try{a.dispatch("preview",q);}catch(IllegalArgumentException e){rejected=true;}check(rejected,"locked table rejected");
  numeric.locked=false;RomAccess readonly=new RomAccess(()->ed,msg->true,false,Files.createTempDirectory("rrreadonly"));rejected=false;try{readonly.dispatch("commit",RomAccess.map("preview_id","none"));}catch(SecurityException e){rejected=true;}check(rejected,"read-only apply block");
  RomAccess no=new RomAccess(()->ed,msg->false,true,Files.createTempDirectory("rrcancel"));s=(Map<String,Object>)no.dispatch("snapshot",RomAccess.map("rom_id","rom_1"));q.put("expected_model_sha256",s.get("model_sha256"));p=(Map<String,Object>)no.dispatch("preview",q);rejected=false;before=RomAccess.sha(r.bin);try{no.dispatch("commit",RomAccess.map("preview_id",p.get("preview_id")));}catch(SecurityException e){rejected=true;}check(rejected&&RomAccess.sha(r.bin).equals(before),"operator cancel");
  RomAccess late=new RomAccess(()->ed,msg->{try{Thread.sleep(35);}catch(Exception e){}return true;},true,Files.createTempDirectory("rrlate"));
  s=(Map<String,Object>)late.dispatch("snapshot",RomAccess.map("rom_id","rom_1"));q.put("expected_model_sha256",s.get("model_sha256"));p=(Map<String,Object>)late.dispatch("preview",q);
  rejected=false;before=RomAccess.sha(r.bin);try{late.dispatchBefore("commit",RomAccess.map("preview_id",p.get("preview_id")),System.nanoTime()+10000000L);}catch(IllegalStateException e){rejected=true;}check(rejected&&RomAccess.sha(r.bin).equals(before),"expired approval cannot apply later");
  rejected=false;try{late.dispatchBefore("status",RomAccess.map(),System.nanoTime()-1);}catch(IllegalStateException e){rejected=true;}check(rejected,"expired queued request blocked");
  for(String bad:new String[]{"{\"a\":1,\"a\":2}","1e9999","{\"a\":NaN}","[01]"}){rejected=false;try{Json.parse(bad);}catch(IllegalArgumentException e){rejected=true;}check(rejected,"strict JSON rejects "+bad);}
  check(Json.stringify(Json.parse("{\"test\":[1,true,null,\"x\\n\"]}")).contains("true"),"JSON roundtrip");
 }
 public static void main(String[]args)throws Exception{final Exception[]error={null};SwingUtilities.invokeAndWait(()->{try{run();}catch(Exception e){error[0]=e;}});if(error[0]!=null)throw error[0];System.out.println("PASS "+checks+" Java model/transaction assertions (test doubles; not live RomRaider)");}
}
