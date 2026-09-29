import a2wc.virtualrr.ReadOnlySSMCollector.ReadOnlyGate;
import com.romraider.io.connection.ConnectionManager;
import com.romraider.logger.ecu.comms.manager.PollingState;
import com.romraider.logger.ecu.comms.manager.PollingStateImpl;
import java.util.Arrays;

/** In-memory command policy only. No collector main, serial or J2534 object. */
public class IndependentCollectorGateCheck {
    static int checks;
    static byte[] frame(int command,int... payload) {
        byte[] q=new byte[payload.length+6];
        q[0]=(byte)0x80;q[1]=0x10;q[2]=(byte)0xf0;q[3]=(byte)(payload.length+1);q[4]=(byte)command;
        for(int i=0;i<payload.length;i++)q[5+i]=(byte)payload[i];
        checksum(q);return q;
    }
    static void checksum(byte[] q) {int sum=0;for(int i=0;i<q.length-1;i++)sum+=q[i]&255;q[q.length-1]=(byte)sum;}
    static void check(boolean value,String name) {checks++;if(!value)throw new AssertionError(name);}
    static void rejects(byte[] q) {try {ReadOnlyGate.validate(q);throw new AssertionError("accepted "+Arrays.toString(q));}catch(SecurityException expected){checks++;}}
    static void accepts(byte[] q) {ReadOnlyGate.validate(q);checks++;}
    static class MemoryOnly implements ConnectionManager {
        int sent;
        public void open(byte[] a,byte[] b){throw new AssertionError("open delegated");}
        public byte[] send(byte[] q){sent++;return new byte[0];}
        public void send(byte[] q,byte[] r,PollingState p){sent++;}
        public void clearLine(){throw new AssertionError("clearLine delegated");}
        public void close(){}
    }
    interface Attempt {void run();}
    static void denied(Attempt a) {try {a.run();throw new AssertionError("forbidden action delegated");}catch(SecurityException expected){checks++;}}
    public static void main(String[] args) {
        accepts(frame(0xbf));
        for(int cmd=0;cmd<256;cmd++)if(cmd!=0xbf)rejects(frame(cmd));
        accepts(frame(0xa0,0,0,0,0,239));
        accepts(frame(0xa0,0,15,255,255,0));
        rejects(frame(0xa0,0,15,255,255,1));
        rejects(frame(0xa0,0,16,0,0,0));
        rejects(frame(0xa0,0,0,0,0,240));
        rejects(frame(0xa0,1,0,0,0,0));
        byte[] six=frame(0xa8,0,255,76,117,255,76,141,255,76,161,255,76,80,255,75,193,255,75,194);
        accepts(six);
        for(int address:new int[]{0xff7400,0xff736c,0xff4c74,0xff4c76,0x60}) {
            byte[] q=six.clone();q[6]=(byte)(address>>>16);q[7]=(byte)(address>>>8);q[8]=(byte)address;checksum(q);rejects(q);
        }
        byte[] q=six.clone();q[5]=1;checksum(q);rejects(q);
        q=six.clone();q[0]=0;checksum(q);rejects(q);
        q=six.clone();q[1]=0x18;checksum(q);rejects(q);
        q=six.clone();q[2]=0;checksum(q);rejects(q);
        q=six.clone();q[3]--;checksum(q);rejects(q);
        q=six.clone();q[q.length-1]^=1;rejects(q);
        rejects(frame(0xb8,0,0,0x60,0x40));
        rejects(frame(0xb0,0,0,0x20,0,1));
        MemoryOnly memory=new MemoryOnly();ReadOnlyGate gate=new ReadOnlyGate(memory);
        PollingState state=new PollingStateImpl();
        gate.send(six,new byte[40],state);check(memory.sent==1,"one reviewed frame delegated");
        state.setFastPoll(true);denied(()->gate.send(six,new byte[40],state));check(memory.sent==1,"fast mode never delegated");
        state.setFastPoll(false);state.setLastState(PollingState.State.STATE_1);denied(()->gate.send(six,new byte[40],state));
        state.setLastState(PollingState.State.STATE_0);state.setCurrentState(PollingState.State.STATE_1);denied(()->gate.send(six,new byte[40],state));
        denied(()->gate.clearLine());denied(()->gate.open(new byte[0],new byte[0]));
        denied(()->gate.send(frame(0xb8,0,0,0x60,0x40)));
        check(memory.sent==1,"no forbidden request reached memory-only delegate");
        System.out.println("PASS "+checks+" independent gate checks; in-memory delegate only; no collector main/provider/serial load");
    }
}
