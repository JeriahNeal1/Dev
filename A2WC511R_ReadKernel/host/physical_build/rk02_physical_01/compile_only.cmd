@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars32.bat"
if errorlevel 1 exit /b 1
where.exe link.exe > resolved_linker.txt
"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207\bin\Hostx86\x86\cl.exe" /nologo /W4 /WX /EHsc /std:c++17 /MT /O2 /Brepro /I"C:\Dev\A2WC511R_ReadKernel\host\physical_build\rk02_physical_01" /I"C:\Dev\A2WC511R_ReadKernel\host" "C:\Dev\A2WC511R_ReadKernel\host\physical_build\rk02_physical_01\native_physical.cpp" /Fonative_physical.obj /Feowned_physical_read32.exe /link /Brepro bcrypt.lib
if errorlevel 1 exit /b 1
