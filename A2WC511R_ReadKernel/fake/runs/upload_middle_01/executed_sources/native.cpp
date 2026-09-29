// Fixed purpose, native x86 host for ONE pinned project-local FAKE J2534 DLL.
// No physical provider paths, arbitrary kernel/address/opcode or retry arguments.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <bcrypt.h>
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <string>
#include <vector>
#include <algorithm>
#include "vendor/j2534_tactrix.h"
#include "owned_artifact.h"
static_assert(sizeof(void*)==4 && sizeof(PASSTHRU_MSG)==4152,"Pinned x86 J2534 ABI");
using Bytes=std::vector<unsigned char>;
static FILE* journal=nullptr;
static unsigned calls=0,frames=0;
static void need(bool b,const char* why){if(!b)throw std::runtime_error(why);}
static std::string hex(const unsigned char* p,size_t n){const char*d="0123456789abcdef";std::string s;for(size_t i=0;i<n;i++){s+=d[p[i]>>4];s+=d[p[i]&15];}return s;}
static std::string sha_file(HANDLE file){
 BCRYPT_ALG_HANDLE alg=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
 need(BCryptOpenAlgorithmProvider(&alg,BCRYPT_SHA256_ALGORITHM,nullptr,0)>=0,"SHA256 provider");
 need(BCryptCreateHash(alg,&hash,nullptr,0,nullptr,0,0)>=0,"SHA256 create");
 unsigned char block[65536],digest[32];DWORD n=0;
 do{need(ReadFile(file,block,sizeof(block),&n,nullptr)!=0,"SHA file read");if(n)need(BCryptHashData(hash,block,n,0)>=0,"SHA update");}while(n);
 need(BCryptFinishHash(hash,digest,sizeof(digest),0)>=0,"SHA finish");BCryptDestroyHash(hash);BCryptCloseAlgorithmProvider(alg,0);return hex(digest,32);
}
static unsigned char sum8(const Bytes& b){unsigned n=0;for(auto v:b)n+=v;return static_cast<unsigned char>(n);}
static Bytes ssm(const Bytes& body,bool reply=false){need(body.size()>=1&&body.size()<=255,"SSM payload limit");Bytes b={0x80,static_cast<unsigned char>(reply?0xF0:0x10),static_cast<unsigned char>(reply?0x10:0xF0),static_cast<unsigned char>(body.size())};b.insert(b.end(),body.begin(),body.end());b.push_back(sum8(b));return b;}
static Bytes beef(const Bytes& body){need(body.size()>=1&&body.size()<=518,"BEEF payload limit");Bytes b={0xBE,0xEF,static_cast<unsigned char>(body.size()>>8),static_cast<unsigned char>(body.size())};b.insert(b.end(),body.begin(),body.end());b.push_back(sum8(b));return b;}
static Bytes parse_ssm(const Bytes& b){need(b.size()>=6&&b[0]==0x80&&b[1]==0xF0&&b[2]==0x10&&b.size()==b[3]+5u&&b.back()==sum8(Bytes(b.begin(),b.end()-1)),"SSM reply framing/direction/checksum");return Bytes(b.begin()+4,b.end()-1);}
static Bytes parse_beef(const Bytes& b){need(b.size()>=6&&b.size()<=523&&b[0]==0xBE&&b[1]==0xEF&&b.size()==static_cast<size_t>(b[2]*256+b[3]+5)&&b.back()==sum8(Bytes(b.begin(),b.end()-1)),"BEEF reply framing/length/checksum");return Bytes(b.begin()+4,b.end()-1);}
static Bytes key_for_seed(const Bytes& seed){
 need(seed.size()==4,"Four byte seed");static const unsigned t[]={5,6,7,1,9,12,13,8,10,13,2,11,15,4,0,3,11,4,6,0,15,2,13,9,5,12,1,10,3,13,14,8};
 static const unsigned keys[]={0x88F0,0x6E74,0x6B70,0x3563,0x9D34,0xDBA3,0x503D,0xAFB8,0x3608,0x834F,0x3382,0x7CA3,0x437D,0x72EB,0x33BC,0x53DA};
 unsigned left=seed[0]*256+seed[1],right=seed[2]*256+seed[3];
 for(auto key:keys){unsigned expand=(right^key)*0x10001u,value=0;for(unsigned shift:{0u,4u,8u,12u})value|=t[(expand>>shift)&31]<<shift;value=((value>>3)|(value<<13))&0xFFFF;unsigned old=right;right=left^value;left=old;}
 return {static_cast<unsigned char>(right>>8),static_cast<unsigned char>(right),static_cast<unsigned char>(left>>8),static_cast<unsigned char>(left)};
}
static Bytes read_request(unsigned pass,unsigned address){need(pass<2&&address<0x100000&&address%512==0,"Fixed read range");return beef({3,static_cast<unsigned char>(pass),static_cast<unsigned char>(address>>24),static_cast<unsigned char>(address>>16),static_cast<unsigned char>(address>>8),static_cast<unsigned char>(address),2,0});}
static Bytes raw_reply(const Bytes& wire,unsigned pass,unsigned address){
 Bytes b=parse_beef(wire);need(b.size()==518&&b[0]==0x83&&b[1]==pass&&b[2]==(address>>24)&&b[3]==((address>>16)&255)&&b[4]==((address>>8)&255)&&b[5]==(address&255),"Wrong read reply opcode/pass/address/size");return Bytes(b.begin()+6,b.end());
}
struct Message{unsigned long before[4];PASSTHRU_MSG msg;unsigned long after[4];Message(){memset(this,0,sizeof(*this));for(int i=0;i<4;i++)before[i]=after[i]=0x51A7C0DE;}bool intact()const{for(int i=0;i<4;i++)if(before[i]!=0x51A7C0DE||after[i]!=0x51A7C0DE)return false;return true;}};
static void set(PASSTHRU_MSG& m,const Bytes& b){m={};m.ProtocolID=3;m.DataSize=static_cast<unsigned long>(b.size());memcpy(m.Data,b.data(),b.size());}
static void log_api(const char* fn,unsigned long status,unsigned long count,uintptr_t before,uintptr_t after,const PASSTHRU_MSG* msg){
 std::string wire=msg&&msg->DataSize<=4128?hex(msg->Data,msg->DataSize):"";
 fprintf(journal,"{\"sequence\":%u,\"function\":\"%s\",\"status\":%lu,\"count\":%lu,\"esp_before\":%u,\"esp_after\":%u,\"wire_hex\":\"%s\",\"physical\":false}\n",calls++,fn,status,count,(unsigned)before,(unsigned)after,wire.c_str());
 need(fflush(journal)==0,"Journal flush");need(before==after,"stdcall stack imbalance");need(status==0,"J2534 status failure; no retry");
}
#define FN(name) auto name=reinterpret_cast<PF_##name*>(GetProcAddress(dll,#name));need(name!=nullptr,"Missing exact fake export " #name)
template<class F> __declspec(noinline) static void tracked(const char* name,F call,const unsigned long& count,const PASSTHRU_MSG* msg){
 uintptr_t before=0,after=0;__asm {mov before,esp}
 unsigned long result=call();__asm {mov after,esp}
 log_api(name,result,count,before,after,msg);
}
#define CALL(name,expr,count,msg) tracked(#name,[&](){return (expr);},count,msg)
static int selftest(){
 unsigned n=0;need(key_for_seed({0x12,0x34,0x56,0x78})==Bytes({0xE7,0x8F,0x1F,0x21}),"Seed known vector");n++;
 need(key_for_seed({0,0,0,0})==Bytes({0x2A,0x52,0xF9,0x63}),"Zero seed vector");n++;
 Bytes payload(518,0);payload[0]=0x83;auto good=beef(payload);need(raw_reply(good,0,0).size()==512,"Raw positive");n++;
 for(unsigned i:{0u,2u,3u,4u,5u,6u,9u,522u}){auto bad=good;bad[i]^=1;if(i!=522)bad.back()=sum8(Bytes(bad.begin(),bad.end()-1));bool rejected=false;try{raw_reply(bad,0,0);}catch(...){rejected=true;}need(rejected,"Mutated read accepted");n++;}
 for(unsigned size:{0u,1u,522u,524u}){Bytes bad(size,0);bool rejected=false;try{raw_reply(bad,0,0);}catch(...){rejected=true;}need(rejected,"Bad size accepted");n++;}
 need(read_request(0,0)!=read_request(1,0)&&read_request(0,0)!=read_request(0,512),"Request discrimination");n++;
 Message m;need(m.intact(),"Canary positive");m.after[0]^=1;need(!m.intact(),"Canary mutation");n++;
 printf("PASS %u native offline controls; no DLL/RPC\n",n);return 0;
}
int wmain(int argc,wchar_t** argv){
 HANDLE output[2]={INVALID_HANDLE_VALUE,INVALID_HANDLE_VALUE};
 try{
  if(argc==2&&wcscmp(argv[1],L"--selftest")==0)return selftest();
  need(argc==1,"No provider/kernel/address/opcode arguments accepted");
  // The only DLL path is a compile-time new-project path; no registration search.
  HANDLE locked=CreateFileW(FAKE_DLL_PATH,GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
  need(locked!=INVALID_HANDLE_VALUE,"Fake DLL lock");need(sha_file(locked)==FAKE_DLL_SHA,"Fake DLL hash pin before load");
  HMODULE dll=LoadLibraryExW(FAKE_DLL_PATH,nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_SYSTEM32);need(dll!=nullptr,"Exact fake DLL load");
  FN(PassThruOpen);FN(PassThruConnect);FN(PassThruStartMsgFilter);FN(PassThruWriteMsgs);FN(PassThruReadMsgs);FN(PassThruIoctl);FN(PassThruStopMsgFilter);FN(PassThruDisconnect);FN(PassThruClose);
  wchar_t path[32768];DWORD chars=GetModuleFileNameW(nullptr,path,32768);need(chars&&chars<32768,"Own executable path");std::wstring folder(path);folder.resize(folder.find_last_of(L"\\/"));
  need(_wfopen_s(&journal,(folder+L"\\native_api.jsonl").c_str(),L"wx")==0&&journal,"Exclusive native journal");
  for(unsigned i=0;i<2;i++){auto name=folder+(i?L"\\pass1.partial.bin":L"\\pass0.partial.bin");output[i]=CreateFileW(name.c_str(),GENERIC_WRITE,FILE_SHARE_READ,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);need(output[i]!=INVALID_HANDLE_VALUE,"Exclusive raw partial file");}
  unsigned long device=0,channel=0,filter=0;
  CALL(PassThruOpen,PassThruOpen(nullptr,&device),0,nullptr);need(device==1,"Fixed fake device");
  CALL(PassThruConnect,PassThruConnect(device,3,0x200,4800,&channel),0,nullptr);need(channel==100,"Fixed fake channel");
  auto start_filter=[&](bool kernel){Message mask,pattern;set(mask.msg,kernel?Bytes({0xFF,0xFF}):Bytes({0xFF,0xFF,0xFF}));set(pattern.msg,kernel?Bytes({0xBE,0xEF}):Bytes({0x80,0xF0,0x10}));CALL(PassThruStartMsgFilter,PassThruStartMsgFilter(channel,1,&mask.msg,&pattern.msg,nullptr,&filter),0,nullptr);need(mask.intact()&&pattern.intact()&&filter==1,"Filter ABI");};
  start_filter(false);
  auto exchange=[&](const Bytes& wire){
   Message tx,rx;set(tx.msg,wire);unsigned long count=1;
   CALL(PassThruWriteMsgs,PassThruWriteMsgs(channel,&tx.msg,&count,1000),count,&tx.msg);need(tx.intact()&&count==1,"Exact one TX");
   count=1;CALL(PassThruReadMsgs,PassThruReadMsgs(channel,&rx.msg,&count,1000),count,&rx.msg);need(rx.intact()&&count==1,"Exact one RX");
   need(rx.msg.ProtocolID==3&&rx.msg.RxStatus==0&&rx.msg.TxFlags==0&&rx.msg.DataSize<=523&&rx.msg.ExtraDataIndex==rx.msg.DataSize,"RX metadata");frames++;return Bytes(rx.msg.Data,rx.msg.Data+rx.msg.DataSize);
  };
  auto positive=[&](const Bytes& request,const Bytes& expected){need(parse_ssm(exchange(ssm(request)))==expected,"Exact positive boot response");};
  auto identity=parse_ssm(exchange(ssm({0xBF})));const Bytes id={0x2F,0x12,0x51,0x53,0x06};
  need(identity.size()==57&&Bytes(identity.begin(),identity.begin()+4)==Bytes({0xFF,0xA2,0x10,0x11})&&Bytes(identity.begin()+4,identity.begin()+9)==id,"Fixed ECU2F12515306 identity");
  positive({0x81},{0xC1});positive({0x83,0},{0xC3});
  auto seed=parse_ssm(exchange(ssm({0x27,1})));need(seed.size()==6&&seed[0]==0x67&&seed[1]==1,"Seed reply");
  Bytes key={0x27,2};auto transformed=key_for_seed(Bytes(seed.begin()+2,seed.end()));key.insert(key.end(),transformed.begin(),transformed.end());positive(key,{0x67,2,0x34});
  positive({0x10,0x85,2},{0x50});
  auto baud=[&](unsigned value){SCONFIG config{1,value};SCONFIG_LIST list{1,&config};CALL(PassThruIoctl,PassThruIoctl(channel,2,&list,nullptr),0,nullptr);};
  baud(15625);
  positive({0x34,0xFF,0x30,0,4,static_cast<unsigned char>(KERNEL_SIZE>>16),static_cast<unsigned char>(KERNEL_SIZE>>8),static_cast<unsigned char>(KERNEL_SIZE)},{0x74,0x84});
  for(unsigned offset=0;offset<KERNEL_SIZE;offset+=128){unsigned address=0xFFFF3000u+offset;Bytes body={0x36,static_cast<unsigned char>(address>>16),static_cast<unsigned char>(address>>8),static_cast<unsigned char>(address)};body.insert(body.end(),KERNEL_CIPHER+offset,KERNEL_CIPHER+std::min(offset+128u,KERNEL_SIZE));positive(body,{0x76});}
  positive({0x31,1,1},{0x71,1,1});
  CALL(PassThruStopMsgFilter,PassThruStopMsgFilter(channel,filter),0,nullptr);baud(62500);start_filter(true);
  auto version=parse_beef(exchange(beef({1})));Bytes expected={0x81};expected.insert(expected.end(),KERNEL_VERSION,KERNEL_VERSION+sizeof(KERNEL_VERSION));need(version==expected,"Exact project kernel version");
  Bytes first;first.reserve(0x100000);
  for(unsigned pass=0;pass<2;pass++)for(unsigned address=0;address<0x100000;address+=512){
   auto block=raw_reply(exchange(read_request(pass,address)),pass,address);DWORD wrote=0;
   need(WriteFile(output[pass],block.data(),512,&wrote,nullptr)&&wrote==512&&FlushFileBuffers(output[pass]),"Persist exact partial raw reply");
   if(!pass)first.insert(first.end(),block.begin(),block.end());else need(std::equal(block.begin(),block.end(),first.begin()+address),"Acquisition pass mismatch");
  }
  CALL(PassThruStopMsgFilter,PassThruStopMsgFilter(channel,filter),0,nullptr);CALL(PassThruDisconnect,PassThruDisconnect(channel),0,nullptr);CALL(PassThruClose,PassThruClose(device),0,nullptr);
  for(auto h:output)CloseHandle(h);output[0]=output[1]=INVALID_HANDLE_VALUE;
  fclose(journal);journal=nullptr;FreeLibrary(dll);CloseHandle(locked);
  printf("PASS_NATIVE_FAKE_TWO_FULL_READS frames=%u calls=%u kernel=%s physical=false\n",frames,calls,KERNEL_SHA);return 0;
 }catch(const std::exception& error){
  if(journal){fprintf(journal,"{\"terminal_error\":true,\"frames\":%u,\"calls\":%u}\n",frames,calls);fflush(journal);fclose(journal);}
  for(auto h:output)if(h!=INVALID_HANDLE_VALUE)CloseHandle(h);
  fprintf(stderr,"FAIL_TERMINAL: %s; no further J2534 calls\n",error.what());return 1;
 }
}
