; Input C:\Dev\Astra_A2WC511R\work\ecuflash_dynamic\discovery_003\loaded_ecuflash_image.bin
; SHA256 1c9b664dd8c27bc0db4fdc3dcb07e8b8e3e8abd39152c4f89f8367e508380c18; capture base 0x00E80000; addresses below are RVAs
00042de0 b870100000               mov eax, 0x1070
00042de5 e846257d00               call 0x1695330
00042dea a1c04ba701               mov eax, dword ptr [0x1a74bc0]
00042def 33c4                     xor eax, esp
00042df1 8984246c100000           mov dword ptr [esp + 0x106c], eax
00042df8 8b842474100000           mov eax, dword ptr [esp + 0x1074]
00042dff 8d542404                 lea edx, [esp + 4]
00042e03 53                       push ebx
00042e04 8b9c2480100000           mov ebx, dword ptr [esp + 0x1080]
00042e0b 55                       push ebp
00042e0c 8bac2480100000           mov ebp, dword ptr [esp + 0x1080]
00042e13 56                       push esi
00042e14 8bf1                     mov esi, ecx
00042e16 8944240c                 mov dword ptr [esp + 0xc], eax
00042e1a 8b4e04                   mov ecx, dword ptr [esi + 4]
00042e1d ff764c                   push dword ptr [esi + 0x4c]
00042e20 52                       push edx
00042e21 8b01                     mov eax, dword ptr [ecx]
00042e23 8b4018                   mov eax, dword ptr [eax + 0x18]
00042e26 ffd0                     call eax
00042e28 84c0                     test al, al
00042e2a 7507                     jne 0xec2e33
00042e2c 32c0                     xor al, al
00042e2e e9ca000000               jmp 0xec2efd
00042e33 8a442410                 mov al, byte ptr [esp + 0x10]
00042e37 3a4608                   cmp al, byte ptr [esi + 8]
00042e3a 75f0                     jne 0xec2e2c
00042e3c 837e1400                 cmp dword ptr [esi + 0x14], 0
00042e40 57                       push edi
00042e41 7632                     jbe 0xec2e75
00042e43 8a4609                   mov al, byte ptr [esi + 9]
00042e46 8a4c2415                 mov cl, byte ptr [esp + 0x15]
00042e4a 3ac8                     cmp cl, al
00042e4c 7510                     jne 0xec2e5e
00042e4e 8a442416                 mov al, byte ptr [esp + 0x16]
00042e52 3a460e                   cmp al, byte ptr [esi + 0xe]
00042e55 7412                     je 0xec2e69
00042e57 32c0                     xor al, al
00042e59 e99e000000               jmp 0xec2efc
00042e5e 3a4e0e                   cmp cl, byte ptr [esi + 0xe]
00042e61 75f4                     jne 0xec2e57
00042e63 38442416                 cmp byte ptr [esp + 0x16], al
00042e67 75ee                     jne 0xec2e57
00042e69 0fb67c2417               movzx edi, byte ptr [esp + 0x17]
00042e6e b804000000               mov eax, 4
00042e73 eb0d                     jmp 0xec2e82
00042e75 0fb67c2415               movzx edi, byte ptr [esp + 0x15]
00042e7a b802000000               mov eax, 2
00042e7f 2b7e4c                   sub edi, dword ptr [esi + 0x4c]
00042e82 8a440414                 mov al, byte ptr [esp + eax + 0x14]
00042e86 8b4c2410                 mov ecx, dword ptr [esp + 0x10]
00042e8a 57                       push edi
00042e8b 8801                     mov byte ptr [ecx], al
00042e8d 8b4e04                   mov ecx, dword ptr [esi + 4]
00042e90 8b464c                   mov eax, dword ptr [esi + 0x4c]
00042e93 8b11                     mov edx, dword ptr [ecx]
00042e95 8d440418                 lea eax, [esp + eax + 0x18]
00042e99 50                       push eax
00042e9a 8b4218                   mov eax, dword ptr [edx + 0x18]
00042e9d ffd0                     call eax
00042e9f 84c0                     test al, al
00042ea1 74b4                     je 0xec2e57
00042ea3 4f                       dec edi
00042ea4 3b3b                     cmp edi, dword ptr [ebx]
00042ea6 77af                     ja 0xec2e57
00042ea8 893b                     mov dword ptr [ebx], edi
00042eaa 8d4c2414                 lea ecx, [esp + 0x14]
00042eae 8b464c                   mov eax, dword ptr [esi + 0x4c]
00042eb1 57                       push edi
00042eb2 03c1                     add eax, ecx
00042eb4 50                       push eax
00042eb5 55                       push ebp
00042eb6 e825047d00               call 0x16932e0
00042ebb 8b464c                   mov eax, dword ptr [esi + 0x4c]
00042ebe 83c40c                   add esp, 0xc
00042ec1 8b5618                   mov edx, dword ptr [esi + 0x18]
00042ec4 8d0c38                   lea ecx, [eax + edi]
00042ec7 32c0                     xor al, al
00042ec9 8a5c0c14                 mov bl, byte ptr [esp + ecx + 0x14]
00042ecd 83fa01                   cmp edx, 1
00042ed0 7512                     jne 0xec2ee4
00042ed2 52                       push edx
00042ed3 52                       push edx
00042ed4 51                       push ecx
00042ed5 8d442420                 lea eax, [esp + 0x20]
00042ed9 50                       push eax
00042eda e861fcfbff               call 0xe82b40
00042edf 83c410                   add esp, 0x10
00042ee2 eb13                     jmp 0xec2ef7
00042ee4 83fa02                   cmp edx, 2
00042ee7 750e                     jne 0xec2ef7
00042ee9 51                       push ecx
00042eea 8d442418                 lea eax, [esp + 0x18]
00042eee 50                       push eax
00042eef e86c03fcff               call 0xe83260
00042ef4 83c408                   add esp, 8
00042ef7 3ad8                     cmp bl, al
00042ef9 0f94c0                   sete al
00042efc 5f                       pop edi
00042efd 8b8c2478100000           mov ecx, dword ptr [esp + 0x1078]
00042f04 5e                       pop esi
00042f05 5d                       pop ebp
00042f06 5b                       pop ebx
00042f07 33cc                     xor ecx, esp
00042f09 e866ff7c00               call 0x1692e74
00042f0e 81c470100000             add esp, 0x1070
00042f14 c20c00                   ret 0xc
