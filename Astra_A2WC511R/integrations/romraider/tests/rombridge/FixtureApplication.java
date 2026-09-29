package rombridge;
import com.romraider.editor.ecu.ECUEditorManager;
/** Test double host, not a copy of RomRaider. */
public class FixtureApplication {
 public static void main(String[] args)throws Exception{
  ModelTests.Rom r=new ModelTests.Rom();r.bin[100]=10;
  r.tables.add(new ModelTests.Table(r,"Fixture",100,2));
  ECUEditorManager.editor=new ModelTests.Editor(r);
  System.out.println("FIXTURE_READY");System.out.flush();
  while(System.in.read()!=-1){}
  System.exit(0);
 }
}
