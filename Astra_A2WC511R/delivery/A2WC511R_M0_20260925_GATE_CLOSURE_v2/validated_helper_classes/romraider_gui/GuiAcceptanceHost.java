package rombridge;
import java.nio.file.*;import java.util.*;import java.awt.*;import java.awt.event.*;import javax.swing.*;import javax.imageio.ImageIO;
import com.romraider.editor.ecu.*;import com.romraider.maps.*;import com.romraider.swing.*;

/** Test-only GUI driver. Native agent and confirmation callback are unchanged.
 * Commands are fixed acceptance actions on one disposable profile/ROM.
 */
public final class GuiAcceptanceHost {
 static Path root,out;static ECUEditor editor;static int imageIndex=0;static boolean stop=false;
 static Map<String,Object> map(Object...a){return RomAccess.map(a);}
 static void write(Path path,Object v)throws Exception{Path temp=Paths.get(path.toString()+".tmp");Files.write(temp,Json.stringify(v).getBytes("UTF-8"));Files.move(temp,path,StandardCopyOption.ATOMIC_MOVE);}
 static Rom rom(){return editor.getImages().get(imageIndex);}
 static Path saved(){return root.resolve("GUI_SAVED_"+out.getFileName()+".NOT_FLASH_READY.bin");}
 static TableTreeNode node(){return rom().getTableNodes().get("idle speed target a");}
 static Table table(){return node().getTable();}
 static void showTable(){editor.setLastSelectedRom(rom());editor.displayTable(node());}
 static java.util.List<Component> descendants(Component c){java.util.List<Component> result=new ArrayList<>();result.add(c);if(c instanceof Container)for(Component x:((Container)c).getComponents())result.addAll(descendants(x));return result;}
 static Dialog approval(){for(Window w:Window.getWindows())if(w instanceof Dialog&&w.isShowing()&&((Dialog)w).getTitle().equals("Codex RomRaider changeset approval"))return (Dialog)w;throw new IllegalStateException("No visible native changeset dialog");}
 static JButton button(Component owner,String text){for(Component c:descendants(owner))if(c instanceof JButton&&text.equals(((JButton)c).getText())&&c.isShowing()&&c.isEnabled())return (JButton)c;throw new IllegalStateException("Visible enabled button not found: "+text);}
 static void screenshot(Component c,String name)throws Exception{Point p=c.getLocationOnScreen();ImageIO.write(new Robot().createScreenCapture(new Rectangle(p.x,p.y,c.getWidth(),c.getHeight())),"png",out.resolve(name+".png").toFile());}
 static Map<String,Object> view()throws Exception{Table t=table();java.util.List<Object> values=new ArrayList<>();for(int i=0;i<Math.min(4,t.getData().length);i++){DataCell c=t.getData()[i];values.add(map("raw",c.getBinValue(),"real",c.getRealValue(),"original_raw",c.getOriginalValue(),"display",t.getTableView().getCellAsString(i)));}return map("image_index",imageIndex,"open_roms",editor.getImages().size(),"file",rom().getFullFileName().toString(),"sha256",RomAccess.sha(rom().getBinary()),"table_visible",t.getTableView().isShowing(),"values",values);}
 static void clickMenu(String name){for(int i=0;i<editor.getJMenuBar().getMenuCount();i++){JMenu m=editor.getJMenuBar().getMenu(i);if(m==null)continue;for(int j=0;j<m.getItemCount();j++){JMenuItem item=m.getItem(j);if(item!=null&&item.getText().toLowerCase(Locale.ROOT).startsWith(name)&&item.isEnabled()){item.doClick();return;}}}throw new IllegalStateException("Native menu item absent: "+name);}
 @SuppressWarnings("unchecked") static Object command(Map<String,Object> q)throws Exception{
  String op=(String)q.get("op"),label=(String)q.get("label");
  if(op.equals("inspect")){screenshot(editor,label);return view();}
  if(op.equals("inspect_dialog")){Dialog d=approval();java.util.List<String> texts=new ArrayList<>();for(Component c:descendants(d))if(c instanceof JLabel)texts.add(((JLabel)c).getText());screenshot(d,label);return map("title",d.getTitle(),"visible",d.isShowing(),"text",texts);}
  if(op.equals("click_dialog")){String text=(String)q.get("button");if(!text.equals("Yes")&&!text.equals("No"))throw new IllegalArgumentException("Acceptance only Yes/No");Dialog d=approval();JButton b=button(d,text);String caption=d.getTitle();b.doClick();return map("native_dialog",caption,"clicked_native_button",text,"mode","Actual JButton event, no callback or dialog value override");}
  if(op.equals("undo")){node().getFrame().getTableMenuBar().getUndoAll().doClick();return view();}
  if(op.equals("compare_original")){node().getFrame().getTableMenuBar().getCompareOriginal().doClick();return view();}
  if(op.equals("compare_off")){node().getFrame().getTableMenuBar().getCompareOff().doClick();return view();}
  if(op.equals("native_mutation_during_dialog")){approval();DataCell c=table().getData()[1];c.setBinValue(c.getBinValue()+1);return view();}
  if(op.equals("save_as")){SwingUtilities.invokeLater(()->{try{clickMenu("save ");}catch(Throwable e){e.printStackTrace();}});return map("scheduled","native Save As menu event");}
  if(op.equals("choose_save_path")){JFileChooser chooser=null;for(Window w:Window.getWindows())if(w.isShowing())for(Component c:descendants(w))if(c instanceof JFileChooser)chooser=(JFileChooser)c;if(chooser==null)throw new IllegalStateException("Native Save As chooser absent");Path file=saved();if(Files.exists(file))throw new IllegalStateException("Refuse overwrite");chooser.setSelectedFile(file.toFile());screenshot(SwingUtilities.getWindowAncestor(chooser),label);button(chooser,"Save").doClick();return map("native_save_path",file.toString());}
  if(op.equals("reopen_saved")){editor.openImage(saved().toString());return map("native_open_scheduled",true);}
  if(op.equals("open_export")){Path file=Paths.get((String)q.get("path")).toRealPath();if(!file.startsWith(out.toRealPath())||!file.toString().endsWith(".NOT_FLASH_READY.bin"))throw new SecurityException("Acceptance export only");editor.openImage(file.toString());return map("native_open_scheduled",true);}
  if(op.equals("acknowledge_checksum")){for(Window w:Window.getWindows())if(w instanceof Dialog&&w.isShowing()&&((Dialog)w).getTitle().equals("ERROR - Checksums Failed")){screenshot(w,label);button(w,"OK").doClick();return map("native_warning_acknowledged","Checksums Failed","bytes_not_corrected",true);}throw new IllegalStateException("Native checksum warning absent");}
  if(op.equals("select_image")){imageIndex=((Number)q.get("index")).intValue();showTable();return view();}
  if(op.equals("stop")){stop=true;editor.dispose();return map("stopped",true);}
  throw new IllegalArgumentException("Unknown fixed acceptance action");
 }
 public static void main(String[] args)throws Exception{
  root=Paths.get(args[0]).toRealPath();out=Paths.get(args[1]).toRealPath();editor=ECUEditorManager.getECUEditor();SwingUtilities.invokeAndWait(()->{editor.setExtendedState(JFrame.NORMAL);editor.setSize(1100,740);editor.setLocation(40,40);editor.initializeEditorUI();editor.openImage(root.resolve("A2WC511R.GUI_TEST.NOT_FLASH_READY.bin").toString());});
  long end=System.currentTimeMillis()+60000;while(editor.getImages().isEmpty()&&System.currentTimeMillis()<end)Thread.sleep(100);SwingUtilities.invokeAndWait(()->{showTable();editor.toFront();});write(out.resolve("gui_ready.json"),map("ready",true,"native_jar","Installed RomRaider1.1.0","physical_io",false));
  Set<String> seen=new HashSet<>();while(!stop){try(java.util.stream.Stream<Path> stream=Files.list(out)){for(Path p:(Iterable<Path>)stream.filter(x->x.getFileName().toString().matches("command_[0-9]+\\.json"))::iterator){String n=p.getFileName().toString();if(!seen.add(n))continue;Map<String,Object> q=(Map<String,Object>)Json.parse(new String(Files.readAllBytes(p),"UTF-8"));Object[] result={null};SwingUtilities.invokeAndWait(()->{try{result[0]=map("ok",true,"result",command(q));}catch(Throwable e){result[0]=map("ok",false,"error",e.toString());e.printStackTrace();}});write(out.resolve(n.replace("command_","result_")),result[0]);}}Thread.sleep(60);}
  System.exit(0);
 }
}
