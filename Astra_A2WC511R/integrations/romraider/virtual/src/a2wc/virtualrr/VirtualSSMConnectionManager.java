package a2wc.virtualrr;

import java.nio.file.*;
import java.util.*;
import java.security.MessageDigest;
import com.romraider.io.connection.ConnectionManager;
import com.romraider.logger.ecu.comms.manager.PollingState;
import rombridge.Json;

/** Offline snapshot transport. No serial, socket, J2534, device, or write fallback.
 * SSM framing is exercised against installed RomRaider; this class is only the
 * virtual endpoint, never a claim that the OEM accepts these address ranges.
 */
public final class VirtualSSMConnectionManager implements ConnectionManager {
 private final List<Map<String,Object>> samples;
 private final byte[] rom;
 private int index=0;
 private boolean closed=false;
 public int requestCount=0;
 public final String snapshotHash,romHash;
 public final List<Map<String,Object>> wireAudit=new ArrayList<>();
 public static String sha(byte[] b)throws Exception {StringBuilder s=new StringBuilder();for(byte v:MessageDigest.getInstance("SHA-256").digest(b))s.append(String.format("%02x",v&255));return s.toString();}
 @SuppressWarnings("unchecked") public VirtualSSMConnectionManager(Path snapshots,String expectedSnapshotHash,Path romFile,String expectedRomHash)throws Exception {
  byte[] data=Files.readAllBytes(snapshots);snapshotHash=sha(data);if(!snapshotHash.equals(expectedSnapshotHash))throw new SecurityException("Snapshot hash mismatch");
  Map<String,Object> root=(Map<String,Object>)Json.parse(new String(data,"UTF-8"));
  if(!"VIRTUAL_SOFTWARE_SCENARIO_NOT_VEHICLE_TELEMETRY".equals(root.get("classification"))||!"2F12515306".equals(root.get("ecuid")))throw new SecurityException("Wrong virtual scenario identity");
  samples=(List<Map<String,Object>>)root.get("snapshots");if(samples==null||samples.isEmpty())throw new IllegalArgumentException("No immutable samples");
  rom=Files.readAllBytes(romFile);romHash=sha(rom);if(rom.length!=1048576||!romHash.equals(expectedRomHash)||!romHash.equals(((Map<?,?>)root.get("overlay_rom")).get("sha256")))throw new SecurityException("ROM image identity mismatch");
 }
 public int sampleCount(){return samples.size();}
 public Map<String,Object> sample(){return Collections.unmodifiableMap(samples.get(index));}
 public synchronized void setSample(int n){checkOpen();if(n<0||n>=samples.size())throw new IllegalArgumentException("Unknown sample");index=n;}
 private void checkOpen(){if(closed)throw new IllegalStateException("Virtual endpoint closed");}
 @SuppressWarnings("unchecked") public int readByte(int address){checkOpen();if(address<0||address>0xffffff)throw new IllegalArgumentException("SSM24 address required");if(address<rom.length)return rom[address]&255;String key=String.format("%08X",address|0xff000000);Object value=((Map<String,Object>)samples.get(index).get("bytes")).get(key);if(!(value instanceof Number))throw new IllegalArgumentException("Uninitialized virtual RAM address "+key);double d=((Number)value).doubleValue();if(d!=(int)d||d<0||d>255)throw new IllegalArgumentException("Invalid initialized byte");return (int)d;}
 private static int u(byte v){return v&255;}
 private static int sum(byte[] b,int end){int n=0;for(int i=0;i<end;i++)n+=u(b[i]);return n&255;}
 private static int address(byte[] q,int i){return u(q[i])*65536+u(q[i+1])*256+u(q[i+2]);}
 public static byte[] frame(int code,byte[] values){if(values.length>254)throw new IllegalArgumentException("SSM response payload limit");byte[] b=new byte[values.length+6];b[0]=(byte)0x80;b[1]=(byte)0xf0;b[2]=0x10;b[3]=(byte)(values.length+1);b[4]=(byte)code;System.arraycopy(values,0,b,5,values.length);b[b.length-1]=(byte)sum(b,b.length-1);return b;}
 private synchronized byte[] reply(byte[] q){checkOpen();if(q==null||q.length<6||u(q[0])!=0x80||u(q[1])!=0x10||u(q[2])!=0xf0||u(q[3])!=q.length-5||sum(q,q.length-1)!=u(q[q.length-1]))throw new IllegalArgumentException("Invalid virtual SSM frame/module/length/checksum");int code=u(q[4]);byte[] value;int response;
  if(code==0xbf){if(q.length!=6)throw new IllegalArgumentException("Malformed BF");value=new byte[64];byte[] id={0x2f,0x12,0x51,0x53,0x06};System.arraycopy(id,0,value,3,5);response=0xff;}
  else if(code==0xa8){if(q.length<10||(q.length-7)%3!=0||u(q[5])>1)throw new IllegalArgumentException("Malformed A8");value=new byte[(q.length-7)/3];for(int i=0;i<value.length;i++)value[i]=(byte)readByte(address(q,6+i*3));response=0xe8;}
  else if(code==0xa0){if(q.length!=11||u(q[5])>1)throw new IllegalArgumentException("Malformed A0");int start=address(q,6),count=u(q[9])+1;if(count>254||(long)start+count>0x1000000L)throw new IllegalArgumentException("A0 response/address limit");value=new byte[count];for(int i=0;i<count;i++)value[i]=(byte)readByte(start+i);response=0xe0;}
  else throw new SecurityException("Virtual endpoint refuses command "+Integer.toHexString(code)+"; no writes/resets/programming permitted");
  requestCount++;if(wireAudit.size()<24){Map<String,Object> row=new LinkedHashMap<>();row.put("sample_index",index);row.put("request_hex",hex(q));row.put("response_hex",hex(frame(response,value)));wireAudit.add(row);}return frame(response,value);
 }
 public static String hex(byte[] b){StringBuilder s=new StringBuilder();for(byte v:b)s.append(String.format("%02X",v&255));return s.toString();}
 private static byte[] echoed(byte[] q,byte[] r){byte[] out=Arrays.copyOf(q,q.length+r.length);System.arraycopy(r,0,out,q.length,r.length);return out;}
 @Override public void open(byte[] start,byte[] stop){checkOpen();if(start.length!=0||stop.length!=0)throw new SecurityException("Virtual SSM requires no physical initialization");}
 @Override public byte[] send(byte[] request){return echoed(request,reply(request));}
 @Override public void send(byte[] request,byte[] response,PollingState pollState){byte[] r=reply(request);if(pollState.getCurrentState()==PollingState.State.STATE_0)r=echoed(request,r);if(r.length!=response.length)throw new IllegalArgumentException("Native response length differs from virtual frame");System.arraycopy(r,0,response,0,r.length);}
 @Override public void clearLine(){checkOpen();}
 @Override public void close(){closed=true;}
}
