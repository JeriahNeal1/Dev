// Fixed-read, x86 stdcall client for one pinned LOCAL FAKE DLL only.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <bcrypt.h>
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <string>
#include <vector>
#include "C:/Dev/Astra_A2WC511R/integrations/ecuflash_virtual/vendor/j2534_tactrix.h"
static_assert(sizeof(void*)==4 && sizeof(PASSTHRU_MSG)==4152,"x86 J2534 ABI only");
static const wchar_t ROOT[]=L"C:\\Dev\\Astra_A2WC511R";
static const char DLL_SHA[]="58be9aaad8e004eb5bd04a600e53394a1139752f1b698ca1832124dbbb4d5cc0";
static const char VERSION[]="OpenECU Subaru SH7058 DUAL  Kernel V1.07";
static FILE* journal=nullptr;
static unsigned calls=0;
static void need(bool ok,const char* message){if(!ok)throw std::runtime_error(message);}
static std::string hex(const unsigned char* bytes,size_t count){
    static const char digit[]="0123456789abcdef";std::string out;out.reserve(count*2);
    for(size_t i=0;i<count;i++){out+=digit[bytes[i]>>4];out+=digit[bytes[i]&15];}return out;
}
static std::string file_sha(HANDLE file){
    BCRYPT_ALG_HANDLE algorithm=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
    need(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)>=0,"SHA256 provider");
    need(BCryptCreateHash(algorithm,&hash,nullptr,0,nullptr,0,0)>=0,"SHA256 object");
    unsigned char block[65536],digest[32];DWORD read=0;
    for(;;){need(ReadFile(file,block,sizeof(block),&read,nullptr)!=0,"Hash file read");if(!read)break;
        need(BCryptHashData(hash,block,read,0)>=0,"SHA256 update");}
    need(BCryptFinishHash(hash,digest,sizeof(digest),0)>=0,"SHA256 finish");
    BCryptDestroyHash(hash);BCryptCloseAlgorithmProvider(algorithm,0);return hex(digest,sizeof(digest));
}
static bool simple_name(const std::wstring& name){
    if(name.empty()||name.size()>80)return false;
    for(wchar_t c:name)if(!((c>=L'a'&&c<=L'z')||(c>=L'A'&&c<=L'Z')||(c>=L'0'&&c<=L'9')||c==L'_'||c==L'-'))return false;
    return true;
}
static std::vector<unsigned char> frame(const std::vector<unsigned char>& payload){
    std::vector<unsigned char> out={0xbe,0xef,(unsigned char)(payload.size()>>8),(unsigned char)payload.size()};
    out.insert(out.end(),payload.begin(),payload.end());unsigned sum=0;for(auto b:out)sum+=b;out.push_back((unsigned char)sum);return out;
}
static std::vector<unsigned char> fixed_request(bool version,unsigned address){
    need(version?address==0:(address<0x100000&&address%512==0),"Fixed request address");
    if(version)return frame({1});
    return frame({3,(unsigned char)(address>>24),(unsigned char)(address>>16),(unsigned char)(address>>8),(unsigned char)address,2,0});
}
static bool allowed_request(const std::vector<unsigned char>& wire,bool version,unsigned address){return wire==fixed_request(version,address);}
struct GuardedMessage{
    unsigned long before[4];PASSTHRU_MSG message;unsigned long after[4];
    GuardedMessage(){memset(this,0,sizeof(*this));for(int i=0;i<4;i++)before[i]=after[i]=0x51a7c0de;}
    bool intact()const{for(int i=0;i<4;i++)if(before[i]!=0x51a7c0de||after[i]!=0x51a7c0de)return false;return true;}
};
static bool valid_reply(const PASSTHRU_MSG& message,bool version){
    unsigned n=version?sizeof(VERSION):512;
    if(message.ProtocolID!=ISO9141||message.RxStatus||message.TxFlags||message.DataSize!=n+6||message.ExtraDataIndex!=message.DataSize)return false;
    const auto* b=message.Data;
    if(b[0]!=0xbe||b[1]!=0xef||((unsigned)b[2]*256+b[3])!=n+1||b[4]!=(version?0x81:0x83))return false;
    unsigned sum=0;for(unsigned i=0;i<message.DataSize-1;i++)sum+=b[i];
    if((unsigned char)sum!=b[message.DataSize-1])return false;
    return !version||memcmp(b+5,VERSION,sizeof(VERSION))==0;
}
static void message_set(PASSTHRU_MSG& msg,const std::vector<unsigned char>& wire){
    memset(&msg,0,sizeof(msg));need(wire.size()<=sizeof(msg.Data),"Bounded message");msg.ProtocolID=ISO9141;msg.DataSize=(unsigned long)wire.size();memcpy(msg.Data,wire.data(),wire.size());
}
static void record(const char* api,unsigned long status,unsigned long count,uintptr_t before,uintptr_t after,const PASSTHRU_MSG* msg){
    std::string bytes=msg&&msg->DataSize<=sizeof(msg->Data)?hex(msg->Data,msg->DataSize):"";
    fprintf(journal,"{\"sequence\":%u,\"function\":\"%s\",\"status\":%lu,\"count\":%lu,\"esp_before\":%u,\"esp_after\":%u,\"wire_hex\":\"%s\",\"physical\":false}\n",calls++,api,status,count,(unsigned)before,(unsigned)after,bytes.c_str());
    need(fflush(journal)==0,"Native journal flush");need(before==after,"stdcall stack imbalance");need(status==0,"Native fake API status failure");
}
#define FN(name) auto name=reinterpret_cast<PF_##name*>(GetProcAddress(dll,#name));need(name!=nullptr,"Missing exact fake export " #name)
#define CALL(name,expr,count,msg) do{uintptr_t stackBefore=0,stackAfter=0;__asm {mov stackBefore,esp} \
    unsigned long result=(expr);__asm {mov stackAfter,esp} \
    record(#name,result,count,stackBefore,stackAfter,msg);}while(0)

static int selftest(){
    unsigned tests=0;
    need(!simple_name(L"../other")&&!simple_name(L"C:\\Windows\\op20pt32.dll")&&simple_name(L"native_01"),"Session name controls");tests++;
    PASSTHRU_MSG base{};auto packet=frame(std::vector<unsigned char>(513,0));packet[4]=0x83;unsigned sum=0;for(size_t i=0;i<packet.size()-1;i++)sum+=packet[i];packet.back()=(unsigned char)sum;
    message_set(base,packet);base.ExtraDataIndex=base.DataSize;need(valid_reply(base,false),"Valid data baseline");tests++;
    for(unsigned index:{0u,2u,3u,4u,517u}){auto bad=base;bad.Data[index]^=1;if(index!=517){unsigned total=0;for(unsigned i=0;i<517;i++)total+=bad.Data[i];bad.Data[517]=(unsigned char)total;}need(!valid_reply(bad,false),"Malformed frame accepted");tests++;}
    for(unsigned type=0;type<5;type++){auto bad=base;if(type==0)bad.ProtocolID=4;if(type==1)bad.RxStatus=1;if(type==2)bad.TxFlags=1;if(type==3)bad.DataSize--;if(type==4)bad.ExtraDataIndex--;need(!valid_reply(bad,false),"Message metadata accepted");tests++;}
    std::vector<unsigned char> vp={0x81};vp.insert(vp.end(),VERSION,VERSION+sizeof(VERSION));message_set(base,frame(vp));base.ExtraDataIndex=base.DataSize;need(valid_reply(base,true),"Exact version");tests++;
    base.Data[base.DataSize-3]^=1;sum=0;for(unsigned i=0;i<base.DataSize-1;i++)sum+=base.Data[i];base.Data[base.DataSize-1]=(unsigned char)sum;need(!valid_reply(base,true),"Wrong version accepted");tests++;
    auto request=fixed_request(false,0);for(unsigned code:{1u,2u,4u,0x20u,0x21u,0x22u,0x23u,0x24u,0x25u,0x31u,0x36u}){auto bad=request;bad[4]=(unsigned char)code;need(!allowed_request(bad,false,0),"Other command allowed");tests++;}
    need(!allowed_request(fixed_request(false,512),false,0),"Out of sequence address");tests++;
    GuardedMessage guarded;need(guarded.intact(),"Canary baseline");guarded.after[0]^=1;need(!guarded.intact(),"Canary mutation missed");tests++;
    puts(("PASS "+std::to_string(tests)+" native negative/control checks; no DLL loaded or RPC attempted").c_str());return 0;
}

int wmain(int argc,wchar_t** argv){
    try{
        if(argc==2&&wcscmp(argv[1],L"--selftest")==0)return selftest();
        need(argc==1,"No transport/path/address/opcode arguments accepted");
        wchar_t session[128];DWORD size=GetEnvironmentVariableW(L"A2WC_NATIVE_RAW_SESSION",session,128);need(size&&size<128&&simple_name(session),"Verified session environment required");
        std::wstring name(session),folder=std::wstring(ROOT)+L"\\work\\ecuflash_dynamic\\"+name;
        std::wstring expected=folder+L"\\native\\a2wc_ecuflash_virtual32.dll";
        wchar_t envFake[32768];size=GetEnvironmentVariableW(L"A2WC_FAKE_DLL",envFake,32768);need(size&&size<32768&&expected==envFake,"Only session's exact fake path accepted");
        HANDLE locked=CreateFileW(expected.c_str(),GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
        need(locked!=INVALID_HANDLE_VALUE,"Fake DLL read lock");need(file_sha(locked)==DLL_SHA,"Fake DLL SHA256 pin mismatch before loading");
        HMODULE dll=LoadLibraryExW(expected.c_str(),nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_SYSTEM32);need(dll!=nullptr,"Pinned fake DLL load");
        FN(PassThruOpen);FN(PassThruConnect);FN(PassThruStartMsgFilter);FN(PassThruWriteMsgs);FN(PassThruReadMsgs);FN(PassThruStopMsgFilter);FN(PassThruDisconnect);FN(PassThruClose);
        std::wstring out=std::wstring(ROOT)+L"\\reports\\local\\ecuflash_dynamic\\native_raw_supplement\\"+name;
        need(_wfopen_s(&journal,(out+L"\\NATIVE_API.jsonl").c_str(),L"wx")==0&&journal,"New native journal required");
        unsigned long device=0,channel=0,filter=0,count=1;
        CALL(PassThruOpen,PassThruOpen((void*)"A2WC VIRTUAL RAW SUPPLEMENT ONLY",&device),0,nullptr);need(device==1,"Synthetic device id");
        CALL(PassThruConnect,PassThruConnect(device,ISO9141,ISO9141_NO_CHECKSUM,62500,&channel),0,nullptr);need(channel>=100,"Synthetic channel id");
        PASSTHRU_MSG mask{},pattern{};message_set(mask,{0xff,0xff});message_set(pattern,{0xbe,0xef});
        CALL(PassThruStartMsgFilter,PassThruStartMsgFilter(channel,PASS_FILTER,&mask,&pattern,nullptr,&filter),0,nullptr);
        std::vector<unsigned char> image;image.reserve(0x100000);
        for(unsigned index=0;index<=2048;index++){
            bool version=index==0;unsigned address=version?0:(index-1)*512;GuardedMessage tx,rx;
            auto request=fixed_request(version,address);need(allowed_request(request,version,(unsigned)image.size()),"Ascending fixed outbound contract");
            message_set(tx.message,request);count=1;
            CALL(PassThruWriteMsgs,PassThruWriteMsgs(channel,&tx.message,&count,2000),count,&tx.message);need(count==1&&tx.intact(),"TX count or ABI canary failure");
            count=1;CALL(PassThruReadMsgs,PassThruReadMsgs(channel,&rx.message,&count,2000),count,&rx.message);
            need(count==1&&rx.intact()&&valid_reply(rx.message,version),"RX count/canary/frame/version failure");
            if(!version)image.insert(image.end(),rx.message.Data+5,rx.message.Data+517);
        }
        need(image.size()==0x100000,"Incomplete exact range");
        CALL(PassThruStopMsgFilter,PassThruStopMsgFilter(channel,filter),0,nullptr);
        CALL(PassThruDisconnect,PassThruDisconnect(channel),0,nullptr);
        CALL(PassThruClose,PassThruClose(device),0,nullptr);
        HANDLE file=CreateFileW((out+L"\\NATIVE_RETURNED_BYTES.bin").c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
        need(file!=INVALID_HANDLE_VALUE,"New output image required");DWORD written=0;need(WriteFile(file,image.data(),(DWORD)image.size(),&written,nullptr)&&written==image.size(),"Image write");need(FlushFileBuffers(file)!=0,"Image flush");CloseHandle(file);
        fclose(journal);journal=nullptr;FreeLibrary(dll);CloseHandle(locked);
        printf("PASS native stdcall fake-DLL raw read; %u calls; 2048 blocks; 1048576 returned bytes; virtual only\n",calls);return 0;
    }catch(const std::exception& e){if(journal){fprintf(journal,"{\"terminal_failure\":true,\"physical\":false}\n");fclose(journal);}fprintf(stderr,"FAIL terminal: %s\n",e.what());return 1;}
}
