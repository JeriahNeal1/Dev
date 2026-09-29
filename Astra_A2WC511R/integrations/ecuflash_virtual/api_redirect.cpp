// Explicit instrumentation fallback for this exact installed ECUFlash image.
// Built-in targets use cdecl; the separately named fake DLL exports stdcall.
namespace api_redirect {
using U=unsigned long;
static FARPROC fake[14]{};
static LONG CALLBACK exceptionTrace(PEXCEPTION_POINTERS p){
    wchar_t line[1024];DWORD stack[12]{};SIZE_T count=0;ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(p->ContextRecord->Esp),stack,sizeof(stack),&count);
    swprintf_s(line,L"code=%08lX eip=%08lX esp=%08lX eax=%08lX ecx=%08lX edx=%08lX stack=%08lX,%08lX,%08lX,%08lX,%08lX,%08lX,%08lX,%08lX",
        p->ExceptionRecord->ExceptionCode,p->ContextRecord->Eip,p->ContextRecord->Esp,p->ContextRecord->Eax,p->ContextRecord->Ecx,p->ContextRecord->Edx,stack[0],stack[1],stack[2],stack[3],stack[4],stack[5],stack[6],stack[7]);
    log("FIRST_CHANCE_EXCEPTION",line);return EXCEPTION_CONTINUE_SEARCH;
}
extern "C" long __cdecl bridgeOpen(const void*n,U*i){return reinterpret_cast<long(__stdcall*)(const void*,U*)>(fake[0])(n,i);}
extern "C" long __cdecl bridgeClose(U d){return reinterpret_cast<long(__stdcall*)(U)>(fake[1])(d);}
extern "C" long __cdecl bridgeConnect(U d,U p,U f,U b,U*c){return reinterpret_cast<long(__stdcall*)(U,U,U,U,U*)>(fake[2])(d,p,f,b,c);}
extern "C" long __cdecl bridgeDisconnect(U c){return reinterpret_cast<long(__stdcall*)(U)>(fake[3])(c);}
extern "C" long __cdecl bridgeRead(U c,void*m,U*n,U t){return reinterpret_cast<long(__stdcall*)(U,void*,U*,U)>(fake[4])(c,m,n,t);}
extern "C" long __cdecl bridgeWrite(U c,const void*m,U*n,U t){return reinterpret_cast<long(__stdcall*)(U,const void*,U*,U)>(fake[5])(c,m,n,t);}
extern "C" long __cdecl bridgeStartPeriodic(U c,const void*m,U*i,U t){return reinterpret_cast<long(__stdcall*)(U,const void*,U*,U)>(fake[6])(c,m,i,t);}
extern "C" long __cdecl bridgeStopPeriodic(U c,U i){return reinterpret_cast<long(__stdcall*)(U,U)>(fake[7])(c,i);}
extern "C" long __cdecl bridgeStartFilter(U c,U t,const void*m,const void*p,const void*f,U*i){return reinterpret_cast<long(__stdcall*)(U,U,const void*,const void*,const void*,U*)>(fake[8])(c,t,m,p,f,i);}
extern "C" long __cdecl bridgeStopFilter(U c,U i){return reinterpret_cast<long(__stdcall*)(U,U)>(fake[9])(c,i);}
extern "C" long __cdecl bridgeVoltage(U d,U p,U v){return reinterpret_cast<long(__stdcall*)(U,U,U)>(fake[10])(d,p,v);}
extern "C" long __cdecl bridgeVersion(U d,char*f,char*l,char*a){return reinterpret_cast<long(__stdcall*)(U,char*,char*,char*)>(fake[11])(d,f,l,a);}
extern "C" long __cdecl bridgeError(char*e){return reinterpret_cast<long(__stdcall*)(char*)>(fake[12])(e);}
extern "C" long __cdecl bridgeIoctl(U d,U o,const void*i,void*r){return reinterpret_cast<long(__stdcall*)(U,U,const void*,void*)>(fake[13])(d,o,i,r);}
struct Site{const char*name;U rva;void*bridge;const char*prefix;int relocation;void*original;};
static Site sites[]={
 {"PassThruOpen",0x1233E0,bridgeOpen,"f6051423a80101568b74240c578b7c24",2},
 {"PassThruClose",0x122AF0,bridgeClose,"f6051423a80101568b742408740e5668",2},
 {"PassThruConnect",0x122B40,bridgeConnect,"f6051423a801018b442404568b742414",2},
 {"PassThruDisconnect",0x122BB0,bridgeDisconnect,"f6051423a80101568b742408740e5668",2},
 {"PassThruReadMsgs",0x123430,bridgeRead,"a01423a801538b5c2410558b6c240c56",1},
 {"PassThruWriteMsgs",0x123A50,bridgeWrite,"83ec148d4424045355565033dbe87e78",-1},
 {"PassThruStartPeriodicMsg",0x1238B0,bridgeStartPeriodic,"51f6051423a80101568b742410578b7c",3},
 {"PassThruStopPeriodicMsg",0x1239E0,bridgeStopPeriodic,"51f6051423a80101568b742410741256",3},
 {"PassThruStartMsgFilter",0x123730,bridgeStartFilter,"51f6051423a801018b442408538b5c24",3},
 {"PassThruStopMsgFilter",0x123970,bridgeStopFilter,"51f6051423a80101568b742410741256",3},
 {"PassThruSetProgrammingVoltage",0x1236B0,bridgeVoltage,"51f6051423a80101568b742414741656",3},
 {"PassThruReadVersion",0x123550,bridgeVersion,"518b442408538b5c2418558b6c241456",-1},
 {"PassThruGetLastError",0x122C00,bridgeError,"83ec10a1c04ba70133c48944240cf605",4},
 {"PassThruIoctl",0x122CE0,bridgeIoctl,"81ecb4000000a1c04ba70133c4898424",7}
};
static int nibble(char c){return c<='9'?c-'0':c-'a'+10;}
DWORD install(){
    static bool installed=false;if(installed)return 201;
    auto base=reinterpret_cast<unsigned char*>(GetModuleHandleW(nullptr));
    for(auto&s:sites){
        unsigned char expected[32]{};size_t length=strlen(s.prefix)/2;
        for(size_t n=0;n<length;n++)expected[n]=static_cast<unsigned char>(nibble(s.prefix[n*2])*16+nibble(s.prefix[n*2+1]));
        if(s.relocation>=0)*reinterpret_cast<DWORD*>(expected+s.relocation)+=static_cast<DWORD>(reinterpret_cast<uintptr_t>(base))-0xE80000;
        if(memcmp(base+s.rva,expected,length)){log("API_PREFIX_MISMATCH",widen(s.name));return 202;}
        s.original=base+s.rva;
    }
    HMODULE dll=LoadLibraryW(allowedFake.c_str());if(!dll)return 203;
    for(int i=0;i<14;i++){fake[i]=GetProcAddress(dll,sites[i].name);if(!fake[i])return 204;}
    LONG error=DetourTransactionBegin();if(error)return 205;
    HANDLE snapshot=CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD,0);THREADENTRY32 te{};te.dwSize=sizeof(te);
    std::vector<HANDLE> handles;
    if(snapshot==INVALID_HANDLE_VALUE){DetourTransactionAbort();return 206;}
    if(Thread32First(snapshot,&te))do{
        if(te.th32OwnerProcessID!=GetCurrentProcessId()||te.th32ThreadID==GetCurrentThreadId())continue;
        HANDLE h=OpenThread(THREAD_SUSPEND_RESUME|THREAD_GET_CONTEXT|THREAD_SET_CONTEXT|THREAD_QUERY_INFORMATION,FALSE,te.th32ThreadID);
        if(!h){error=1;break;}handles.push_back(h);if(DetourUpdateThread(h)){error=1;break;}
    }while(Thread32Next(snapshot,&te));
    CloseHandle(snapshot);
    if(!error)for(auto&s:sites)if(DetourAttach(&s.original,s.bridge)){error=1;break;}
    if(error)DetourTransactionAbort();else error=DetourTransactionCommit();
    for(auto h:handles)CloseHandle(h);
    if(error)return 207;
    AddVectoredExceptionHandler(1,exceptionTrace);
    installed=true;log("INSTRUMENTED_BUILTIN_J2534_READY",L"14 cdecl bridges -> separately named stdcall fake DLL; not normal registry discovery");return 0;
}
}
extern "C" DWORD WINAPI A2WCInstallApi(LPVOID){return api_redirect::install();}
