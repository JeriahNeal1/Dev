import java.io.*;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import com.romraider.io.connection.ConnectionManager;
import com.romraider.io.protocol.ssm.iso9141.SSMProtocol;
import com.romraider.logger.ecu.comms.manager.PollingState;
import com.romraider.logger.ecu.comms.manager.PollingStateImpl;
import com.romraider.logger.ecu.definition.Module;
import rombridge.Json;

/** Isolated native RomRaider codec with recorded compiled OEM virtual replies.
 * No ConnectionManagerFactory, serial/J2534 factory, DLL, device or socket.
 */
public final class NativeVirtualEndpoint {
    static final String REQUEST="8010f014a800ff4c75ff4c8dff4ca1ff4c50ff4bc1ff4bc272";
    static byte[] unhex(String text) {
        if(text.length()%2!=0)throw new IllegalArgumentException("Odd hex length");
        byte[] b=new byte[text.length()/2];
        for(int i=0;i<b.length;i++)b[i]=(byte)Integer.parseInt(text.substring(i*2,i*2+2),16);
        return b;
    }
    static String hex(byte[] bytes) {
        StringBuilder b=new StringBuilder();for(byte v:bytes)b.append(String.format("%02x",v&255));return b.toString();
    }
    static String sha(byte[] bytes)throws Exception{return hex(MessageDigest.getInstance("SHA-256").digest(bytes));}
    static Map<String,Object> map(Object... kv){Map<String,Object> r=new LinkedHashMap<>();for(int i=0;i<kv.length;i+=2)r.put((String)kv[i],kv[i+1]);return r;}
    static void emit(Object value){System.out.println(Json.stringify(value));System.out.flush();}

    static final class TranscriptConnection implements ConnectionManager {
        final List<Map<String,Object>> samples;int index=0;boolean closed=false;
        TranscriptConnection(List<Map<String,Object>> samples){this.samples=samples;}
        public void open(byte[] a,byte[] b){throw new SecurityException("No device initialization is implemented");}
        public void clearLine(){throw new SecurityException("No line clearing or break is implemented");}
        public void close(){closed=true;}
        public byte[] send(byte[] request){throw new SecurityException("Only explicit STATE_0 virtual read is implemented");}
        public void send(byte[] request,byte[] response,PollingState state){
            if(closed)throw new IllegalStateException("Virtual endpoint closed");
            if(!hex(request).equals(REQUEST)||state.isFastPoll()||state.getCurrentState()!=PollingState.State.STATE_0||state.getLastState()!=PollingState.State.STATE_0)throw new SecurityException("Only fixed six-address one-shot A8 is implemented");
            if(index>=samples.size())throw new IllegalStateException("Recorded virtual samples exhausted");
            Map<String,Object> sample=samples.get(index++);
            if(!REQUEST.equals(sample.get("request_hex")))throw new SecurityException("Fixture request differs");
            byte[] reply=unhex((String)sample.get("response_hex"));
            if(response.length!=request.length+reply.length)throw new IllegalArgumentException("Native response buffer length differs");
            System.arraycopy(request,0,response,0,request.length);System.arraycopy(reply,0,response,request.length,reply.length);
        }
    }

    @SuppressWarnings("unchecked") public static void main(String[] args)throws Exception {
        if(args.length!=4)throw new IllegalArgumentException("Exact fixture/hash and stockROM/hash are required");
        byte[] fixture=Files.readAllBytes(Paths.get(args[0]));
        if(!sha(fixture).equals(args[1])||!sha(Files.readAllBytes(Paths.get(args[2]))).equals(args[3]))throw new SecurityException("Fixture or stock ROM hash differs");
        Map<String,Object> root=(Map<String,Object>)Json.parse(new String(fixture,"UTF-8"));
        if(!"PASS".equals(root.get("status"))||!"VIRTUAL_COMPILED_OEM_A8_READS_NOT_PHYSICAL_TELEMETRY".equals(root.get("classification"))||!args[3].equals(((Map<?,?>)root.get("stock_rom")).get("sha256")))throw new SecurityException("Fixture identity/classification differs");
        List<Map<String,Object>> samples=(List<Map<String,Object>>)root.get("samples");
        if(samples==null||samples.isEmpty())throw new SecurityException("No recorded samples");
        SSMProtocol protocol=new SSMProtocol();PollingStateImpl state=new PollingStateImpl();state.setFastPoll(false);
        Module module=new Module("ECU",new byte[]{0x10},"M0.7 isolated virtual OEM A8",new byte[]{(byte)0xf0},false);
        int[] addresses={0xff4c75,0xff4c8d,0xff4ca1,0xff4c50,0xff4bc1,0xff4bc2};
        byte[][] addressBytes=new byte[addresses.length][3];
        for(int i=0;i<addresses.length;i++)addressBytes[i]=new byte[]{(byte)(addresses[i]>>>16),(byte)(addresses[i]>>>8),(byte)addresses[i]};
        byte[] canonical=protocol.constructReadAddressRequest(module,addressBytes);
        if(!hex(canonical).equals(REQUEST))throw new SecurityException("Installed native A8 encoder differs");
        TranscriptConnection connection=new TranscriptConnection(samples);
        emit(map("type","ready","mode","ISOLATED_NATIVE_ROMRAIDER_VIRTUAL","native_request_hex",REQUEST,"samples",samples.size(),"physical_backend",false));
        try(BufferedReader reader=new BufferedReader(new InputStreamReader(System.in,"UTF-8"))){
            for(String line;(line=reader.readLine())!=null;){
                Map<String,Object> command=(Map<String,Object>)Json.parse(line);
                if(!"exchange".equals(command.get("op"))||!REQUEST.equals(command.get("request_hex"))||command.size()!=2)throw new SecurityException("Only exact fixed A8 exchange is supported");
                int index=connection.index;
                byte[] wire=new byte[canonical.length+12];connection.send(canonical,wire,state);
                if(!Arrays.equals(canonical,Arrays.copyOf(wire,canonical.length)))throw new SecurityException("Exact native echo differs");
                byte[] data=protocol.parseResponseData(protocol.preprocessResponse(canonical,wire,state));
                if(data.length!=6)throw new SecurityException("Native payload length differs");
                emit(map("type","exchange","wire_hex",hex(wire),"native_raw_hex",hex(data),"native_parser_verified",true,
                    "sample_id",samples.get(index).get("sample_id"),"fixture_index",index,"physical_backend",false));
            }
        }finally{connection.close();}
    }
}
