#pragma once
#define NOMINMAX
#include <windows.h>
#include <cstdint>
using U = uint32_t;
struct Msg { U protocol, rx, tx, timestamp, size, extra; unsigned char data[4128]; };
struct Config { U parameter, value; };
struct ConfigList { U count; Config *items; };
static_assert(sizeof(Msg)==4152, "J2534 04.04 ABI");
static_assert(sizeof(void*)==4, "Reviewed OpenPort provider is x86");
using Open = long (__stdcall *)(void*, U*);
using Close = long (__stdcall *)(U);
using Connect = long (__stdcall *)(U,U,U,U,U*);
using Messages = long (__stdcall *)(U,Msg*,U*,U);
using Ioctl = long (__stdcall *)(U,U,void*,void*);
using Filter = long (__stdcall *)(U,U,Msg*,Msg*,Msg*,U*);
using StopFilter = long (__stdcall *)(U,U);
