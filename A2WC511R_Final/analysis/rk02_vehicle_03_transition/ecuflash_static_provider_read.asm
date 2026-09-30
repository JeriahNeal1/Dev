; Input C:\Dev\Astra_A2WC511R\work\ecuflash_dynamic\discovery_003\loaded_ecuflash_image.bin
; SHA256 1c9b664dd8c27bc0db4fdc3dcb07e8b8e3e8abd39152c4f89f8367e508380c18; capture base 0x00E80000; addresses below are RVAs
00097310 b844100000               mov eax, 0x1044
00097315 e816e07700               call 0x1695330
0009731a a1c04ba701               mov eax, dword ptr [0x1a74bc0]
0009731f 33c4                     xor eax, esp
00097321 89842440100000           mov dword ptr [esp + 0x1040], eax
00097328 53                       push ebx
00097329 55                       push ebp
0009732a 8bac2450100000           mov ebp, dword ptr [esp + 0x1050]
00097331 56                       push esi
00097332 8bf1                     mov esi, ecx
00097334 57                       push edi
00097335 8bbc245c100000           mov edi, dword ptr [esp + 0x105c]
0009733c 8d4e24                   lea ecx, [esi + 0x24]
0009733f e8bc30faff               call 0xeba400
00097344 84c0                     test al, al
00097346 745f                     je 0xf173a7
00097348 8b06                     mov eax, dword ptr [esi]
0009734a 8bce                     mov ecx, esi
0009734c 8b4008                   mov eax, dword ptr [eax + 8]
0009734f ffd0                     call eax
00097351 84c0                     test al, al
00097353 7452                     je 0xf173a7
00097355 8b8668020000             mov eax, dword ptr [esi + 0x268]
0009735b 85c0                     test eax, eax
0009735d 7448                     je 0xf173a7
0009735f ff760c                   push dword ptr [esi + 0xc]
00097362 8d4c2418                 lea ecx, [esp + 0x18]
00097366 c744241801000000         mov dword ptr [esp + 0x18], 1
0009736e 51                       push ecx
0009736f 8d4c2420                 lea ecx, [esp + 0x20]
00097373 51                       push ecx
00097374 50                       push eax
00097375 8d4e24                   lea ecx, [esi + 0x24]
00097378 e8b320faff               call 0xeb9430
0009737d 85c0                     test eax, eax
0009737f 7526                     jne 0xf173a7
00097381 f644241c0e               test byte ptr [esp + 0x1c], 0xe
00097386 743c                     je 0xf173c4
00097388 ff760c                   push dword ptr [esi + 0xc]
0009738b 8d442418                 lea eax, [esp + 0x18]
0009738f 50                       push eax
00097390 8d442420                 lea eax, [esp + 0x20]
00097394 50                       push eax
00097395 ffb668020000             push dword ptr [esi + 0x268]
0009739b 8d4e24                   lea ecx, [esi + 0x24]
0009739e e88d20faff               call 0xeb9430
000973a3 85c0                     test eax, eax
000973a5 74da                     je 0xf17381
000973a7 32c0                     xor al, al
000973a9 8b8c2450100000           mov ecx, dword ptr [esp + 0x1050]
000973b0 5f                       pop edi
000973b1 5e                       pop esi
000973b2 5d                       pop ebp
000973b3 5b                       pop ebx
000973b4 33cc                     xor ecx, esp
000973b6 e8b9ba7700               call 0x1692e74
000973bb 81c444100000             add esp, 0x1044
000973c1 c20800                   ret 8
000973c4 8b442428                 mov eax, dword ptr [esp + 0x28]
000973c8 8b0f                     mov ecx, dword ptr [edi]
000973ca 50                       push eax
000973cb 3bc1                     cmp eax, ecx
000973cd 7630                     jbe 0xf173ff
000973cf 51                       push ecx
000973d0 6854b86f01               push 0x16fb854
000973d5 ff7614                   push dword ptr [esi + 0x14]
000973d8 e873c6ffff               call 0xf13a50
000973dd 83c410                   add esp, 0x10
000973e0 8d442430                 lea eax, [esp + 0x30]
000973e4 ff742428                 push dword ptr [esp + 0x28]
000973e8 50                       push eax
000973e9 51                       push ecx
000973ea 8bcc                     mov ecx, esp
000973ec 6890b86f01               push 0x16fb890
000973f1 e8faacf6ff               call 0xe820f0
000973f6 8bce                     mov ecx, esi
000973f8 e823f1ffff               call 0xf16520
000973fd eba8                     jmp 0xf173a7
000973ff 8907                     mov dword ptr [edi], eax
00097401 8d442434                 lea eax, [esp + 0x34]
00097405 50                       push eax
00097406 55                       push ebp
00097407 e8d4be7700               call 0x16932e0
0009740c 83c40c                   add esp, 0xc
0009740f 833f00                   cmp dword ptr [edi], 0
00097412 7446                     je 0xf1745a
00097414 8b06                     mov eax, dword ptr [esi]
00097416 8bce                     mov ecx, esi
00097418 8b00                     mov eax, dword ptr [eax]
0009741a ffd0                     call eax
0009741c 84c0                     test al, al
0009741e 743a                     je 0xf1745a
00097420 f644241c01               test byte ptr [esp + 0x1c], 1
00097425 8d442430                 lea eax, [esp + 0x30]
00097429 ff37                     push dword ptr [edi]
0009742b 50                       push eax
0009742c 51                       push ecx
0009742d 8bcc                     mov ecx, esp
0009742f 7418                     je 0xf17449
00097431 6898b86f01               push 0x16fb898
00097436 e8b5acf6ff               call 0xe820f0
0009743b 8bce                     mov ecx, esi
0009743d e8def0ffff               call 0xf16520
00097442 b001                     mov al, 1
00097444 e960ffffff               jmp 0xf173a9
00097449 689cb86f01               push 0x16fb89c
0009744e e89dacf6ff               call 0xe820f0
00097453 8bce                     mov ecx, esi
00097455 e8c6f0ffff               call 0xf16520
0009745a b001                     mov al, 1
0009745c e948ffffff               jmp 0xf173a9
00097461 cc                       int3 
