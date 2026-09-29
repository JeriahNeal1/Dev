#include <windows.h>
#include <detours.h>
#include <string>
#include <iostream>
int wmain(int argc,wchar_t**argv){
    if(argc!=3)return 2;
    std::wstring target=argv[1],dll=argv[2];
    int n=WideCharToMultiByte(CP_ACP,0,dll.c_str(),-1,nullptr,0,nullptr,nullptr);
    std::string ansi(n,0);WideCharToMultiByte(CP_ACP,0,dll.c_str(),-1,ansi.data(),n,nullptr,nullptr);
    std::wstring cmd=L"\""+target+L"\"";
    STARTUPINFOW si{};si.cb=sizeof(si);si.dwFlags=STARTF_USESHOWWINDOW;si.wShowWindow=SW_HIDE;
    PROCESS_INFORMATION pi{};
    if(!DetourCreateProcessWithDllExW(target.c_str(),cmd.data(),nullptr,nullptr,FALSE,CREATE_DEFAULT_ERROR_MODE,nullptr,nullptr,&si,&pi,ansi.c_str(),nullptr)){
        std::cerr<<"create failed "<<GetLastError()<<std::endl;return 3;
    }
    std::cout<<"{\"pid\":"<<pi.dwProcessId<<"}"<<std::endl;
    WaitForSingleObject(pi.hProcess,INFINITE);DWORD code=0;GetExitCodeProcess(pi.hProcess,&code);
    std::cout<<"{\"exit_code\":"<<code<<"}"<<std::endl;
    CloseHandle(pi.hThread);CloseHandle(pi.hProcess);return 0;
}
