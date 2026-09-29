@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars32.bat"
if errorlevel 1 exit /b 1
where.exe cl.exe > cl_path.txt
where.exe link.exe > link_path.txt
cl /nologo /Bv /W4 /WX /EHsc /std:c++17 /MT /O2 /Brepro /c identity_probe.cpp /Foidentity_probe.obj > compiler_version.txt 2>&1
if errorlevel 1 exit /b 1
link /? > linker_version.txt 2>&1
exit /b 0
