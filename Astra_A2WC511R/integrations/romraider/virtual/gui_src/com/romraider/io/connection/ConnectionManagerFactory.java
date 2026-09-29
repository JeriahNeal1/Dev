package com.romraider.io.connection;
import java.nio.file.*;
import a2wc.virtualrr.VirtualSSMConnectionManager;
import com.romraider.util.SettingsManager;
/** Isolated GUI test classpath only. No physical implementation or fallback. */
public final class ConnectionManagerFactory {
 public static Path snapshots,rom;public static String snapshotsHash,romHash;
 public static volatile VirtualSSMConnectionManager active;
 public static ConnectionManager getManager(String port,ConnectionProperties p){
  if(!"A2WC-VIRTUAL".equals(port)||!SettingsManager.getSettings().getJ2534Device().isEmpty())throw new SecurityException("Only isolated A2WC-VIRTUAL endpoint allowed");
  try{return active=new VirtualSSMConnectionManager(snapshots,snapshotsHash,rom,romHash);}catch(Exception e){throw new IllegalStateException(e);}
 }
}
