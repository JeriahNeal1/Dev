package a2wc.virtualrr;
import java.nio.file.*;import java.util.*;import java.io.*;import java.util.concurrent.*;
import com.romraider.io.connection.*;
import com.romraider.io.protocol.ssm.iso9141.SSMProtocol;
import com.romraider.io.j2534.api.J2534TransportFactory;
import com.romraider.io.serial.connection.SerialConnectionManager;
import com.romraider.logger.ecu.comms.manager.*;
import com.romraider.logger.ecu.definition.Module;
import rombridge.Json;

/** Prepared collector: all validation invokes virtual mode only in development.
 * Physical mode is an explicit later user action; no fallback, RAM kernel,
 * reset, clearLine, write command, serial break or active test is permitted.
 */
public final class ReadOnlySSMCollector {
 public static final int[] RAM={0xff4c75,0xff4c8d,0xff4ca1,0xff4c50,0xff4bc1,0xff4bc2};
 static final String AUTH="I_AUTHORIZE_READ_ONLY_SSM";
 static final Module ECU=new Module("ECU",new byte[]{0x10},"Read only acquisition",new byte[]{(byte)0xf0},false);
 static int u(byte b){return b&255;}
 static byte[] address(int n){return new byte[]{(byte)(n>>>16),(byte)(n>>>8),(byte)n};}
 static int addr(byte[] b,int i){return u(b[i])*65536+u(b[i+1])*256+u(b[i+2]);}
 static boolean ram(int a){for(int p:RAM)if(a==p)return true;return false;}
 public static final class ReadOnlyGate implements ConnectionManager {
  final ConnectionManager underlying;public int requests=0;
  public ReadOnlyGate(ConnectionManager manager){underlying=Objects.requireNonNull(manager);}
  public static void validate(byte[] q){if(q==null||q.length<6||u(q[0])!=0x80||u(q[1])!=0x10||u(q[2])!=0xf0||u(q[3])!=q.length-5)throw new SecurityException("Invalid SSM frame");int sum=0;for(int i=0;i<q.length-1;i++)sum+=u(q[i]);if((sum&255)!=u(q[q.length-1]))throw new SecurityException("Invalid SSM checksum");int code=u(q[4]);
   if(code==0xbf&&q.length==6)return;
   if(code==0xa0&&q.length==11&&q[5]==0){int start=addr(q,6),count=u(q[9])+1;if(count<=240&&(long)start+count<=1048576)return;}
   if(code==0xa8&&q.length>=10&&(q.length-7)%3==0&&q[5]==0){for(int i=6;i<q.length-1;i+=3)if(!ram(addr(q,i)))throw new SecurityException("Only six reviewed raw RAM bytes permitted");return;}
   throw new SecurityException("Only BF, bounded A0 ROM reads, and six-byte A8 reads permitted");
  }
  public void open(byte[] a,byte[] b){throw new SecurityException("No physical initialization command allowed");}
  public byte[] send(byte[] q){validate(q);requests++;return underlying.send(q);}
  public void send(byte[] q,byte[] r,PollingState p){validate(q);if(p.getCurrentState()!=PollingState.State.STATE_0||p.getLastState()!=PollingState.State.STATE_0||p.isFastPoll())throw new SecurityException("Single read with echo only; no clearLine or cached fast response");requests++;underlying.send(q,r,p);}
  public void clearLine(){throw new SecurityException("No break or line-clearing transmission allowed");}
  public void close(){underlying.close();}
 }
 static byte[] read(SSMProtocol protocol,ReadOnlyGate gate,PollingState state,byte[] q,int bytes,int code){byte[] wire=new byte[q.length+bytes+6];gate.send(q,wire,state);if(!Arrays.equals(Arrays.copyOf(wire,q.length),q))throw new IllegalStateException("Missing/exact request echo mismatch; abort without fallback");byte[] reply=protocol.preprocessResponse(q,wire,state);if(u(reply[4])!=code)throw new IllegalStateException("ECU rejected/unexpected read command");byte[] data=protocol.parseResponseData(reply);if(data.length!=bytes)throw new IllegalStateException("Read length mismatch");return data;}
 static void write(Path p,Object o)throws Exception{Files.write(p,Json.stringify(o).getBytes("UTF-8"),StandardOpenOption.CREATE_NEW);}
 static byte[] initialize(ReadOnlyGate gate,byte[] q,long timeoutMs)throws Exception{ExecutorService executor=Executors.newSingleThreadExecutor(r->{Thread t=new Thread(r,"ReadOnlySSMInit");t.setDaemon(true);return t;});Future<byte[]> task=executor.submit(()->gate.send(q));try{return task.get(timeoutMs,TimeUnit.MILLISECONDS);}finally{task.cancel(true);executor.shutdownNow();}}
 static void sample(SSMProtocol protocol,ReadOnlyGate gate,PollingState state,ConnectionManager manager,boolean virtual,byte[][] addresses,List<Object> samples,long started,String phase,int pass,int offset){if(virtual)((VirtualSSMConnectionManager)manager).setSample(samples.size()%((VirtualSSMConnectionManager)manager).sampleCount());byte[] values=read(protocol,gate,state,protocol.constructReadAddressRequest(ECU,addresses),RAM.length,0xe8);Map<String,Object> row=NativeLoggerAcceptance.map("phase",phase,"sample_index",samples.size(),"pass",pass,"ROM_offset",offset,"host_utc",java.time.Instant.now().toString(),"host_elapsed_ms",(System.nanoTime()-started)/1000000);for(int i=0;i<RAM.length;i++)row.put(String.format("FFFF%04X",RAM[i]&65535),u(values[i]));samples.add(row);}
 public static void main(String[] args)throws Exception{
  if(args.length<2)throw new IllegalArgumentException("virtual OUT SNAPSHOT SHA ROM SHA | physical-j2534 OUT DLL SHA "+AUTH+" | physical-serial OUT COMx "+AUTH);
  String mode=args[0];boolean virtual=mode.equals("virtual");if(!virtual&&!mode.equals("physical-j2534")&&!mode.equals("physical-serial"))throw new SecurityException("Explicit transport mode required");
  Path out=Paths.get(args[1]).toAbsolutePath().normalize();if(Files.exists(out))throw new IllegalArgumentException("Output directory must be new");
  Files.createDirectories(out);
  SSMProtocol protocol=new SSMProtocol();ConnectionProperties props=protocol.getDefaultConnectionProperties();ConnectionManager manager=null;ReadOnlyGate gate=null;long started=System.nanoTime();List<Object> samples=new ArrayList<>();PollingState state=new PollingStateImpl();
  Map<String,Object> result=NativeLoggerAcceptance.map("classification",virtual?"VIRTUAL_SOFTWARE_SCENARIO_NOT_VEHICLE_TELEMETRY":"PHYSICAL_READ_ONLY_SSM_ACQUISITION_NOT_FLASH_READY","transport",mode,"stock_A0_support","UNPROVEN_UNTIL_THIS_PHYSICAL_RUN","requested_commands",Arrays.asList("BF ECU identification","A0 ROM ranges only","A8 six exact raw RAM addresses"),"no_kernel_upload",true,"no_reset_or_write_or_break",true,"java",System.getProperty("java.version"),"java_arch",System.getProperty("sun.arch.data.model"));
  try{
  if(virtual){if(args.length!=6)throw new IllegalArgumentException("Virtual requires all input identities");manager=new VirtualSSMConnectionManager(Paths.get(args[2]),args[3],Paths.get(args[4]),args[5]);result.put("virtual_snapshot_sha256",args[3]);result.put("virtual_ROM_sha256",args[5]);}
  else {if(!AUTH.equals(args[args.length-1]))throw new SecurityException("Explicit future human read-only invocation required");
   if(mode.equals("physical-j2534")){if(args.length!=5)throw new IllegalArgumentException("Exact DLL and hash required");Path dll=Paths.get(args[2]).toRealPath();byte[] image=Files.readAllBytes(dll);String h=VirtualSSMConnectionManager.sha(image);if(!h.equals(args[3]))throw new SecurityException("Reviewed provider hash differs");int pe=u(image[0x3c])|(u(image[0x3d])<<8)|(u(image[0x3e])<<16)|(u(image[0x3f])<<24);int machine=u(image[pe+4])|(u(image[pe+5])<<8);if(machine!=0x14c||!"32".equals(System.getProperty("sun.arch.data.model")))throw new SecurityException("Reviewed OpenPort provider requires 32-bit JVM");result.put("provider_path",dll.toString());result.put("provider_sha256",h);manager=J2534TransportFactory.getManager("ISO9141",props,dll.toString());}
   else {if(args.length!=4||!args[2].matches("COM[1-9][0-9]*"))throw new SecurityException("Explicit existing COM port required; OpenPort J2534 is not a COM port");result.put("port",args[2]);manager=new SerialConnectionManager(args[2],props);}
  }
  gate=new ReadOnlyGate(manager);
   byte[] initQ=protocol.constructEcuInitRequest(ECU),init=protocol.preprocessResponse(initQ,initialize(gate,initQ,10000),state);protocol.checkValidEcuInitResponse(init);String ecuId=protocol.parseEcuInitResponse(init).getEcuId();if(!ecuId.equals("2F12515306"))throw new IllegalStateException("Unexpected ECUID "+ecuId);result.put("ecuid",ecuId);
   byte[] pilot=read(protocol,gate,state,protocol.constructReadMemoryRequest(ECU,address(0x2000),8),8,0xe0);if(!Arrays.equals(pilot,"A2WC511R".getBytes("US-ASCII")))throw new IllegalStateException("Pilot CALID mismatch");result.put("calid","A2WC511R");
   byte[][] ramAddresses=new byte[RAM.length][];for(int i=0;i<RAM.length;i++)ramAddresses[i]=address(RAM[i]);
   for(int burst=0;burst<60;burst++)sample(protocol,gate,state,manager,virtual,ramAddresses,samples,started,"initial_burst",0,-1);
   List<String> hashes=new ArrayList<>();result.put("rom_hashes",hashes);for(int pass=0;pass<2;pass++){byte[] rom=new byte[1048576];int block=0;for(int offset=0;offset<rom.length;offset+=240){result.put("read_pass",pass+1);result.put("read_request_offset",offset);int count=Math.min(240,rom.length-offset);byte[] data=read(protocol,gate,state,protocol.constructReadMemoryRequest(ECU,address(offset),count),count,0xe0);System.arraycopy(data,0,rom,offset,count);
     if(block++%64==0||offset+count==rom.length)sample(protocol,gate,state,manager,virtual,ramAddresses,samples,started,"ROM_read",pass+1,offset);
    }String h=VirtualSSMConnectionManager.sha(rom);hashes.add(h);Files.write(out.resolve("pass"+(pass+1)+".ACQUIRED.NOT_FLASH_READY.bin"),rom,StandardOpenOption.CREATE_NEW);if(!Arrays.equals(Arrays.copyOfRange(rom,0x2000,0x2008),pilot))throw new IllegalStateException("Full ROM CALID disagrees with verified pilot");if(pass==1&&!hashes.get(0).equals(h))throw new IllegalStateException("Two ROM reads differ; no current-image attestation");}
   for(int burst=0;burst<60;burst++)sample(protocol,gate,state,manager,virtual,ramAddresses,samples,started,"final_burst",0,-1);
   result.put("status","PASS_READ_ACQUISITION_ONLY");result.put("rom_hashes",hashes);result.put("two_full_reads_identical",true);
  }catch(Exception failure){result.put("status","BLOCKED_ABORTED_NO_FALLBACK");result.put("failure",failure.toString());throw failure;}
  finally{Exception closeFailure=null;try{if(manager!=null)manager.close();}catch(Exception e){closeFailure=e;result.put("cleanup_failure",e.toString());result.put("status","BLOCKED_ABORTED_NO_FALLBACK");}result.put("requests",gate==null?0:gate.requests);result.put("elapsed_ms",(System.nanoTime()-started)/1000000);write(out.resolve("raw_six_channel_samples.json"),samples);write(out.resolve("acquisition_result.json"),result);if(closeFailure!=null)throw closeFailure;}
  System.out.println(Json.stringify(result));
 }
}
