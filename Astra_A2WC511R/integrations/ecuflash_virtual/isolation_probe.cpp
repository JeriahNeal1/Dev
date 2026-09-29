#include <windows.h>
#include <cstdio>
#include <initializer_list>
#include <shlobj.h>
#pragma comment(lib,"shell32.lib")
int main(){
    const DWORD views[]={0,KEY_WOW64_32KEY,KEY_WOW64_64KEY};
    for(DWORD view : views){
    HKEY key;LONG r=RegOpenKeyExW(HKEY_LOCAL_MACHINE,L"SOFTWARE\\PassThruSupport.04.04",0,KEY_READ|view,&key);
    if(r)return 20;
    DWORD count=0;RegQueryInfoKeyW(key,nullptr,nullptr,nullptr,&count,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr);
    if(count!=1)return 21;wchar_t name[256];DWORD n=256;RegEnumKeyExW(key,0,name,&n,nullptr,nullptr,nullptr,nullptr);
    if(wcscmp(name,L"A2WC511R Virtual ECU"))return 22;RegCloseKey(key);
    }
    HKEY user;DWORD disposition;
    if(RegCreateKeyExW(HKEY_CURRENT_USER,L"Software\\A2WCIsolationProbe",0,nullptr,0,KEY_ALL_ACCESS,nullptr,&user,&disposition))return 25;
    const DWORD value=0x511;
    if(RegSetValueExW(user,L"marker",0,REG_DWORD,reinterpret_cast<const BYTE*>(&value),sizeof(value)))return 26;
    RegCloseKey(user);
    wchar_t appdata[MAX_PATH],expected[32768];
    GetEnvironmentVariableW(L"A2WC_APPDATA",expected,32768);
    if(FAILED(SHGetFolderPathW(nullptr,CSIDL_APPDATA,nullptr,0,appdata)))return 27;
    if(wcsncmp(appdata,expected,wcslen(expected)))return 28;
    if(!SHGetSpecialFolderPathW(nullptr,appdata,CSIDL_APPDATA,FALSE))return 29;
    if(wcsncmp(appdata,expected,wcslen(expected)))return 30;
    wchar_t denied[32768];GetEnvironmentVariableW(L"A2WC_DENIED_TEST_DLL",denied,32768);
    if(LoadLibraryW(denied))return 23; // Private sentinel, never the real DLL.
    HANDLE h=CreateFileW(L"\\\\.\\A2WC_VIRTUAL_SENTINEL_NOT_A_DEVICE",GENERIC_READ,0,nullptr,OPEN_EXISTING,0,nullptr);
    if(h!=INVALID_HANDLE_VALUE||GetLastError()!=ERROR_ACCESS_DENIED)return 24;
    return 0;
}
