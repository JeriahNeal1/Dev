// Fixed-observation worker. There is no input field for bus bytes or addresses.
#include "j2534_abi.h"
#include <bcrypt.h>
#include <algorithm>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
#include <fstream>
#include <iterator>
#include <io.h>
#include <fcntl.h>
#pragma comment(lib,"bcrypt.lib")
const std::vector<unsigned char> IDENTITY{0x80,0x10,0xf0,1,0xbf,0x40};
const std::vector<unsigned char> SNAPSHOT{0x80,0x10,0xf0,0x14,0xa8,0,0xff,0x4c,0x75,0xff,0x4c,0x8d,0xff,0x4c,0xa1,0xff,0x4c,0x50,0xff,0x4b,0xc1,0xff,0x4b,0xc2,0x72};
enum class Op { Invalid, Identity, Snapshot, Close };
Op parse(const std::string& s) {
    if(s=="IDENTITY") return Op::Identity;
    if(s=="SNAPSHOT") return Op::Snapshot;
    if(s=="CLOSE") return Op::Close;
    return Op::Invalid;
}
std::string hex(const unsigned char *p, size_t n) {
    std::string s; const char *h="0123456789abcdef";
    for(size_t i=0;i<n;i++){s+=h[p[i]>>4];s+=h[p[i]&15];} return s;
}
std::string sha_file(const wchar_t *path) {
    std::ifstream f(path,std::ios::binary); if(!f) throw std::runtime_error("provider read failed");
    std::vector<unsigned char> data((std::istreambuf_iterator<char>(f)),{});
    BCRYPT_ALG_HANDLE alg=nullptr; BCRYPT_HASH_HANDLE h=nullptr; unsigned char digest[32];
    if(BCryptOpenAlgorithmProvider(&alg,BCRYPT_SHA256_ALGORITHM,nullptr,0)<0) throw std::runtime_error("hash provider");
    NTSTATUS a=BCryptCreateHash(alg,&h,nullptr,0,nullptr,0,0);
    NTSTATUS b=a<0?a:BCryptHashData(h,data.data(),static_cast<ULONG>(data.size()),0);
    NTSTATUS c=b<0?b:BCryptFinishHash(h,digest,32,0);
    if(h) BCryptDestroyHash(h); BCryptCloseAlgorithmProvider(alg,0);
    if(c<0) throw std::runtime_error("provider hash failed"); return hex(digest,32);
}
struct Device {
    HMODULE dll=nullptr; U device=0,channel=0,filter=0; bool opened=false,connected=false,filtered=false;
    bool cleanup_good=true;
    Open open=nullptr; Close close=nullptr,disconnect=nullptr; Connect connect=nullptr;
    Messages write=nullptr,read=nullptr; Ioctl ioctl=nullptr; Filter start=nullptr; StopFilter stop=nullptr;
    template<class T> T symbol(const char *name) {
        auto p=GetProcAddress(dll,name); if(!p) throw std::runtime_error(std::string("missing export ")+name);
        return reinterpret_cast<T>(p);
    }
    static void check(long result,const char* operation) {
        if(result) throw std::runtime_error(std::string(operation)+" status "+std::to_string(result));
    }
    void init(bool fake) {
        wchar_t self[32768]; if(!GetModuleFileNameW(nullptr,self,32768)) throw std::runtime_error("exe path");
        std::wstring path(self); path=path.substr(0,path.find_last_of(L"\\/")+1)+L"fake_j2534.dll";
        if(!fake) {
            path=L"C:\\Windows\\SysWOW64\\op20pt32.dll";
            if(sha_file(path.c_str())!="f432084801762d919a3c31974616e097562424470003edc4f4fb843df34103cf")
                throw std::runtime_error("installed provider hash differs");
        }
        dll=LoadLibraryExW(path.c_str(),nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_SYSTEM32);
        if(!dll) throw std::runtime_error("provider load failed");
        // Only these exports are reachable. No programming voltage, periodic message or init APIs.
        open=symbol<Open>("PassThruOpen"); close=symbol<Close>("PassThruClose");
        connect=symbol<Connect>("PassThruConnect"); disconnect=symbol<Close>("PassThruDisconnect");
        write=symbol<Messages>("PassThruWriteMsgs"); read=symbol<Messages>("PassThruReadMsgs");
        ioctl=symbol<Ioctl>("PassThruIoctl"); start=symbol<Filter>("PassThruStartMsgFilter"); stop=symbol<StopFilter>("PassThruStopMsgFilter");
        check(open(nullptr,&device),"open"); opened=true;
        check(connect(device,3,0x200,4800,&channel),"connect"); connected=true;
        Config items[]={{7,1},{10,1},{12,0},{3,1},{32,0},{22,0}}; ConfigList list{6,items};
        check(ioctl(channel,2,&list,nullptr),"fixed SET_CONFIG");
        Msg mask{}, pattern{}; mask.protocol=pattern.protocol=3; mask.size=pattern.size=1;
        check(start(channel,1,&mask,&pattern,nullptr,&filter),"pass filter"); filtered=true;
    }
    bool cleanup() {
        bool good=cleanup_good;
        if(filtered){good=(stop(channel,filter)==0)&&good;filtered=false;}
        if(connected){good=(disconnect(channel)==0)&&good;connected=false;}
        if(opened){good=(close(device)==0)&&good;opened=false;}
        if(dll){FreeLibrary(dll);dll=nullptr;} cleanup_good=good; return good;
    }
    ~Device(){cleanup();}
    void exchange(Op op) {
        if(op!=Op::Identity && op!=Op::Snapshot) throw std::runtime_error("nonread operation rejected");
        const auto& q=op==Op::Identity?IDENTITY:SNAPSHOT;
        Msg tx{}; tx.protocol=3; tx.size=static_cast<U>(q.size()); std::copy(q.begin(),q.end(),tx.data);
        // Last boundary guard operates on the actual ABI message, not the caller's claim.
        if(tx.protocol!=3 || tx.tx || tx.rx || tx.extra || tx.timestamp ||
            tx.size!=q.size() || std::memcmp(tx.data,q.data(),q.size())) throw std::runtime_error("wire guard");
        std::cerr<<"TX host_tick_ms="<<GetTickCount64()<<" raw="<<hex(tx.data,tx.size)<<"\n";
        U n=1; check(write(channel,&tx,&n,1000),"fixed diagnostic TX"); if(n!=1) throw std::runtime_error("short TX");
        const size_t reply_size=op==Op::Identity?62:12;
        std::vector<unsigned char> wire; std::string events="["; bool first=true;
        ULONGLONG deadline=GetTickCount64()+1200;
        while(wire.size()<q.size()+reply_size) {
            if(GetTickCount64()>=deadline) throw std::runtime_error("RX deadline");
            Msg rx{}; n=1; long result=read(channel,&rx,&n,100);
            if((result==0x10 || result==9) && n==0) continue;
            check(result,"read");
            std::cerr<<"RX host_tick_ms="<<GetTickCount64()<<" provider_us="<<rx.timestamp<<" rx_status="<<rx.rx
                <<" declared_size="<<rx.size<<" raw="<<hex(rx.data,std::min(rx.size,4128U))<<"\n";
            if(n!=1 || rx.protocol!=3 || rx.size==0 || rx.size>4128 || rx.extra>rx.size || rx.tx!=0 ||
                (rx.extra && rx.extra!=rx.size) || (rx.rx & ~1U)) throw std::runtime_error("unsupported RX metadata");
            if(wire.size()+rx.size>q.size()+reply_size) throw std::runtime_error("extra RX bytes");
            if(!first) events+=",";first=false;
            events+="{\"timestamp_us\":"+std::to_string(rx.timestamp)+",\"rx_status\":"+std::to_string(rx.rx)+",\"raw_hex\":\""+hex(rx.data,rx.size)+"\"}";
            wire.insert(wire.end(),rx.data,rx.data+rx.size);
        }
        events+="]";
        if(!std::equal(q.begin(),q.end(),wire.begin())) throw std::runtime_error("missing or different exact echo");
        const unsigned char *r=wire.data()+q.size(); U sum=0;
        for(size_t i=0;i<reply_size-1;i++) sum+=r[i];
        if(r[0]!=0x80 || r[1]!=0xf0 || r[2]!=0x10 || r[3]!=reply_size-5 ||
            r[4]!=(op==Op::Identity?0xff:0xe8) || (sum&255)!=r[reply_size-1]) throw std::runtime_error("response framing");
        const unsigned char ecuid[]={0x2f,0x12,0x51,0x53,0x06};
        if(op==Op::Identity && std::memcmp(r+8,ecuid,5)) throw std::runtime_error("unexpected ECU ID");
        std::cout<<"{\"type\":\"exchange\",\"operation\":\""<<(op==Op::Identity?"IDENTITY":"SNAPSHOT")<<"\",\"wire_hex\":\""<<hex(wire.data(),wire.size())<<"\",\"provider_frames\":"<<events<<"}"<<std::endl;
    }
};
int policy_test() {
    size_t rejected=0;
    for(auto original: {std::string("IDENTITY"),std::string("SNAPSHOT"),std::string("CLOSE")}) {
        for(size_t i=0;i<original.size();i++) for(unsigned v=0;v<256;v++) {
            auto s=original;s[i]=static_cast<char>(v);if(s==original)continue;
            if(parse(s)!=Op::Invalid)return 1;rejected++;
        }
        for(size_t i=0;i<=original.size();i++) for(unsigned v=0;v<256;v++) {
            auto s=original;s.insert(i,1,static_cast<char>(v));if(parse(s)!=Op::Invalid)return 2;rejected++;
        }
        for(size_t i=0;i<original.size();i++){auto s=original;s.erase(i,1);if(parse(s)!=Op::Invalid)return 3;rejected++;}
    }
    std::cout<<"{\"status\":\"PASS\",\"single_byte_token_mutations_rejected\":"<<rejected<<"}"<<std::endl;return 0;
}
int main(int argc,char** argv) {
    _setmode(_fileno(stdin),_O_BINARY); _setmode(_fileno(stdout),_O_BINARY);
    if(argc==2 && std::string(argv[1])=="--policy-selftest") return policy_test();
    if(argc!=2 || (std::string(argv[1])!="--fake" && std::string(argv[1])!="--physical-read-only")) return 2;
    bool fake=std::string(argv[1])=="--fake", identified=false; Device device;
    std::cout<<"{\"type\":\"ready\",\"fake\":"<<(fake?"true":"false")<<",\"provider_loaded\":false}"<<std::endl;
    try {
        while(true) {
            std::string line; int c;
            while((c=std::cin.get())!=EOF && c!='\n') {if(line.size()>=16)throw std::runtime_error("oversized operation");line+=static_cast<char>(c);}
            if(c==EOF) {if(!line.empty())throw std::runtime_error("unterminated operation");break;}
            Op op=parse(line); if(op==Op::Invalid) throw std::runtime_error("operation rejected");
            if(op==Op::Close) break;
            if(!identified) {if(op!=Op::Identity)throw std::runtime_error("identity required");device.init(fake);device.exchange(op);identified=true;}
            else {if(op!=Op::Snapshot)throw std::runtime_error("identity cannot be repeated");device.exchange(op);}
        }
        if(!device.cleanup())throw std::runtime_error("cleanup failed");
        std::cout<<"{\"type\":\"closed\"}"<<std::endl;return 0;
    } catch(const std::exception& e) {
        bool clean=device.cleanup(); std::cerr<<e.what()<<"\n";
        std::cout<<"{\"type\":\"terminal_failure\",\"cleanup_ok\":"<<(clean?"true":"false")<<"}"<<std::endl;return 1;
    }
}
