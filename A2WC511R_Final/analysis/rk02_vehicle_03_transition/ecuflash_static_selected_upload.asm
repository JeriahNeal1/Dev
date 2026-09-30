; Input C:\Dev\Astra_A2WC511R\work\ecuflash_dynamic\discovery_003\loaded_ecuflash_image.bin
; SHA256 1c9b664dd8c27bc0db4fdc3dcb07e8b8e3e8abd39152c4f89f8367e508380c18; capture base 0x00E80000; addresses below are RVAs
0009c0f0 51                       push ecx
0009c0f1 56                       push esi
0009c0f2 57                       push edi
0009c0f3 8bf9                     mov edi, ecx
0009c0f5 68c8000000               push 0xc8
0009c0fa 8b4f04                   mov ecx, dword ptr [edi + 4]
0009c0fd e89e91ffff               call 0xf152a0
0009c102 8b471c                   mov eax, dword ptr [edi + 0x1c]
0009c105 83e802                   sub eax, 2
0009c108 743a                     je 0xf1c144
0009c10a 48                       dec eax
0009c10b 7430                     je 0xf1c13d
0009c10d 48                       dec eax
0009c10e 7426                     je 0xf1c136
0009c110 51                       push ecx
0009c111 8bf4                     mov esi, esp
0009c113 6a2c                     push 0x2c
0009c115 68fcbf6f01               push 0x16fbffc
0009c11a e8d1386000               call 0x151f9f0
0009c11f 83c408                   add esp, 8
0009c122 8906                     mov dword ptr [esi], eax
0009c124 8b4f08                   mov ecx, dword ptr [edi + 8]
0009c127 6a07                     push 7
0009c129 e8127affff               call 0xf13b40
0009c12e 32c0                     xor al, al
0009c130 5f                       pop edi
0009c131 5e                       pop esi
0009c132 59                       pop ecx
0009c133 c20400                   ret 4
0009c136 be0030ffff               mov esi, 0xffff3000
0009c13b eb0c                     jmp 0xf1c149
0009c13d be0060ffff               mov esi, 0xffff6000
0009c142 eb05                     jmp 0xf1c149
0009c144 be00000200               mov esi, 0x20000
0009c149 8b07                     mov eax, dword ptr [edi]
0009c14b 8b4f0c                   mov ecx, dword ptr [edi + 0xc]
0009c14e ff7004                   push dword ptr [eax + 4]
0009c151 6a04                     push 4
0009c153 56                       push esi
0009c154 e81757faff               call 0xec1870
0009c159 8b07                     mov eax, dword ptr [edi]
0009c15b 8b4f0c                   mov ecx, dword ptr [edi + 0xc]
0009c15e ff7004                   push dword ptr [eax + 4]
0009c161 6a04                     push 4
0009c163 56                       push esi
0009c164 e80757faff               call 0xec1870
0009c169 84c0                     test al, al
0009c16b 74c1                     je 0xf1c12e
0009c16d 8b07                     mov eax, dword ptr [edi]
0009c16f 8bcf                     mov ecx, edi
0009c171 ff7004                   push dword ptr [eax + 4]
0009c174 56                       push esi
0009c175 ff742418                 push dword ptr [esp + 0x18]
0009c179 e812010000               call 0xf1c290
0009c17e 84c0                     test al, al
0009c180 74ac                     je 0xf1c12e
0009c182 8b4f04                   mov ecx, dword ptr [edi + 4]
0009c185 68c8000000               push 0xc8
0009c18a e81191ffff               call 0xf152a0
0009c18f 8b4f0c                   mov ecx, dword ptr [edi + 0xc]
0009c192 8d442408                 lea eax, [esp + 8]
0009c196 6a02                     push 2
0009c198 50                       push eax
0009c199 66c74424100101           mov word ptr [esp + 0x10], 0x101
0009c1a0 e87b5bfaff               call 0xec1d20
0009c1a5 5f                       pop edi
0009c1a6 b001                     mov al, 1
0009c1a8 5e                       pop esi
0009c1a9 59                       pop ecx
0009c1aa c20400                   ret 4
0009c1ad cc                       int3 
0009c1ae cc                       int3 
0009c1af cc                       int3 
