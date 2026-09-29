package rombridge;
import java.nio.file.*;import java.util.*;import javax.swing.SwingUtilities;
import com.romraider.maps.*;
/** Actual installed checksum implementation; reads inputs, repairs only clones. */
public final class NativeChecksumCheck {
 public static void main(String[] args)throws Exception {
  Throwable[] error={null};
  SwingUtilities.invokeAndWait(()->{try{
   Table1D t=new Table1D();t.setStorageAddress(0xFFB80);t.setDataSize(168);
   if(t.getRamOffset()!=0)throw new AssertionError("Unexpected offset");
   List<Object> rows=new ArrayList<>();byte[] raw=Files.readAllBytes(Paths.get(args[0]));byte[] fixed=Files.readAllBytes(Paths.get(args[1]));
   for(int i=0;i<2;i++){byte[] input=i==0?raw:fixed;int status=RomChecksum.validateRomChecksum(input,t);byte[] calculated=input.clone();RomChecksum.calculateRomChecksum(calculated,t);if(status!=(i==0?1:0)||!Arrays.equals(calculated,fixed))throw new AssertionError("Native checksum disagreement");rows.add(RomAccess.map("path",args[i],"sha256",RomAccess.sha(input),"native_validation",status,"native_repaired_sha256",RomAccess.sha(calculated),"calculated_exactly_equals_corrected_derivative",true));}
   Files.write(Paths.get(args[2]),Json.stringify(RomAccess.map("status","PASS","inputs",rows,"implementation","Actual installed RomRaider.jar RomChecksum; no input writes or vehicle access")).getBytes("UTF-8"));
  }catch(Throwable e){error[0]=e;e.printStackTrace();}});
  System.exit(error[0]==null?0:1);
 }
}
