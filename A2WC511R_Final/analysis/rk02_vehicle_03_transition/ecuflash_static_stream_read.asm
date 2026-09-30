; Input C:\Dev\Astra_A2WC511R\work\ecuflash_dynamic\discovery_003\loaded_ecuflash_image.bin
; SHA256 1c9b664dd8c27bc0db4fdc3dcb07e8b8e3e8abd39152c4f89f8367e508380c18; capture base 0x00E80000; addresses below are RVAs
00097470 51                       push ecx
00097471 55                       push ebp
00097472 8b6c240c                 mov ebp, dword ptr [esp + 0xc]
00097476 56                       push esi
00097477 8bf1                     mov esi, ecx
00097479 8d4e24                   lea ecx, [esi + 0x24]
0009747c e87f2ffaff               call 0xeba400
00097481 84c0                     test al, al
00097483 0f84e8000000             je 0xf17571
00097489 8b06                     mov eax, dword ptr [esi]
0009748b 8bce                     mov ecx, esi
0009748d 8b4008                   mov eax, dword ptr [eax + 8]
00097490 ffd0                     call eax
00097492 84c0                     test al, al
00097494 0f84d7000000             je 0xf17571
0009749a 83be6802000000           cmp dword ptr [esi + 0x268], 0
000974a1 0f84ca000000             je 0xf17571
000974a7 8b96b0120000             mov edx, dword ptr [esi + 0x12b0]
000974ad 8b8eb4120000             mov ecx, dword ptr [esi + 0x12b4]
000974b3 53                       push ebx
000974b4 8b5c2418                 mov ebx, dword ptr [esp + 0x18]
000974b8 57                       push edi
000974b9 3bd1                     cmp edx, ecx
000974bb 7336                     jae 0xf174f3
000974bd 2bca                     sub ecx, edx
000974bf 8d7c241c                 lea edi, [esp + 0x1c]
000974c3 3bcb                     cmp ecx, ebx
000974c5 894c2410                 mov dword ptr [esp + 0x10], ecx
000974c9 8d442410                 lea eax, [esp + 0x10]
000974cd 0f43c7                   cmovae eax, edi
000974d0 8b38                     mov edi, dword ptr [eax]
000974d2 8d8690020000             lea eax, [esi + 0x290]
000974d8 57                       push edi
000974d9 03c2                     add eax, edx
000974db 50                       push eax
000974dc 55                       push ebp
000974dd e8febd7700               call 0x16932e0
000974e2 2bdf                     sub ebx, edi
000974e4 83c40c                   add esp, 0xc
000974e7 03ef                     add ebp, edi
000974e9 895c241c                 mov dword ptr [esp + 0x1c], ebx
000974ed 01beb0120000             add dword ptr [esi + 0x12b0], edi
000974f3 85db                     test ebx, ebx
000974f5 7466                     je 0xf1755d
000974f7 8d8e90020000             lea ecx, [esi + 0x290]
000974fd 8d4900                   lea ecx, [ecx]
00097500 8b06                     mov eax, dword ptr [esi]
00097502 8d542418                 lea edx, [esp + 0x18]
00097506 52                       push edx
00097507 51                       push ecx
00097508 8bce                     mov ecx, esi
0009750a c744242020100000         mov dword ptr [esp + 0x20], 0x1020
00097512 8b4014                   mov eax, dword ptr [eax + 0x14]
00097515 ffd0                     call eax
00097517 84c0                     test al, al
00097519 744c                     je 0xf17567
0009751b 8b442418                 mov eax, dword ptr [esp + 0x18]
0009751f 8d54241c                 lea edx, [esp + 0x1c]
00097523 3bc3                     cmp eax, ebx
00097525 8986b4120000             mov dword ptr [esi + 0x12b4], eax
0009752b 8d4c2418                 lea ecx, [esp + 0x18]
0009752f 0f43ca                   cmovae ecx, edx
00097532 8d8690020000             lea eax, [esi + 0x290]
00097538 8b39                     mov edi, dword ptr [ecx]
0009753a 57                       push edi
0009753b 50                       push eax
0009753c 55                       push ebp
0009753d e89ebd7700               call 0x16932e0
00097542 2bdf                     sub ebx, edi
00097544 89beb0120000             mov dword ptr [esi + 0x12b0], edi
0009754a 83c40c                   add esp, 0xc
0009754d 895c241c                 mov dword ptr [esp + 0x1c], ebx
00097551 03ef                     add ebp, edi
00097553 8d8e90020000             lea ecx, [esi + 0x290]
00097559 85db                     test ebx, ebx
0009755b 75a3                     jne 0xf17500
0009755d 5f                       pop edi
0009755e 5b                       pop ebx
0009755f 5e                       pop esi
00097560 b001                     mov al, 1
00097562 5d                       pop ebp
00097563 59                       pop ecx
00097564 c20800                   ret 8
00097567 5f                       pop edi
00097568 5b                       pop ebx
00097569 5e                       pop esi
0009756a 32c0                     xor al, al
0009756c 5d                       pop ebp
0009756d 59                       pop ecx
0009756e c20800                   ret 8
00097571 5e                       pop esi
00097572 32c0                     xor al, al
00097574 5d                       pop ebp
00097575 59                       pop ecx
00097576 c20800                   ret 8
00097579 cc                       int3 
0009757a cc                       int3 
0009757b cc                       int3 
0009757c cc                       int3 
0009757d cc                       int3 
0009757e cc                       int3 
0009757f cc                       int3 
