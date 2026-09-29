package a2wc.virtualrr;
import java.nio.file.*;import java.util.*;import java.lang.reflect.*;import java.awt.Point;import java.awt.Robot;import java.awt.Rectangle;import javax.swing.*;import javax.imageio.ImageIO;
import com.romraider.Settings;import com.romraider.util.SettingsManager;
import com.romraider.logger.ecu.EcuLogger;
import com.romraider.logger.ecu.definition.EcuParameter;
import com.romraider.logger.ecu.ui.SerialPortComboBox;
import com.romraider.logger.ecu.ui.paramlist.ParameterListTableModel;
import com.romraider.logger.ecu.ui.handler.livedata.LiveDataTableModel;
import com.romraider.io.connection.ConnectionManagerFactory;
import rombridge.Json;
/** Bounded test driver of the unchanged installed logger UI and controller. */
public final class NativeLoggerGui {
 static Object field(Object o,String name)throws Exception{Field f=o.getClass().getDeclaredField(name);f.setAccessible(true);return f.get(o);}
 static Path out;static EcuLogger logger;
 static void shot(String name)throws Exception{Point p=logger.getLocationOnScreen();ImageIO.write(new Robot().createScreenCapture(new Rectangle(p.x,p.y,logger.getWidth(),logger.getHeight())),"png",out.resolve(name+".png").toFile());}
 static void write(String name,Object o)throws Exception{Files.write(out.resolve(name),Json.stringify(o).getBytes("UTF-8"));}
 static boolean wanted(EcuParameter p){if(p.getId().matches("E91[01][0-9]"))return true;if(!p.getId().startsWith("E_A2WC511R_"))return false;for(String a:p.getAddress().getAddresses())if(!Arrays.asList("FF4BC1","FF4BC2","FF4C8D").contains(a.replace("0x","").toUpperCase(Locale.ROOT)))return false;return true;}
 @SuppressWarnings("unchecked")public static void main(String[] a)throws Exception{
  out=Paths.get(a[0]);Files.createDirectories(out);ConnectionManagerFactory.snapshots=Paths.get(a[1]);ConnectionManagerFactory.snapshotsHash=a[2];ConnectionManagerFactory.rom=Paths.get(a[3]);ConnectionManagerFactory.romHash=a[4];
  Settings s=SettingsManager.getSettings();s.setLoggerProtocol("SSM");s.setTransportProtocol("ISO9141");s.setJ2534Device("");s.setLoggerPort("A2WC-VIRTUAL");s.setLoggerPortDefault("A2WC-VIRTUAL");s.setAutoConnectOnStartup(false);s.setFileLoggingControllerSwitchActive(false);s.setLoggerDefinitionFilePath(a[5]);s.setLoggerProfileFilePath(a[6]);s.setLoggerOutputDirPath(out.resolve("VIRTUAL_NATIVE_CSV").toString());s.setFastPoll(false);s.setLogExternalsOnly(false);s.setElm327Enabled(false);
  logger=EcuLogger.getEcuLogger(null);SwingUtilities.invokeAndWait(()->{logger.setExtendedState(JFrame.NORMAL);logger.setSize(1150,820);logger.setLocation(60,50);logger.setVisible(true);logger.setTitle("VIRTUAL SOFTWARE ONLY - NO VEHICLE - A2WC511R final05");logger.setRefreshMode(false);try{((SerialPortComboBox)field(logger,"portsComboBox")).refreshPortList(new TreeSet<String>(Arrays.asList("A2WC-VIRTUAL")),"A2WC-VIRTUAL");}catch(Exception e){throw new RuntimeException(e);}s.setLoggerPort("A2WC-VIRTUAL");logger.startLogging();});
  long until=System.currentTimeMillis()+30000;while(!logger.isEcuInit()&&System.currentTimeMillis()<until)Thread.sleep(100);if(!logger.isEcuInit())throw new IllegalStateException("Native GUI BF initialization not completed");
  Thread.sleep(600);SwingUtilities.invokeAndWait(()->{try{ParameterListTableModel model=(ParameterListTableModel)field(logger,"dataTabParamListTableModel");int count=0;for(EcuParameter p:(List<EcuParameter>)field(logger,"ecuParams")){if(wanted(p)){model.selectParam(p,true);count++;}}if(count!=20)throw new AssertionError("Expected20 native parameters, got "+count);}catch(Exception e){throw new RuntimeException(e);}});
  Files.createDirectories(out.resolve("VIRTUAL_NATIVE_CSV"));SwingUtilities.invokeAndWait(()->{try{((JToggleButton)field(logger,"logToFileButton")).doClick();}catch(Exception e){throw new RuntimeException(e);}});
  java.util.List<Object> views=new ArrayList<>();for(int i=0;i<15;i++){
   until=System.currentTimeMillis()+10000;while((ConnectionManagerFactory.active==null||ConnectionManagerFactory.active.requestCount<1)&&System.currentTimeMillis()<until)Thread.sleep(50);
   VirtualSSMConnectionManager endpoint=ConnectionManagerFactory.active;endpoint.setSample(i);Thread.sleep(600);final int sample=i;
   SwingUtilities.invokeAndWait(()->{try{LiveDataTableModel m=(LiveDataTableModel)field(logger,"dataTableModel");java.util.List<Object> rows=new ArrayList<>();for(int r=0;r<m.getRowCount();r++)rows.add(Arrays.asList(m.getValueAt(r,0),m.getValueAt(r,2),m.getValueAt(r,4)));views.add(NativeLoggerAcceptance.map("sample_index",sample,"native_live_rows",rows));if(sample==0||sample==14)shot("native_logger_sample_"+sample);}catch(Exception e){throw new RuntimeException(e);}});
  }
  SwingUtilities.invokeAndWait(()->{try{((JToggleButton)field(logger,"logToFileButton")).doClick();}catch(Exception e){throw new RuntimeException(e);}});logger.stopLogging();write("native_gui_views.json",views);write("result.json",NativeLoggerAcceptance.map("status","PASS","samples",15,"physical_connections",0,"provider_enumeration_or_loading",false,"classification","VIRTUAL_SOFTWARE_SCENARIO_NOT_VEHICLE_TELEMETRY"));SwingUtilities.invokeAndWait(()->logger.dispose());System.exit(0);
 }
}
