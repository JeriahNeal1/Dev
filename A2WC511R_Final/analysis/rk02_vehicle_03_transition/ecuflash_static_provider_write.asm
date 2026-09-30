; Input C:\Dev\Astra_A2WC511R\work\ecuflash_dynamic\discovery_003\loaded_ecuflash_image.bin
; SHA256 1c9b664dd8c27bc0db4fdc3dcb07e8b8e3e8abd39152c4f89f8367e508380c18; capture base 0x00E80000; addresses below are RVAs
00097fb0 b84c100000               mov eax, 0x104c
00097fb5 e876d37700               call 0x1695330
00097fba a1c04ba701               mov eax, dword ptr [0x1a74bc0]
00097fbf 33c4                     xor eax, esp
00097fc1 89842448100000           mov dword ptr [esp + 0x1048], eax
00097fc8 8b842450100000           mov eax, dword ptr [esp + 0x1050]
00097fcf 53                       push ebx
00097fd0 55                       push ebp
00097fd1 56                       push esi
00097fd2 8bf1                     mov esi, ecx
00097fd4 8944240c                 mov dword ptr [esp + 0xc], eax
00097fd8 57                       push edi
00097fd9 8d4e24                   lea ecx, [esi + 0x24]
00097fdc e81f24faff               call 0xeba400
00097fe1 84c0                     test al, al
00097fe3 0f84f0000000             je 0xf180d9
00097fe9 8b06                     mov eax, dword ptr [esi]
00097feb 8bce                     mov ecx, esi
00097fed 8b4008                   mov eax, dword ptr [eax + 8]
00097ff0 ffd0                     call eax
00097ff2 84c0                     test al, al
00097ff4 0f84df000000             je 0xf180d9
00097ffa 83be6802000000           cmp dword ptr [esi + 0x268], 0
00098001 0f84d2000000             je 0xf180d9
00098007 8b9c2464100000           mov ebx, dword ptr [esp + 0x1064]
0009800e 85db                     test ebx, ebx
00098010 0f84b8000000             je 0xf180ce
00098016 c744241820100000         mov dword ptr [esp + 0x18], 0x1020
0009801e 8bff                     mov edi, edi
00098020 8d8c2464100000           lea ecx, [esp + 0x1064]
00098027 81fb20100000             cmp ebx, 0x1020
0009802d 8d442418                 lea eax, [esp + 0x18]
00098031 0f46c1                   cmovbe eax, ecx
00098034 8b38                     mov edi, dword ptr [eax]
00098036 8d442438                 lea eax, [esp + 0x38]
0009803a 57                       push edi
0009803b ff742414                 push dword ptr [esp + 0x14]
0009803f 897c2438                 mov dword ptr [esp + 0x38], edi
00098043 50                       push eax
00098044 e897b27700               call 0x16932e0
00098049 8b4608                   mov eax, dword ptr [esi + 8]
0009804c 83c40c                   add esp, 0xc
0009804f 017c2410                 add dword ptr [esp + 0x10], edi
00098053 2bdf                     sub ebx, edi
00098055 89442420                 mov dword ptr [esp + 0x20], eax
00098059 8bce                     mov ecx, esi
0009805b 8b8684020000             mov eax, dword ptr [esi + 0x284]
00098061 89442428                 mov dword ptr [esp + 0x28], eax
00098065 8b06                     mov eax, dword ptr [esi]
00098067 899c2464100000           mov dword ptr [esp + 0x1064], ebx
0009806e c744243400000000         mov dword ptr [esp + 0x34], 0
00098076 c744241401000000         mov dword ptr [esp + 0x14], 1
0009807e 8b00                     mov eax, dword ptr [eax]
00098080 ffd0                     call eax
00098082 84c0                     test al, al
00098084 7421                     je 0xf180a7
00098086 57                       push edi
00098087 8d44243c                 lea eax, [esp + 0x3c]
0009808b 50                       push eax
0009808c 51                       push ecx
0009808d 8bfc                     mov edi, esp
0009808f 6a03                     push 3
00098091 68a0b86f01               push 0x16fb8a0
00098096 e855796000               call 0x151f9f0
0009809b 83c408                   add esp, 8
0009809e 8907                     mov dword ptr [edi], eax
000980a0 8bce                     mov ecx, esi
000980a2 e879e4ffff               call 0xf16520
000980a7 ff760c                   push dword ptr [esi + 0xc]
000980aa 8d442418                 lea eax, [esp + 0x18]
000980ae 50                       push eax
000980af 8d442428                 lea eax, [esp + 0x28]
000980b3 50                       push eax
000980b4 ffb668020000             push dword ptr [esi + 0x268]
000980ba 8d4e24                   lea ecx, [esi + 0x24]
000980bd e84e18faff               call 0xeb9910
000980c2 85c0                     test eax, eax
000980c4 750c                     jne 0xf180d2
000980c6 85db                     test ebx, ebx
000980c8 0f8552ffffff             jne 0xf18020
000980ce b001                     mov al, 1
000980d0 eb09                     jmp 0xf180db
000980d2 8bce                     mov ecx, esi
000980d4 e8f7f4ffff               call 0xf175d0
000980d9 32c0                     xor al, al
000980db 8b8c2458100000           mov ecx, dword ptr [esp + 0x1058]
000980e2 5f                       pop edi
000980e3 5e                       pop esi
000980e4 5d                       pop ebp
000980e5 5b                       pop ebx
000980e6 33cc                     xor ecx, esp
000980e8 e887ad7700               call 0x1692e74
000980ed 81c44c100000             add esp, 0x104c
000980f3 c20800                   ret 8
000980f6 cc                       int3 
000980f7 cc                       int3 
000980f8 cc                       int3 
000980f9 cc                       int3 
000980fa cc                       int3 
000980fb cc                       int3 
000980fc cc                       int3 
000980fd cc                       int3 
000980fe cc                       int3 
000980ff cc                       int3 
00098100 8b442404                 mov eax, dword ptr [esp + 4]
00098104 c74104f07b8a01           mov dword ptr [ecx + 4], 0x18a7bf0
0009810b 8901                     mov dword ptr [ecx], eax
0009810d 8bc1                     mov eax, ecx
0009810f c6410801                 mov byte ptr [ecx + 8], 1
00098113 c20400                   ret 4
00098116 cc                       int3 
00098117 cc                       int3 
00098118 cc                       int3 
00098119 cc                       int3 
0009811a cc                       int3 
0009811b cc                       int3 
0009811c cc                       int3 
0009811d cc                       int3 
0009811e cc                       int3 
0009811f cc                       int3 
00098120 8b5104                   mov edx, dword ptr [ecx + 4]
00098123 83c104                   add ecx, 4
00098126 8b02                     mov eax, dword ptr [edx]
00098128 85c0                     test eax, eax
0009812a 7413                     je 0xf1813f
0009812c 83f8ff                   cmp eax, -1
0009812f 7434                     je 0xf18165
00098131 83c8ff                   or eax, 0xffffffff
00098134 f00fc102                 lock xadd dword ptr [edx], eax
00098138 0f95c0                   setne al
0009813b 84c0                     test al, al
0009813d 7526                     jne 0xf18165
0009813f 56                       push esi
00098140 8b31                     mov esi, dword ptr [ecx]
00098142 8b460c                   mov eax, dword ptr [esi + 0xc]
00098145 83c004                   add eax, 4
00098148 8d0486                   lea eax, [esi + eax*4]
0009814b 50                       push eax
0009814c 8b4608                   mov eax, dword ptr [esi + 8]
0009814f 83c004                   add eax, 4
00098152 8d0486                   lea eax, [esi + eax*4]
00098155 50                       push eax
00098156 e855bff6ff               call 0xe840b0
0009815b 56                       push esi
0009815c e87f5d7700               call 0x168dee0
00098161 83c404                   add esp, 4
00098164 5e                       pop esi
00098165 c3                       ret 
00098166 cc                       int3 
00098167 cc                       int3 
00098168 cc                       int3 
00098169 cc                       int3 
0009816a cc                       int3 
0009816b cc                       int3 
0009816c cc                       int3 
0009816d cc                       int3 
0009816e cc                       int3 
0009816f cc                       int3 
