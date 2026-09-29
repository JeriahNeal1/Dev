#define NOMINMAX
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include "vendor/j2534_tactrix.h"
#include "vendor/json.hpp"
#include <mutex>
#include <string>
#include <vector>
#pragma comment(lib,"ws2_32.lib")
using json=nlohmann::json;
static std::mutex callMutex;
static SOCKET rpcSocket=INVALID_SOCKET;
static unsigned long long rpcSequence=0;
static std::string lastError="No error";
static std::string env(const char *name){char b[4096];DWORD n=GetEnvironmentVariableA(name,b,sizeof(b));if(!n||n>=sizeof(b))throw std::runtime_error("missing environment");return std::string(b,n);}
static void nativeAudit(const json&event){
    static HANDLE journal=INVALID_HANDLE_VALUE;
    if(journal==INVALID_HANDLE_VALUE){
        auto path=env("A2WC_NATIVE_API_LOG");
        journal=CreateFileA(path.c_str(),FILE_APPEND_DATA,FILE_SHARE_READ|FILE_SHARE_WRITE,nullptr,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,nullptr);
        if(journal==INVALID_HANDLE_VALUE)throw std::runtime_error("native audit file unavailable");
    }
    std::string data=event.dump()+"\n";DWORD wrote=0;
    if(!WriteFile(journal,data.data(),static_cast<DWORD>(data.size()),&wrote,nullptr)||wrote!=data.size()||!FlushFileBuffers(journal))
        throw std::runtime_error("native audit write failed; no call success claimed");
}
static void transfer(SOCKET s,char *p,int n,bool sendData){while(n){int r=sendData?send(s,p,n,0):recv(s,p,n,0);if(r<=0)throw std::runtime_error(std::string(sendData?"virtual send failed WSA=":"virtual receive failed WSA=")+std::to_string(WSAGetLastError()));p+=r;n-=r;}}
static json rpc(json q){
    std::lock_guard<std::mutex> lock(callMutex);
    static bool initialized=false;if(!initialized){WSADATA d;if(WSAStartup(MAKEWORD(2,2),&d))throw std::runtime_error("WSA");initialized=true;}
    FILETIME ft;GetSystemTimePreciseAsFileTime(&ft);LARGE_INTEGER c,f;QueryPerformanceCounter(&c);QueryPerformanceFrequency(&f);
    q["utc_filetime"]=static_cast<uint64_t>(ft.dwHighDateTime)<<32|ft.dwLowDateTime;
    q["monotonic_counter"]=c.QuadPart;q["monotonic_frequency"]=f.QuadPart;q["thread"]=GetCurrentThreadId();q["pid"]=GetCurrentProcessId();
    auto sequence=rpcSequence++;nativeAudit({{"sequence",sequence},{"phase","REQUEST_BEFORE_DISPATCH"},{"request",q}});
    q["token"]=env("A2WC_RPC_TOKEN");
    try{
        if(rpcSocket==INVALID_SOCKET){
        rpcSocket=socket(AF_INET,SOCK_STREAM,IPPROTO_TCP);if(rpcSocket==INVALID_SOCKET)throw std::runtime_error("virtual socket creation failed WSA="+std::to_string(WSAGetLastError()));
        DWORD deadline=5000;setsockopt(rpcSocket,SOL_SOCKET,SO_RCVTIMEO,reinterpret_cast<char*>(&deadline),sizeof(deadline));
        setsockopt(rpcSocket,SOL_SOCKET,SO_SNDTIMEO,reinterpret_cast<char*>(&deadline),sizeof(deadline));
        BOOL noDelay=TRUE;setsockopt(rpcSocket,IPPROTO_TCP,TCP_NODELAY,reinterpret_cast<char*>(&noDelay),sizeof(noDelay));
        sockaddr_in address{};address.sin_family=AF_INET;address.sin_addr.s_addr=htonl(INADDR_LOOPBACK);address.sin_port=htons(static_cast<u_short>(std::stoul(env("A2WC_RPC_PORT"))));
        if(connect(rpcSocket,reinterpret_cast<sockaddr*>(&address),sizeof(address)))throw std::runtime_error("virtual connect failed WSA="+std::to_string(WSAGetLastError()));
        }
        SOCKET s=rpcSocket;
        auto text=q.dump();uint32_t size=htonl(static_cast<uint32_t>(text.size()));transfer(s,reinterpret_cast<char*>(&size),4,true);transfer(s,text.data(),static_cast<int>(text.size()),true);
        transfer(s,reinterpret_cast<char*>(&size),4,false);size=ntohl(size);if(size>4*1024*1024)throw std::runtime_error("oversized virtual reply");
        text.resize(size);transfer(s,text.data(),size,false);auto response=json::parse(text);
        nativeAudit({{"sequence",sequence},{"phase","RETURN"},{"response",response}});return response;
    }catch(const std::exception&e){if(rpcSocket!=INVALID_SOCKET)closesocket(rpcSocket);rpcSocket=INVALID_SOCKET;
        try{nativeAudit({{"sequence",sequence},{"phase","RPC_EXCEPTION"},{"status",ERR_FAILED},{"error",e.what()}});}catch(...){}throw;}
}
static json message(const PASSTHRU_MSG *m){
    if(!m||m->DataSize>4128)throw std::runtime_error("invalid J2534 message");
    const char*h="0123456789abcdef";std::string bytes;for(unsigned long i=0;i<m->DataSize;i++){bytes+=h[m->Data[i]>>4];bytes+=h[m->Data[i]&15];}
    return {{"protocol",m->ProtocolID},{"rx_status",m->RxStatus},{"tx_flags",m->TxFlags},{"timestamp",m->Timestamp},{"extra",m->ExtraDataIndex},{"data_hex",bytes}};
}
static unsigned char hexbyte(char a,char b){
    auto nibble=[](char v)->int{if(v>='0'&&v<='9')return v-'0';if(v>='a'&&v<='f')return v-'a'+10;if(v>='A'&&v<='F')return v-'A'+10;throw std::runtime_error("non-hex virtual reply");};
    return static_cast<unsigned char>((nibble(a)<<4)|nibble(b));
}
static bool boundedName(const void* p,std::string& s){
    if(!p)return true;
    for(size_t i=0;i<1024;i++){char ch;SIZE_T n=0;if(!ReadProcessMemory(GetCurrentProcess(),static_cast<const char*>(p)+i,&ch,1,&n)||n!=1)return false;if(!ch)return true;s+=ch;}
    return false;
}
static long badarg(const char*fn,const char*why){return rpc({{"function",fn},{"invalid_arguments",why}}).at("status");}
static void putmessage(PASSTHRU_MSG*m,const json& v){
    *m={};m->ProtocolID=v.at("protocol");m->RxStatus=v.value("rx_status",0UL);m->TxFlags=v.value("tx_flags",0UL);m->Timestamp=v.value("timestamp",0UL);
    auto s=v.at("data_hex").get<std::string>();if(s.size()%2||s.size()>8256)throw std::runtime_error("bad virtual message");
    m->DataSize=static_cast<unsigned long>(s.size()/2);m->ExtraDataIndex=v.value("extra",m->DataSize);
    for(unsigned long i=0;i<m->DataSize;i++)m->Data[i]=hexbyte(s[i*2],s[i*2+1]);
}
#define BEGIN try {
#define END }catch(const std::exception&e){lastError=e.what();try{rpc({{"function",__func__},{"native_exception",lastError}});}catch(...){}return ERR_FAILED;}
extern "C" {
long __stdcall PassThruOpen(const void* name,unsigned long* id){BEGIN
    if(!id)return badarg("PassThruOpen","null device output");std::string text;if(!boundedName(name,text))return badarg("PassThruOpen","unreadable or unterminated name (limit1024)");
    std::string hex;const char*d="0123456789abcdef";bool ascii=true;for(unsigned char c:text){hex+=d[c>>4];hex+=d[c&15];if(c<32||c>126)ascii=false;}
    json q={{"function","PassThruOpen"},{"name_pointer",reinterpret_cast<uintptr_t>(name)},{"name_hex",hex},{"name",ascii?text:"<non-ASCII; see name_hex>"}};auto r=rpc(q);*id=r.value("device",0UL);return r.at("status");END}
long __stdcall PassThruClose(unsigned long id){BEGIN return rpc({{"function","PassThruClose"},{"device",id}}).at("status");END}
long __stdcall PassThruConnect(unsigned long id,unsigned long protocol,unsigned long flags,unsigned long baud,unsigned long*ch){BEGIN
    if(!ch)return badarg("PassThruConnect","null channel output");auto r=rpc({{"function","PassThruConnect"},{"device",id},{"protocol",protocol},{"flags",flags},{"baud",baud}});*ch=r.value("channel",0UL);return r.at("status");END}
long __stdcall PassThruDisconnect(unsigned long ch){BEGIN return rpc({{"function","PassThruDisconnect"},{"channel",ch}}).at("status");END}
long __stdcall PassThruWriteMsgs(unsigned long ch,const void*p,unsigned long*n,unsigned long timeout){BEGIN
    if(!n||!p)return badarg("PassThruWriteMsgs","null messages/count");if(*n>128)return badarg("PassThruWriteMsgs","count exceeds128");auto m=static_cast<const PASSTHRU_MSG*>(p);json a=json::array();for(unsigned long i=0;i<*n;i++)a.push_back(message(m+i));
    auto r=rpc({{"function","PassThruWriteMsgs"},{"channel",ch},{"timeout",timeout},{"count",*n},{"messages",a}});*n=r.value("count",0UL);return r.at("status");END}
long __stdcall PassThruReadMsgs(unsigned long ch,void*p,unsigned long*n,unsigned long timeout){BEGIN
    if(!n||!p)return badarg("PassThruReadMsgs","null messages/count");if(*n>128)return badarg("PassThruReadMsgs","count exceeds128");auto r=rpc({{"function","PassThruReadMsgs"},{"channel",ch},{"timeout",timeout},{"count",*n}});
    auto a=r.value("messages",json::array());if(a.size()>*n)throw std::runtime_error("too many RX");auto m=static_cast<PASSTHRU_MSG*>(p);for(size_t i=0;i<a.size();i++)putmessage(m+i,a[i]);*n=static_cast<unsigned long>(a.size());return r.at("status");END}
long __stdcall PassThruStartPeriodicMsg(unsigned long ch,const void*p,unsigned long*id,unsigned long interval){BEGIN
    if(!p||!id)return badarg("PassThruStartPeriodicMsg","null message/id");
    auto r=rpc({{"function","PassThruStartPeriodicMsg"},{"channel",ch},{"interval",interval},{"message",message(static_cast<const PASSTHRU_MSG*>(p))}});if(id)*id=r.value("id",0UL);return r.at("status");END}
long __stdcall PassThruStopPeriodicMsg(unsigned long ch,unsigned long id){BEGIN return rpc({{"function","PassThruStopPeriodicMsg"},{"channel",ch},{"id",id}}).at("status");END}
long __stdcall PassThruStartMsgFilter(unsigned long ch,unsigned long type,const void*mask,const void*pattern,const void*flow,unsigned long*id){BEGIN
    if(!mask||!pattern||!id)return badarg("PassThruStartMsgFilter","null mask/pattern/id");
    auto r=rpc({{"function","PassThruStartMsgFilter"},{"channel",ch},{"filter_type",type},{"mask",mask?message(static_cast<const PASSTHRU_MSG*>(mask)):json()},{"pattern",pattern?message(static_cast<const PASSTHRU_MSG*>(pattern)):json()},{"flow",flow?message(static_cast<const PASSTHRU_MSG*>(flow)):json()}});if(id)*id=r.value("id",0UL);return r.at("status");END}
long __stdcall PassThruStopMsgFilter(unsigned long ch,unsigned long id){BEGIN return rpc({{"function","PassThruStopMsgFilter"},{"channel",ch},{"id",id}}).at("status");END}
long __stdcall PassThruSetProgrammingVoltage(unsigned long id,unsigned long pin,unsigned long voltage){BEGIN
    return rpc({{"function","PassThruSetProgrammingVoltage"},{"device",id},{"pin",pin},{"voltage",voltage}}).at("status");END}
long __stdcall PassThruReadVersion(unsigned long id,char*firmware,char*dll,char*api){BEGIN
    if(!firmware||!dll||!api)return badarg("PassThruReadVersion","null version output");
    auto r=rpc({{"function","PassThruReadVersion"},{"device",id},{"firmware_pointer",reinterpret_cast<uintptr_t>(firmware)},{"dll_pointer",reinterpret_cast<uintptr_t>(dll)},{"api_pointer",reinterpret_cast<uintptr_t>(api)}});if(r.at("status")==0){strcpy_s(firmware,80,r.at("firmware").get<std::string>().c_str());strcpy_s(dll,80,r.at("dll").get<std::string>().c_str());strcpy_s(api,80,r.at("api").get<std::string>().c_str());}return r.at("status");END}
long __stdcall PassThruGetLastError(char*text){BEGIN
    if(!text)return badarg("PassThruGetLastError","null error output");
    json q={{"function","PassThruGetLastError"}};if(lastError!="No error")q["native_error"]=lastError;
    auto r=rpc(q);strcpy_s(text,80,r.value("error",lastError).substr(0,79).c_str());return r.at("status");END}
long __stdcall PassThruIoctl(unsigned long id,unsigned long op,const void*in,void*out){BEGIN
    json q={{"function","PassThruIoctl"},{"id",id},{"ioctl",op},{"input_pointer",reinterpret_cast<uintptr_t>(in)},{"output_pointer",reinterpret_cast<uintptr_t>(out)}};
    if((op==GET_CONFIG||op==SET_CONFIG)&&!in)return badarg("PassThruIoctl","null config input");
    if((op==READ_VBATT||op==READ_PROG_VOLTAGE)&&!out)return badarg("PassThruIoctl","null voltage output");
    if((op==GET_CONFIG||op==SET_CONFIG)&&in){auto list=static_cast<const SCONFIG_LIST*>(in);if(list->NumOfParams>128)return badarg("PassThruIoctl","config exceeds128");if(list->NumOfParams&&!list->ConfigPtr)return badarg("PassThruIoctl","null ConfigPtr");q["config"]=json::array();for(unsigned long i=0;i<list->NumOfParams;i++)q["config"].push_back({{"parameter",list->ConfigPtr[i].Parameter},{"value",list->ConfigPtr[i].Value}});}
    if(op==FAST_INIT&&in)q["init_message"]=message(static_cast<const PASSTHRU_MSG*>(in));
    if(op==FIVE_BAUD_INIT&&in){auto a=static_cast<const SBYTE_ARRAY*>(in);if(a->NumOfBytes>65536)return badarg("PassThruIoctl","oversized initialization input");if(a->NumOfBytes&&!a->BytePtr)return badarg("PassThruIoctl","null initialization bytes");q["input_bytes"]=std::vector<unsigned char>(a->BytePtr,a->BytePtr+a->NumOfBytes);}
    unsigned long serviceCapacity=0;
    if(op==TX_IOCTL_APP_SERVICE){
        unsigned long header[2]{};SIZE_T n=0;
        if(!in||!out||!ReadProcessMemory(GetCurrentProcess(),in,header,sizeof(header),&n)||n!=sizeof(header)||header[0]>4096)return badarg("PassThruIoctl","invalid inline APP_SERVICE header");
        if(!ReadProcessMemory(GetCurrentProcess(),out,&serviceCapacity,4,&n)||n!=4||serviceCapacity>65536)return badarg("PassThruIoctl","invalid inline APP_SERVICE output capacity");
        std::vector<unsigned char> bytes(header[0]);if(header[0]&&(!ReadProcessMemory(GetCurrentProcess(),static_cast<const char*>(in)+8,bytes.data(),bytes.size(),&n)||n!=bytes.size()))return badarg("PassThruIoctl","unreadable inline APP_SERVICE bytes");
        q["service_id"]=header[1];q["input_bytes"]=bytes;q["output_capacity"]=serviceCapacity;q["abi_provenance"]="VENDOR_KLOGGER_SAMPLE_AND_INSTALLED_RVA96C20_INLINE_RECORD";
    }
    if(op==TX_IOCTL_SET_DLL_DEBUG_FLAGS||op==TX_IOCTL_SET_DEV_DEBUG_FLAGS)q["unqualified_debug_argument"]=reinterpret_cast<uintptr_t>(in);
    if(op==TX_IOCTL_GET_DEVICE_INSTANCES){
        q["output_contract"]="PINNED_ECUFLASH_1_44_4870_SINGLE_UTF16LE_NUL_PATH_MAX512_WCHAR";
        if(in||!out)return badarg("PassThruIoctl","70004 requires NULL input and WCHAR output per recovered caller");
    }
    auto r=rpc(q);long status=r.at("status");if(status)return status;
    if((op==READ_VBATT||op==READ_PROG_VOLTAGE)&&out)*static_cast<unsigned long*>(out)=r.at("value");
    if(op==TX_IOCTL_GET_DEVICE_INSTANCES&&out){
        auto path=r.at("device_instance").get<std::string>();if(path.empty()||path.size()>120)return ERR_FAILED;
        for(char c:path)if(c<32||c>126)return ERR_FAILED;
        auto wide=static_cast<wchar_t*>(out);for(size_t i=0;i<path.size();i++)wide[i]=path[i];wide[path.size()]=0;
    }
    if(op==TX_IOCTL_APP_SERVICE&&out){auto data=r.at("output_bytes").get<std::vector<unsigned char>>();if(data.size()>serviceCapacity)return ERR_BUFFER_OVERFLOW;memcpy(static_cast<char*>(out)+4,data.data(),data.size());*static_cast<unsigned long*>(out)=static_cast<unsigned long>(data.size());}
    if(op==GET_CONFIG&&in){auto list=const_cast<SCONFIG_LIST*>(static_cast<const SCONFIG_LIST*>(in));auto items=r.at("config");if(items.size()!=list->NumOfParams)return ERR_FAILED;for(unsigned long i=0;i<list->NumOfParams;i++)list->ConfigPtr[i].Value=items[i].at("value");}
    if(op==FAST_INIT&&out)putmessage(static_cast<PASSTHRU_MSG*>(out),r.at("init_message"));
    if(op==FIVE_BAUD_INIT&&out){auto a=static_cast<SBYTE_ARRAY*>(out);auto data=r.at("output_bytes").get<std::vector<unsigned char>>();if(data.size()>a->NumOfBytes)return ERR_BUFFER_OVERFLOW;std::copy(data.begin(),data.end(),a->BytePtr);a->NumOfBytes=static_cast<unsigned long>(data.size());}
    return status;END}
}
