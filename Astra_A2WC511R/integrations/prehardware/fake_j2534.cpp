// Instrumented ABI-compatible provider. Never forwards or loads another provider.
#include "j2534_abi.h"
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <string>
#include <vector>
#include <algorithm>
static std::vector<Msg> queue;
static U tick=0;
static bool hang_read=false;
static void event(const char *s){std::fprintf(stderr,"FAKE %s\n",s);std::fflush(stderr);}
static std::vector<unsigned char> unhex(const char *s){std::vector<unsigned char> r;while(*s){char b[3]={*s++,*s++,0};r.push_back(static_cast<unsigned char>(strtoul(b,nullptr,16)));}return r;}
static std::string fault(){char s[128]{};DWORD n=GetEnvironmentVariableA("A2WC_FAKE_FAULT",s,128);return n>0&&n<128?s:"";}
extern "C" {
long __stdcall PassThruOpen(void* p,U* id){event("Open");if(fault()=="open_failure")return 7;if(p||!id)return 4;*id=1;return 0;}
long __stdcall PassThruClose(U id){event("Close");if(fault()=="close_failure")return 7;return id==1?0:0x1a;}
long __stdcall PassThruConnect(U id,U protocol,U flags,U baud,U* ch){event("Connect ISO9141 flags0200 baud4800");if(fault()=="connect_failure")return 7;if(id!=1||protocol!=3||flags!=0x200||baud!=4800)return 7;*ch=2;return 0;}
long __stdcall PassThruDisconnect(U ch){event("Disconnect");if(fault()=="disconnect_failure")return 7;return ch==2?0:2;}
long __stdcall PassThruIoctl(U ch,U op,void *in,void *out){event("Ioctl");if(fault()=="config_failure")return 7;if(ch!=2||op!=2||out||!in)return 0xf;auto list=static_cast<ConfigList*>(in);const Config expected[]={{7,1},{10,1},{12,0},{3,1},{32,0},{22,0}};return list->count==6&&!std::memcmp(list->items,expected,sizeof(expected))?0:5;}
long __stdcall PassThruStartMsgFilter(U ch,U type,Msg* mask,Msg* pattern,Msg* flow,U* id){event("StartFilter");if(fault()=="filter_failure")return 7;if(ch!=2||type!=1||!mask||!pattern||flow||mask->size!=1||pattern->size!=1||mask->data[0]||pattern->data[0])return 7;*id=3;return 0;}
long __stdcall PassThruStopMsgFilter(U ch,U id){event("StopFilter");if(fault()=="stop_failure")return 7;return ch==2&&id==3?0:7;}
long __stdcall PassThruWriteMsgs(U ch,Msg* msg,U* n,U timeout){
    event("WriteMsgs");if(ch!=2||!msg||!n||*n!=1||timeout!=1000)return 7;
    auto bf=unhex("8010f001bf40"),a8=unhex("8010f014a800ff4c75ff4c8dff4ca1ff4c50ff4bc1ff4bc272");
    std::vector<unsigned char> q(msg->data,msg->data+std::min(msg->size,4128U));
    if(msg->protocol!=3||msg->rx||msg->tx||msg->timestamp||msg->extra||(q!=bf&&q!=a8)){event("FORBIDDEN_WIRE");return 0xa;}
    std::fprintf(stderr,"FAKE WIRE ");for(auto b:q)std::fprintf(stderr,"%02x",b);std::fprintf(stderr,"\n");std::fflush(stderr);
    Msg echo=*msg;echo.rx=1;echo.timestamp=++tick;echo.extra=echo.size;
    auto r=q==bf?unhex("80f01039ffa210112f1251530673facba62b81fea800000060ce54f9b1e4000c200000000000dc00005d1f3080f226000043fb00e1000000000000c1f0c2"):unhex("80f01007e811110102010100");
    unsigned sum=0;for(size_t i=0;i<r.size()-1;i++)sum+=r[i];r.back()=sum&255;
    auto f=fault(); if(f=="bad_checksum")r.back()^=1;if(f=="wrong_opcode")r[4]^=1;if(f=="wrong_identity"&&q==bf)r[8]^=1;
    hang_read=f=="hang_snapshot"&&q==a8;
    if(f=="wrong_identity"){sum=0;for(size_t i=0;i<r.size()-1;i++)sum+=r[i];r.back()=sum&255;}
    if(f!="missing_echo")queue.push_back(echo);
    if(f=="echo_mismatch"&&!queue.empty())queue.back().data[0]^=1;
    if(f=="timeout") {queue.clear();return 0;}
    Msg reply{};reply.protocol=3;reply.size=static_cast<U>(r.size());reply.extra=reply.size;reply.timestamp=++tick;std::copy(r.begin(),r.end(),reply.data);
    if(f=="rx_status")reply.rx=4;if(f=="wrong_protocol")reply.protocol=5;if(f=="extra_bytes")reply.data[reply.size++]=0;
    if(f=="oversized")reply.size=5000;
    if(f=="split") {for(auto b:r){Msg one{};one.protocol=3;one.size=one.extra=1;one.timestamp=++tick;one.data[0]=b;queue.push_back(one);}}
    else queue.push_back(reply);
    if(f=="short_tx")*n=0;return 0;
}
long __stdcall PassThruReadMsgs(U ch,Msg* msg,U* n,U){event("ReadMsgs");if(hang_read)Sleep(10000);if(ch!=2||!msg||!n||*n!=1)return 7;if(queue.empty()){*n=0;Sleep(20);return 0x10;}*msg=queue.front();queue.erase(queue.begin());*n=1;return 0;}
// Tripwire exports: the worker must never resolve or invoke any of these.
long __stdcall PassThruSetProgrammingVoltage(U,U,U){event("FORBIDDEN_VOLTAGE");return 7;}
long __stdcall PassThruStartPeriodicMsg(U,Msg*,U*,U){event("FORBIDDEN_PERIODIC");return 7;}
}
