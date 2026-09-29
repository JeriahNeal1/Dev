#define NOMINMAX
#include <windows.h>
#include <winternl.h>
#include <shlobj.h>
#pragma comment(lib,"shell32.lib")
#pragma comment(lib,"ole32.lib")
#pragma comment(lib,"uuid.lib")
#include <detours.h>
#include <string>
#include <algorithm>
#include <cstdio>
#include <cstdint>
#include <vector>
#include <tlhelp32.h>
static HANDLE logFile=INVALID_HANDLE_VALUE;
static std::wstring allowedFake;
using LdrLoad = NTSTATUS (NTAPI *)(PWSTR,ULONG*,PUNICODE_STRING,PHANDLE);
static LdrLoad realLdr=nullptr;
using NtCreate = NTSTATUS (NTAPI *)(PHANDLE,ACCESS_MASK,POBJECT_ATTRIBUTES,PIO_STATUS_BLOCK,PLARGE_INTEGER,ULONG,ULONG,ULONG,ULONG,PVOID,ULONG);
static NtCreate realNtCreate=nullptr;
static decltype(&CreateFileW) realCreateW=CreateFileW;
static decltype(&CreateFileA) realCreateA=CreateFileA;
static std::wstring virtualRoot;
static std::wstring privateAppData;
static decltype(&SHGetFolderPathW) realFolderW=SHGetFolderPathW;
static decltype(&SHGetFolderPathA) realFolderA=SHGetFolderPathA;
static decltype(&SHGetKnownFolderPath) realKnownFolder=SHGetKnownFolderPath;
static decltype(&SHGetSpecialFolderPathW) realSpecialW=SHGetSpecialFolderPathW;
static decltype(&SHGetSpecialFolderPathA) realSpecialA=SHGetSpecialFolderPathA;
static decltype(&RegOpenKeyExW) realRegOpenW=RegOpenKeyExW;
static decltype(&RegOpenKeyExA) realRegOpenA=RegOpenKeyExA;
static decltype(&RegCreateKeyExW) realRegCreateW=RegCreateKeyExW;
static decltype(&RegCreateKeyExA) realRegCreateA=RegCreateKeyExA;
static std::wstring lower(std::wstring s){std::transform(s.begin(),s.end(),s.begin(),::towlower);return s;}
static void log(const char* kind,const std::wstring& value){
    if(logFile==INVALID_HANDLE_VALUE)return;
    char text[4096];SYSTEMTIME t;GetSystemTime(&t);
    int n=snprintf(text,sizeof(text),"%04u-%02u-%02uT%02u:%02u:%02u.%03uZ tick=%llu thread=%lu %s ",t.wYear,t.wMonth,t.wDay,t.wHour,t.wMinute,t.wSecond,t.wMilliseconds,GetTickCount64(),GetCurrentThreadId(),kind);
    int m=WideCharToMultiByte(CP_UTF8,0,value.c_str(),static_cast<int>(value.size()),text+n,static_cast<int>(sizeof(text))-n-2,nullptr,nullptr);
    if(m<0)m=0;text[n+m++]='\n';DWORD done;WriteFile(logFile,text,n+m,&done,nullptr);FlushFileBuffers(logFile);
}
static bool providerDenied(const std::wstring& path){
    auto s=lower(path);if(s==lower(allowedFake))return false;
    auto sep=s.find_last_of(L"\\/");auto name=s.substr(sep==std::wstring::npos?0:sep+1);
    return name.find(L"op20")!=std::wstring::npos || name.find(L"op10")!=std::wstring::npos ||
           name.find(L"ftd2xx")!=std::wstring::npos || name.find(L"j2534")!=std::wstring::npos;
}
static NTSTATUS NTAPI guardedLdr(PWSTR path,ULONG* flags,PUNICODE_STRING name,PHANDLE handle){
    std::wstring s=name&&name->Buffer?std::wstring(name->Buffer,name->Length/2):L"";
    if(providerDenied(s)){log("DENIED_PROVIDER_LOAD",s);if(handle)*handle=nullptr;return static_cast<NTSTATUS>(0xC0000022);}
    NTSTATUS status=realLdr(path,flags,name,handle);log(status>=0?"DLL_LOADED":"DLL_LOAD_FAILED",s);return status;
}
static bool deviceDenied(const std::wstring& path){
    auto s=lower(path);
    return s.rfind(L"\\\\.\\",0)==0 || s.rfind(L"\\\\?\\usb",0)==0 ||
        s.rfind(L"\\device\\",0)==0 || (s.rfind(L"com",0)==0&&s.size()>3&&iswdigit(s[3]));
}
static NTSTATUS NTAPI guardedNtCreate(PHANDLE h,ACCESS_MASK a,POBJECT_ATTRIBUTES o,PIO_STATUS_BLOCK io,PLARGE_INTEGER size,ULONG attr,ULONG share,ULONG disp,ULONG options,PVOID ea,ULONG ealen){
    std::wstring s=o&&o->ObjectName&&o->ObjectName->Buffer?std::wstring(o->ObjectName->Buffer,o->ObjectName->Length/2):L"";
    auto p=lower(s);
    bool deny=p.find(L"usb#")!=std::wstring::npos || p.find(L"ftdibus")!=std::wstring::npos || p.find(L"ftser")!=std::wstring::npos ||
        p.rfind(L"\\??\\com",0)==0 || p.rfind(L"\\device\\serial",0)==0 || p.rfind(L"\\device\\vcp",0)==0;
    if(deny){log("DENIED_NT_DEVICE_OPEN",s);if(h)*h=nullptr;return static_cast<NTSTATUS>(0xC0000022);}
    return realNtCreate(h,a,o,io,size,attr,share,disp,options,ea,ealen);
}
static HANDLE WINAPI guardedCreateW(LPCWSTR p,DWORD a,DWORD b,LPSECURITY_ATTRIBUTES c,DWORD d,DWORD e,HANDLE f){
    if(p&&deviceDenied(p)){log("DENIED_DEVICE_OPEN",p);SetLastError(ERROR_ACCESS_DENIED);return INVALID_HANDLE_VALUE;}
    return realCreateW(p,a,b,c,d,e,f);
}
static HANDLE WINAPI guardedCreateA(LPCSTR p,DWORD a,DWORD b,LPSECURITY_ATTRIBUTES c,DWORD d,DWORD e,HANDLE f){
    std::wstring w;if(p){int n=MultiByteToWideChar(CP_ACP,0,p,-1,nullptr,0);w.resize(n);MultiByteToWideChar(CP_ACP,0,p,-1,w.data(),n);w.resize(n-1);}
    if(deviceDenied(w)){log("DENIED_DEVICE_OPEN",w);SetLastError(ERROR_ACCESS_DENIED);return INVALID_HANDLE_VALUE;}
    return realCreateA(p,a,b,c,d,e,f);
}
static std::wstring env(const wchar_t* name){wchar_t b[32768];DWORD n=GetEnvironmentVariableW(name,b,32768);if(!n||n>=32768)ExitProcess(180);return std::wstring(b,n);}
static HRESULT WINAPI guardedFolderW(HWND h,int folder,HANDLE token,DWORD flags,LPWSTR path){
    int id=folder&0xff;if(id==CSIDL_APPDATA||id==CSIDL_LOCAL_APPDATA){
        auto s=privateAppData+(id==CSIDL_APPDATA?L"\\Roaming":L"\\Local");if(s.size()>=MAX_PATH)return E_FAIL;
        wcscpy_s(path,MAX_PATH,s.c_str());log("APPDATA_REDIRECT",s);return S_OK;
    }return realFolderW(h,folder,token,flags,path);
}
static HRESULT WINAPI guardedFolderA(HWND h,int folder,HANDLE token,DWORD flags,LPSTR path){
    int id=folder&0xff;if(id==CSIDL_APPDATA||id==CSIDL_LOCAL_APPDATA){wchar_t w[MAX_PATH];auto status=guardedFolderW(h,folder,token,flags,w);if(FAILED(status))return status;
        if(!WideCharToMultiByte(CP_ACP,0,w,-1,path,MAX_PATH,nullptr,nullptr))return E_FAIL;return S_OK;
    }return realFolderA(h,folder,token,flags,path);
}
static HRESULT WINAPI guardedKnownFolder(REFKNOWNFOLDERID folder,DWORD flags,HANDLE token,PWSTR*path){
    if(IsEqualGUID(folder,FOLDERID_RoamingAppData)||IsEqualGUID(folder,FOLDERID_LocalAppData)){
        auto s=privateAppData+(IsEqualGUID(folder,FOLDERID_RoamingAppData)?L"\\Roaming":L"\\Local");
        *path=static_cast<PWSTR>(CoTaskMemAlloc((s.size()+1)*sizeof(wchar_t)));if(!*path)return E_OUTOFMEMORY;
        wcscpy_s(*path,s.size()+1,s.c_str());log("APPDATA_REDIRECT",s);return S_OK;
    }return realKnownFolder(folder,flags,token,path);
}
static BOOL WINAPI guardedSpecialW(HWND h,LPWSTR path,int folder,BOOL create){
    if(folder==CSIDL_APPDATA||folder==CSIDL_LOCAL_APPDATA)return SUCCEEDED(guardedFolderW(h,folder,nullptr,0,path));
    return realSpecialW(h,path,folder,create);
}
static BOOL WINAPI guardedSpecialA(HWND h,LPSTR path,int folder,BOOL create){
    if(folder==CSIDL_APPDATA||folder==CSIDL_LOCAL_APPDATA)return SUCCEEDED(guardedFolderA(h,folder,nullptr,0,path));
    return realSpecialA(h,path,folder,create);
}
static std::wstring widen(const char*p){
    if(!p)return L"";int n=MultiByteToWideChar(CP_ACP,0,p,-1,nullptr,0);std::wstring w(n,0);MultiByteToWideChar(CP_ACP,0,p,-1,w.data(),n);w.resize(n-1);return w;
}
static bool regRoute(HKEY root,const std::wstring& sub,std::wstring& target){
    auto s=lower(sub);
    bool machine=root==HKEY_LOCAL_MACHINE&&(s.rfind(L"software\\passthrusupport.",0)==0||s.rfind(L"software\\wow6432node\\passthrusupport.",0)==0);
    bool user=root==HKEY_CURRENT_USER&&(s==L"software\\openecu"||s.rfind(L"software\\openecu\\",0)==0||s==L"software\\a2wcisolationprobe");
    if(!machine&&!user)return false;
    target=virtualRoot+(machine?L"\\Machine\\":L"\\User\\")+sub;log("REGISTRY_REDIRECT",sub);return true;
}
static LSTATUS WINAPI guardedRegOpenW(HKEY h,LPCWSTR sub,DWORD opt,REGSAM sam,PHKEY out){
    std::wstring target;if(regRoute(h,sub?sub:L"",target))return realRegOpenW(HKEY_CURRENT_USER,target.c_str(),opt,sam&~(KEY_WOW64_32KEY|KEY_WOW64_64KEY),out);
    return realRegOpenW(h,sub,opt,sam,out);
}
static LSTATUS WINAPI guardedRegOpenA(HKEY h,LPCSTR sub,DWORD opt,REGSAM sam,PHKEY out){
    std::wstring target;if(regRoute(h,widen(sub),target))return realRegOpenW(HKEY_CURRENT_USER,target.c_str(),opt,sam&~(KEY_WOW64_32KEY|KEY_WOW64_64KEY),out);
    return realRegOpenA(h,sub,opt,sam,out);
}
static LSTATUS WINAPI guardedRegCreateW(HKEY h,LPCWSTR sub,DWORD reserved,LPWSTR cls,DWORD opt,REGSAM sam,const LPSECURITY_ATTRIBUTES sa,PHKEY out,LPDWORD disp){
    std::wstring target;if(regRoute(h,sub?sub:L"",target))return realRegCreateW(HKEY_CURRENT_USER,target.c_str(),reserved,cls,opt,sam&~(KEY_WOW64_32KEY|KEY_WOW64_64KEY),sa,out,disp);
    return realRegCreateW(h,sub,reserved,cls,opt,sam,sa,out,disp);
}
static LSTATUS WINAPI guardedRegCreateA(HKEY h,LPCSTR sub,DWORD reserved,LPSTR cls,DWORD opt,REGSAM sam,const LPSECURITY_ATTRIBUTES sa,PHKEY out,LPDWORD disp){
    std::wstring target;if(regRoute(h,widen(sub),target)){auto wcls=widen(cls);return realRegCreateW(HKEY_CURRENT_USER,target.c_str(),reserved,cls?wcls.data():nullptr,opt,sam&~(KEY_WOW64_32KEY|KEY_WOW64_64KEY),sa,out,disp);}
    return realRegCreateA(h,sub,reserved,cls,opt,sam,sa,out,disp);
}
BOOL WINAPI DllMain(HINSTANCE,DWORD reason,LPVOID){
    if(DetourIsHelperProcess())return TRUE;
    if(reason==DLL_PROCESS_ATTACH){
        DetourRestoreAfterWith();
        auto logfile=env(L"A2WC_GUARD_LOG");allowedFake=env(L"A2WC_FAKE_DLL");
        logFile=CreateFileW(logfile.c_str(),GENERIC_WRITE,FILE_SHARE_READ|FILE_SHARE_WRITE,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
        if(logFile==INVALID_HANDLE_VALUE)ExitProcess(181);
        virtualRoot=env(L"A2WC_VREG");
        privateAppData=env(L"A2WC_APPDATA");
        if(virtualRoot.rfind(L"Software\\A2WC511R_VirtualRead\\",0)!=0)ExitProcess(182);
        realLdr=reinterpret_cast<LdrLoad>(GetProcAddress(GetModuleHandleW(L"ntdll.dll"),"LdrLoadDll"));
        realNtCreate=reinterpret_cast<NtCreate>(GetProcAddress(GetModuleHandleW(L"ntdll.dll"),"NtCreateFile"));
        if(!realLdr||!realNtCreate)ExitProcess(185);
        DetourTransactionBegin();DetourUpdateThread(GetCurrentThread());
        LONG a=DetourAttach(&(PVOID&)realLdr,guardedLdr);
        LONG b=DetourAttach(&(PVOID&)realCreateW,guardedCreateW);
        LONG c=DetourAttach(&(PVOID&)realCreateA,guardedCreateA);
        LONG d=DetourAttach(&(PVOID&)realNtCreate,guardedNtCreate);
        LONG e=DetourAttach(&(PVOID&)realRegOpenW,guardedRegOpenW);
        LONG f=DetourAttach(&(PVOID&)realRegOpenA,guardedRegOpenA);
        LONG g=DetourAttach(&(PVOID&)realRegCreateW,guardedRegCreateW);
        LONG h=DetourAttach(&(PVOID&)realRegCreateA,guardedRegCreateA);
        LONG i=DetourAttach(&(PVOID&)realFolderW,guardedFolderW);
        LONG j=DetourAttach(&(PVOID&)realFolderA,guardedFolderA);
        LONG k=DetourAttach(&(PVOID&)realKnownFolder,guardedKnownFolder);
        LONG l=DetourAttach(&(PVOID&)realSpecialW,guardedSpecialW);
        LONG m=DetourAttach(&(PVOID&)realSpecialA,guardedSpecialA);
        LONG result=DetourTransactionCommit();
        if(a||b||c||d||e||f||g||h||i||j||k||l||m||result)ExitProcess(186);
        log("ISOLATION_READY",virtualRoot);
    }
    return TRUE;
}
#include "api_redirect.cpp"
