#include <windows.h>
#include "vendor/j2534_tactrix.h"
#include <cstdio>
static_assert(sizeof(PASSTHRU_MSG)==4152,"J2534 x86 layout");
#define FN(name) auto name=reinterpret_cast<PF_##name*>(GetProcAddress(dll,#name));if(!name)return 50
#define REQUIRE(expr) if(!(expr)){printf("failed line %d\n",__LINE__);return __LINE__;}
int main(){
    wchar_t path[32768];REQUIRE(GetEnvironmentVariableW(L"A2WC_FAKE_DLL",path,32768));
    HMODULE dll=LoadLibraryW(path);REQUIRE(dll);
    FN(PassThruOpen);FN(PassThruClose);FN(PassThruConnect);FN(PassThruDisconnect);FN(PassThruReadMsgs);FN(PassThruWriteMsgs);
    FN(PassThruStartPeriodicMsg);FN(PassThruStopPeriodicMsg);FN(PassThruStartMsgFilter);FN(PassThruStopMsgFilter);
    FN(PassThruSetProgrammingVoltage);FN(PassThruReadVersion);FN(PassThruGetLastError);FN(PassThruIoctl);
    unsigned long dev=0,ch=0,id=0;REQUIRE(PassThruOpen("A2WC offline probe",&dev)==0);
    char fw[80],lib[80],api[80];REQUIRE(PassThruReadVersion(dev,fw,lib,api)==0);
    char stress[32];if(GetEnvironmentVariableA("A2WC_RPC_STRESS",stress,sizeof(stress))){
        unsigned long count=strtoul(stress,nullptr,10);REQUIRE(count<=20000);
        for(unsigned long i=0;i<count;i++)REQUIRE(PassThruReadVersion(dev,fw,lib,api)==0);
        printf("PASS %lu sequential RPC messages on persistent loopback connection\n",count);
    }
    REQUIRE(PassThruConnect(dev,ISO9141,ISO9141_NO_CHECKSUM|ISO9141_K_LINE_ONLY,4800,&ch)==0);
    PASSTHRU_MSG mask{},pattern{},tx{},rx{};mask.ProtocolID=pattern.ProtocolID=tx.ProtocolID=ISO9141;mask.DataSize=pattern.DataSize=1;
    REQUIRE(PassThruStartMsgFilter(ch,PASS_FILTER,&mask,&pattern,nullptr,&id)==0);
    unsigned char bf[]={0x80,0x10,0xF0,1,0xBF,0x40};tx.DataSize=sizeof(bf);memcpy(tx.Data,bf,sizeof(bf));unsigned long n=1;
    REQUIRE(PassThruWriteMsgs(ch,&tx,&n,100)==0&&n==1);n=1;
    REQUIRE(PassThruReadMsgs(ch,&rx,&n,100)==0&&n==1&&rx.DataSize==62&&rx.Data[4]==0xFF);
    unsigned long voltage=0;REQUIRE(PassThruIoctl(dev,READ_VBATT,nullptr,&voltage)==0&&voltage==12500);
    REQUIRE(PassThruIoctl(dev,0x70004,nullptr,nullptr)==ERR_NULL_PARAMETER);
    REQUIRE(PassThruSetProgrammingVoltage(dev,12,0)==ERR_NOT_SUPPORTED);
    unsigned long periodic=0;REQUIRE(PassThruStartPeriodicMsg(ch,&tx,&periodic,100)==ERR_NOT_SUPPORTED);
    REQUIRE(PassThruStopPeriodicMsg(ch,99)==ERR_NOT_SUPPORTED);
    char error[80];REQUIRE(PassThruGetLastError(error)==0);
    REQUIRE(PassThruStopMsgFilter(ch,id)==0);REQUIRE(PassThruDisconnect(ch)==0);REQUIRE(PassThruClose(dev)==0);
    puts("PASS all14 fake J2534 entrypoints; BF exact62-byte response; unsupported visibly rejected");return 0;
}
