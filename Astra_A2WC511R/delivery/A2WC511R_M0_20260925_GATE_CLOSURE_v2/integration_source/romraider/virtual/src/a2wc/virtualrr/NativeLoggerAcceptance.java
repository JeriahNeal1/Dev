package a2wc.virtualrr;
import java.nio.file.*;import java.util.*;
import com.romraider.util.SettingsManager;
import com.romraider.logger.ecu.comms.io.connection.SSMLoggerConnection;
import com.romraider.logger.ecu.comms.query.*;
import com.romraider.logger.ecu.comms.manager.*;
import com.romraider.logger.ecu.definition.*;
import com.romraider.logger.ecu.definition.Module;
import com.romraider.io.protocol.ssm.iso9141.SSMProtocol;
import rombridge.Json;

/** Actual installed definition loader, conversions, query deduplication, SSM
 * encoder, response validator and logger connection; only endpoint is virtual. */
public final class NativeLoggerAcceptance {
 static Map<String,Object> map(Object... a){Map<String,Object> m=new LinkedHashMap<>();for(int i=0;i<a.length;i+=2)m.put((String)a[i],a[i+1]);return m;}
 static int checks=0;
 static void check(boolean ok,String what){if(!ok)throw new AssertionError(what);checks++;}
 static void reject(Runnable fn,String what){try{fn.run();}catch(RuntimeException good){checks++;return;}throw new AssertionError("Accepted forbidden "+what);}
 static void write(Path p,Object o)throws Exception{Files.write(p,Json.stringify(o).getBytes("UTF-8"));}
 static Map<String,Object> definition(EcuParameter p){return map("id",p.getId(),"name",p.getName(),"addresses",Arrays.asList(p.getAddress().getAddresses()),"expression",p.getSelectedConvertor().getExpression(),"format",p.getSelectedConvertor().getFormat(),"units",p.getSelectedConvertor().getUnits());}
 public static void main(String[] args)throws Exception{
  Path out=Paths.get(args[0]);Files.createDirectories(out);SettingsManager.getSettings().setLoggerProtocol("SSM");SettingsManager.getSettings().setTransportProtocol("ISO9141");
  VirtualSSMConnectionManager backend=new VirtualSSMConnectionManager(Paths.get(args[1]),args[2],Paths.get(args[3]),args[4]);
  Module ecu=new Module("ECU",new byte[]{0x10},"Virtual software only",new byte[]{(byte)0xf0},false);SSMLoggerConnection nativeConnection=new SSMLoggerConnection(backend);
  EcuInit[] init={null};nativeConnection.ecuInit(v->init[0]=v,ecu);check(init[0]!=null&&init[0].getEcuId().equals("2F12515306"),"native BF parse");
  EcuDataLoaderImpl stock=new EcuDataLoaderImpl();stock.loadConfigFromXml(args[5],"SSM","S13",init[0]);EcuDataLoaderImpl merged=new EcuDataLoaderImpl();merged.loadConfigFromXml(args[6],"SSM","S13",init[0]);
  Map<String,EcuParameter> all=new LinkedHashMap<>();for(EcuParameter p:merged.getEcuParameters())all.put(p.getId(),p);for(EcuParameter p:stock.getEcuParameters())check(Json.stringify(definition(p)).equals(Json.stringify(definition(all.get(p.getId())))),"unchanged existing definition "+p.getId());
  List<EcuQuery> queries=new ArrayList<>();List<Object> definitions=new ArrayList<>();int m0count=0,stockcount=0;
  for(EcuParameter p:merged.getEcuParameters()){
   boolean m0=p.getId().matches("E91[01][0-9]");boolean historical=p.getId().startsWith("E_A2WC511R_");if(!m0&&!historical)continue;
   try{for(String address:p.getAddress().getAddresses())backend.readByte(Integer.parseInt(address.replace("0x",""),16));}catch(IllegalArgumentException unsupported){if(m0)throw unsupported;continue;}
   if(m0)m0count++;else stockcount++;queries.add(new EcuQueryImpl(p));definitions.add(definition(p));
  }
  check(m0count==17,"all final05 M0 definitions loaded");check(stockcount>=3,"unchanged historical OEM channels loaded");write(out.resolve("native_loaded_definitions.json"),definitions);
  List<Object> rows=new ArrayList<>();PollingState state=new PollingStateImpl();for(int i=0;i<backend.sampleCount();i++){
   backend.setSample(i);nativeConnection.sendAddressReads(queries,ecu,state);Map<String,Object> values=new LinkedHashMap<>();for(EcuQuery q:queries){long raw=0;for(String a:q.getAddresses())raw=(raw<<8)|backend.readByte(Integer.parseInt(a.replace("0x",""),16));check(q.getResponse()==raw,"native conversion equals compiled RAM: "+q.getLoggerData().getId());values.put(q.getLoggerData().getId(),map("value",q.getResponse(),"display",q.getLoggerData().getSelectedConvertor().format(q.getResponse())));}rows.add(map("sample_id",backend.sample().get("sample_id"),"virtual_time_ms",backend.sample().get("virtual_time_ms"),"values",values));
  }
  write(out.resolve("native_virtual_samples.json"),map("classification","VIRTUAL_SOFTWARE_SCENARIO_NOT_VEHICLE_TELEMETRY","samples",rows));
  for(EcuQuery q:queries)if(q.getLoggerData().getId().matches("E91[01][0-9]")){int n=q.getAddresses().length;byte[] max=new byte[n];Arrays.fill(max,(byte)0xff);q.setResponse(max);check(q.getResponse()==(n==4?4294967295.0:255.0),"unsigned M0 maximum "+q.getLoggerData().getId());if(n==4){q.setResponse(new byte[]{1,2,3,4});check(q.getResponse()==16909060.0,"big-endian M0 word "+q.getLoggerData().getId());}}
  // Exercise fast-poll response without request echo using the native state path.
  state.setCurrentState(PollingState.State.STATE_1);state.setFastPoll(true);nativeConnection.sendAddressReads(queries,ecu,state);checks++;state.setCurrentState(PollingState.State.STATE_0);state.setFastPoll(false);
  SSMProtocol protocol=new SSMProtocol();byte[] expected=Files.readAllBytes(Paths.get(args[3]));byte[] dump=new byte[expected.length];for(int offset=0;offset<dump.length;offset+=128){byte[] addr={(byte)(offset>>>16),(byte)(offset>>>8),(byte)offset};byte[] req=protocol.constructReadMemoryRequest(ecu,addr,128);byte[] response=backend.send(req);byte[] data=protocol.parseResponseData(protocol.preprocessResponse(req,response,state));check(data.length==128,"native A0 block length");System.arraycopy(data,0,dump,offset,128);}check(Arrays.equals(dump,expected),"native A0 entire immutable ROM exactly reconstructed");
  reject(()->backend.send(protocol.constructWriteAddressRequest(ecu,new byte[]{0,0,0x60},(byte)0x40)),"B8 reset");reject(()->backend.send(protocol.constructWriteMemoryRequest(ecu,new byte[]{(byte)0xff,0x74,0},new byte[]{1})),"B0 RAM write");reject(()->backend.readByte(0xff7000),"unknown RAM");reject(()->backend.setSample(backend.sampleCount()),"unknown sample");
  byte[] malformed=protocol.constructReadMemoryRequest(ecu,new byte[]{0,0x20,0},8);malformed[malformed.length-1]^=1;reject(()->backend.send(malformed),"bad checksum");
  byte[] badModule=protocol.constructReadMemoryRequest(ecu,new byte[]{0,0x20,0},8);badModule[1]=0x18;reject(()->backend.send(badModule),"other module");
  byte[] invalidResponse=VirtualSSMConnectionManager.frame(0xe8,new byte[]{1});invalidResponse[invalidResponse.length-1]^=1;reject(()->protocol.parseResponseData(invalidResponse),"native malformed response");
  final int[] reached={0};com.romraider.io.connection.ConnectionManager inert=new com.romraider.io.connection.ConnectionManager(){public void open(byte[] a,byte[] b){reached[0]++;}public byte[] send(byte[] q){reached[0]++;return new byte[0];}public void send(byte[] q,byte[] r,PollingState p){reached[0]++;}public void clearLine(){reached[0]++;}public void close(){}};
  ReadOnlySSMCollector.ReadOnlyGate guard=new ReadOnlySSMCollector.ReadOnlyGate(inert);
  reject(()->guard.send(protocol.constructWriteMemoryRequest(ecu,new byte[]{(byte)0xff,0x74,0},new byte[]{1})),"collector B0 blocked before transport");
  reject(()->guard.send(protocol.constructWriteAddressRequest(ecu,new byte[]{0,0,0x60},(byte)0x40)),"collector reset blocked before transport");
  reject(()->guard.send(protocol.constructReadMemoryRequest(ecu,new byte[]{0x0f,(byte)0xff,(byte)0xff},2)),"collector beyond ROM");
  reject(()->guard.send(protocol.constructReadAddressRequest(ecu,new byte[][]{{(byte)0xff,0x4b,(byte)0xc3}})),"collector unreviewed RAM");
  reject(()->guard.clearLine(),"collector break");reject(()->guard.open(new byte[0],new byte[0]),"collector custom initialize");
  check(reached[0]==0,"forbidden requests never reached underlying transport");
  ReadOnlySSMCollector.ReadOnlyGate.validate(protocol.constructReadMemoryRequest(ecu,new byte[]{0,0x20,0},240));checks++;
  write(out.resolve("wire_examples.json"),backend.wireAudit);backend.close();reject(()->backend.readByte(0x2000),"closed endpoint");
  write(out.resolve("result.json"),map("status","PASS","checks",checks,"native_romraider","installed1.1.0","snapshot_sha256",backend.snapshotHash,"rom_sha256",backend.romHash,"m0_fields",m0count,"unchanged_historical_fields",stockcount,"samples",rows.size(),"requests",backend.requestCount,"native_A0_full_ROM_sha256",VirtualSSMConnectionManager.sha(dump),"device_connections",0,"global_provider_changes",0,"limitations","Immutable software snapshots. BF availability bytes explicitly virtual/zero. No physical transport, peripheral timing, OEM A0 acceptance or full GUI logger integration proven."));System.out.println("PASS "+checks+" checks, "+queries.size()+" native channels, "+rows.size()+" compiled samples");
 }
}
