package rombridge;

import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.lang.instrument.Instrumentation;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.*;
import javax.swing.*;
import com.sun.net.httpserver.*;

/** Load with -javaagent:romraider-bridge.jar=path/to/bridge.properties.
 * No bytecode transformation or RomRaider jar replacement; reflection to public model API.
 */
public final class Agent {
    private static HttpServer server;
    public static synchronized void premain(String arg, final Instrumentation inst) {
        if(server!=null){System.err.println("RomRaider bridge already running");return;}
        try{
            if(arg==null)throw new IllegalArgumentException("Bridge properties path required");
            final Properties p=new Properties();try(InputStream in=Files.newInputStream(Paths.get(arg))){p.load(in);}
            final byte[] token=p.getProperty("token","").getBytes(StandardCharsets.US_ASCII);
            if(token.length<48)throw new IllegalArgumentException("Use a random token of at least 48 characters");
            final Path connection=Paths.get(p.getProperty("connection")).toAbsolutePath().normalize();
            final Path work=Paths.get(p.getProperty("work")).toAbsolutePath().normalize();
            final boolean allow="true".equals(p.getProperty("allow_apply","false"));
            final RomAccess access=new RomAccess(new RomAccess.EditorProvider(){
                public Object editor()throws Exception{
                    Class<?> manager=null;
                    for(Class<?> c:inst.getAllLoadedClasses())if(c.getName().equals("com.romraider.editor.ecu.ECUEditorManager")){manager=c;break;}
                    if(manager==null)throw new IllegalStateException("RomRaider ECU Editor is not loaded yet");
                    return RomAccess.call(manager,"getECUEditorWithoutCreation");
                }
            },new RomAccess.Approval(){public boolean approve(String message){return JOptionPane.showConfirmDialog(null,message,"Codex RomRaider changeset approval",JOptionPane.YES_NO_OPTION,JOptionPane.WARNING_MESSAGE)==JOptionPane.YES_OPTION;}},allow,work);
            server=HttpServer.create(new InetSocketAddress("127.0.0.1",0),0);
            final int port=server.getAddress().getPort();
            server.setExecutor(Executors.newSingleThreadExecutor(new ThreadFactory(){public Thread newThread(Runnable r){Thread t=new Thread(r,"RomRaiderBridgeHTTP");t.setDaemon(true);return t;}}));
            server.createContext("/rpc",new HttpHandler(){
                @SuppressWarnings("unchecked") public void handle(HttpExchange x)throws IOException{
                    int code=200;Object response;
                    try{
                        if(!x.getRequestMethod().equals("POST")||!x.getRequestURI().toString().equals("/rpc"))throw new SecurityException("POST /rpc only");
                        String host=x.getRequestHeaders().getFirst("Host");
                        if(!("127.0.0.1:"+port).equals(host)||x.getRequestHeaders().getFirst("Origin")!=null)throw new SecurityException("Invalid origin/host");
                        String auth=x.getRequestHeaders().getFirst("Authorization");
                        if(auth==null||!auth.startsWith("Bearer ")||!MessageDigest.isEqual(token,auth.substring(7).getBytes(StandardCharsets.US_ASCII)))throw new SecurityException("Unauthorized");
                        ByteArrayOutputStream b=new ByteArrayOutputStream();byte[]buffer=new byte[8192];int n;
                        try(InputStream in=x.getRequestBody()){while((n=in.read(buffer))!=-1){b.write(buffer,0,n);if(b.size()>4194304)throw new IllegalArgumentException("Request too large");}}
                        Object parsed=Json.parse(new String(b.toByteArray(),StandardCharsets.UTF_8));if(!(parsed instanceof Map))throw new IllegalArgumentException("Object required");
                        Map<String,Object>q=(Map<String,Object>)parsed;RomAccess.exact(q,"op","args");if(!(q.get("args") instanceof Map))throw new IllegalArgumentException("args must be object");
                        final String op=RomAccess.text(q.get("op"));final Map<String,Object>args=(Map<String,Object>)q.get("args");
                        final long deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(230);
                        final FutureTask<Object>task=new FutureTask<Object>(new Callable<Object>(){public Object call()throws Exception{return access.dispatchBefore(op,args,deadline);}});
                        // One HTTP worker serializes requests; all model operations are on Swing's EDT.
                        SwingUtilities.invokeLater(task);
                        try{response=RomAccess.map("ok",true,"result",task.get(240,TimeUnit.SECONDS));}
                        catch(TimeoutException e){task.cancel(false);throw new IllegalStateException("Editor busy or approval timed out; inspect state before retrying any commit");}
                        catch(ExecutionException e){Throwable cause=e.getCause();if(cause instanceof Exception)throw (Exception)cause;throw e;}
                    }catch(SecurityException e){code=403;response=RomAccess.map("ok",false,"error",e.getClass().getSimpleName()+": "+e.getMessage());}
                     catch(Exception e){code=400;response=RomAccess.map("ok",false,"error",e.getClass().getSimpleName()+": "+e.getMessage());}
                    byte[] out=Json.stringify(response).getBytes(StandardCharsets.UTF_8);x.getResponseHeaders().set("Content-Type","application/json; charset=utf-8");x.getResponseHeaders().set("Cache-Control","no-store");x.sendResponseHeaders(code,out.length);try(OutputStream os=x.getResponseBody()){os.write(out);}x.close();
                }
            });
            // Make the HTTP dispatcher's inherited daemon status independent of the application's exit policy.
            Thread starter=new Thread(new Runnable(){public void run(){server.start();}},"RomRaiderBridgeStart");starter.setDaemon(true);starter.start();starter.join();Files.createDirectories(connection.getParent());
            Files.write(connection,Json.stringify(RomAccess.map("url","http://127.0.0.1:"+port+"/rpc","token",new String(token,StandardCharsets.US_ASCII),"bridge_session",access.session,"apply_enabled",allow,"version","2.0.0")).getBytes(StandardCharsets.UTF_8));
            Runtime.getRuntime().addShutdownHook(new Thread(new Runnable(){public void run(){server.stop(0);try{Files.deleteIfExists(connection);}catch(IOException ignored){}}}));
            System.err.println("RomRaider model bridge running on loopback. Apply enabled="+allow+"; local confirmation required per commit.");
        }catch(Exception e){System.err.println("RomRaider bridge did not start: "+e);if(server!=null){server.stop(0);server=null;}}
    }
}
