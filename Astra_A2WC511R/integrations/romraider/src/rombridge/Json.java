package rombridge;

import java.util.*;
import java.lang.reflect.Array;

/** Small strict JSON codec. No object deserialization, expressions, or executable input. */
public final class Json {
    public static Object parse(String text) {
        Parser p = new Parser(text); Object value = p.value(0); p.ws();
        if (p.i != text.length()) throw new IllegalArgumentException("Trailing JSON data");
        return value;
    }
    public static String stringify(Object value) {
        StringBuilder b = new StringBuilder(); write(b, value, 0); return b.toString();
    }
    private static void write(StringBuilder b, Object v, int depth) {
        if (depth > 64) throw new IllegalArgumentException("JSON nesting too deep");
        if (v == null) { b.append("null"); return; }
        if (v instanceof String || v instanceof Character || v instanceof Enum) {
            b.append('"'); String s = v.toString();
            for (int i=0;i<s.length();i++) {
                char c=s.charAt(i);
                switch(c) {
                    case '"': b.append("\\\""); break; case '\\': b.append("\\\\"); break;
                    case '\n': b.append("\\n"); break; case '\r': b.append("\\r"); break;
                    case '\t': b.append("\\t"); break;
                    default: if(c<32) b.append(String.format("\\u%04x",(int)c)); else b.append(c);
                }
            }
            b.append('"'); return;
        }
        if(v instanceof Boolean) { b.append(v); return; }
        if(v instanceof Number) {
            double d=((Number)v).doubleValue();
            if(Double.isNaN(d)||Double.isInfinite(d)) throw new IllegalArgumentException("Non-finite JSON number");
            b.append(v); return;
        }
        if(v instanceof Map) {
            b.append('{'); boolean first=true;
            for(Object e0:((Map<?,?>)v).entrySet()) {
                Map.Entry<?,?> e=(Map.Entry<?,?>)e0;
                if(!first)b.append(',');first=false;write(b,String.valueOf(e.getKey()),depth+1);b.append(':');write(b,e.getValue(),depth+1);
            }
            b.append('}'); return;
        }
        if(v instanceof Iterable || v.getClass().isArray()) {
            b.append('[');boolean first=true;
            Iterable<?> values;
            if(v instanceof Iterable)values=(Iterable<?>)v;
            else { List<Object> l=new ArrayList<Object>();for(int i=0;i<Array.getLength(v);i++)l.add(Array.get(v,i)); values=l; }
            for(Object e:values){if(!first)b.append(',');first=false;write(b,e,depth+1);}b.append(']');return;
        }
        throw new IllegalArgumentException("Unsupported JSON type "+v.getClass().getName());
    }
    private static final class Parser {
        final String s;int i=0;Parser(String s){this.s=s;}
        void ws(){while(i<s.length() && " \r\n\t".indexOf(s.charAt(i))>=0)i++;}
        char take(){if(i>=s.length())throw new IllegalArgumentException("Truncated JSON");return s.charAt(i++);}
        Object value(int depth){
            if(depth>64)throw new IllegalArgumentException("JSON nesting too deep");ws();
            if(i>=s.length())throw new IllegalArgumentException("Missing JSON value");
            char c=s.charAt(i);
            if(c=='"')return string();
            if(c=='{'){
                i++;Map<String,Object> m=new LinkedHashMap<String,Object>();ws();if(i<s.length()&&s.charAt(i)=='}'){i++;return m;}
                while(true){ws();String k=string();ws();if(take()!=':')throw new IllegalArgumentException("Expected colon");if(m.containsKey(k))throw new IllegalArgumentException("Duplicate key");m.put(k,value(depth+1));ws();c=take();if(c=='}')return m;if(c!=',')throw new IllegalArgumentException("Expected comma");}
            }
            if(c=='['){i++;List<Object> l=new ArrayList<Object>();ws();if(i<s.length()&&s.charAt(i)==']'){i++;return l;}while(true){l.add(value(depth+1));ws();c=take();if(c==']')return l;if(c!=',')throw new IllegalArgumentException("Expected comma");}}
            for(String token:new String[]{"true","false","null"})if(s.startsWith(token,i)){i+=token.length();return token.equals("null")?null:Boolean.valueOf(token);}
            int begin=i;while(i<s.length()&&"-+0123456789.eE".indexOf(s.charAt(i))>=0)i++;
            String n=s.substring(begin,i);
            if(!n.matches("-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?"))throw new IllegalArgumentException("Bad JSON number");
            Double d=Double.valueOf(n);if(!Double.isFinite(d))throw new IllegalArgumentException("Non-finite JSON number");return d;
        }
        String string(){
            if(take()!='"')throw new IllegalArgumentException("Expected string");StringBuilder b=new StringBuilder();
            while(true){char c=take();if(c=='"')return b.toString();if(c<32)throw new IllegalArgumentException("Control character");if(c!='\\'){b.append(c);continue;}c=take();
                switch(c){case '"':case '\\':case '/':b.append(c);break;case 'b':b.append('\b');break;case 'f':b.append('\f');break;case 'n':b.append('\n');break;case 'r':b.append('\r');break;case 't':b.append('\t');break;case 'u':if(i+4>s.length())throw new IllegalArgumentException("Short escape");b.append((char)Integer.parseInt(s.substring(i,i+4),16));i+=4;break;default:throw new IllegalArgumentException("Bad escape");}
            }
        }
    }
}
