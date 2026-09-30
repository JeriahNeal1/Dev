; Input C:\Dev\Astra_A2WC511R\work\ecuflash_dynamic\discovery_003\loaded_ecuflash_image.bin
; SHA256 1c9b664dd8c27bc0db4fdc3dcb07e8b8e3e8abd39152c4f89f8367e508380c18; capture base 0x00E80000; addresses below are RVAs
0009bb60 83ec18                   sub esp, 0x18
0009bb63 a1c04ba701               mov eax, dword ptr [0x1a74bc0]
0009bb68 33c4                     xor eax, esp
0009bb6a 89442414                 mov dword ptr [esp + 0x14], eax
0009bb6e 56                       push esi
0009bb6f 57                       push edi
0009bb70 8bf9                     mov edi, ecx
0009bb72 8b4f04                   mov ecx, dword ptr [edi + 4]
0009bb75 85c9                     test ecx, ecx
0009bb77 0f8434010000             je 0xf1bcb1
0009bb7d 8b01                     mov eax, dword ptr [ecx]
0009bb7f 68c0120000               push 0x12c0
0009bb84 ff5034                   call dword ptr [eax + 0x34]
0009bb87 8b4704                   mov eax, dword ptr [edi + 4]
0009bb8a 6a01                     push 1
0009bb8c c7400803000000           mov dword ptr [eax + 8], 3
0009bb93 8b4f04                   mov ecx, dword ptr [edi + 4]
0009bb96 8b01                     mov eax, dword ptr [ecx]
0009bb98 ff5040                   call dword ptr [eax + 0x40]
0009bb9b 8b4f04                   mov ecx, dword ptr [edi + 4]
0009bb9e 8b01                     mov eax, dword ptr [ecx]
0009bba0 8b4004                   mov eax, dword ptr [eax + 4]
0009bba3 ffd0                     call eax
0009bba5 84c0                     test al, al
0009bba7 0f8404010000             je 0xf1bcb1
0009bbad 8b4f04                   mov ecx, dword ptr [edi + 4]
0009bbb0 68c0120000               push 0x12c0
0009bbb5 8b01                     mov eax, dword ptr [ecx]
0009bbb7 ff5034                   call dword ptr [eax + 0x34]
0009bbba 8b4f04                   mov ecx, dword ptr [edi + 4]
0009bbbd 6a00                     push 0
0009bbbf 8b01                     mov eax, dword ptr [ecx]
0009bbc1 ff503c                   call dword ptr [eax + 0x3c]
0009bbc4 8b4f04                   mov ecx, dword ptr [edi + 4]
0009bbc7 6a01                     push 1
0009bbc9 6a07                     push 7
0009bbcb 8b01                     mov eax, dword ptr [ecx]
0009bbcd ff505c                   call dword ptr [eax + 0x5c]
0009bbd0 8b4f04                   mov ecx, dword ptr [edi + 4]
0009bbd3 6a00                     push 0
0009bbd5 6a0a                     push 0xa
0009bbd7 8b01                     mov eax, dword ptr [ecx]
0009bbd9 ff505c                   call dword ptr [eax + 0x5c]
0009bbdc 8b4f04                   mov ecx, dword ptr [edi + 4]
0009bbdf 6a00                     push 0
0009bbe1 6a0c                     push 0xc
0009bbe3 8b01                     mov eax, dword ptr [ecx]
0009bbe5 ff505c                   call dword ptr [eax + 0x5c]
0009bbe8 8b4f04                   mov ecx, dword ptr [edi + 4]
0009bbeb 6a00                     push 0
0009bbed 6a03                     push 3
0009bbef 8b01                     mov eax, dword ptr [ecx]
0009bbf1 ff505c                   call dword ptr [eax + 0x5c]
0009bbf4 837f1c01                 cmp dword ptr [edi + 0x1c], 1
0009bbf8 750c                     jne 0xf1bc06
0009bbfa 8b4f04                   mov ecx, dword ptr [edi + 4]
0009bbfd 6afe                     push -2
0009bbff 6a09                     push 9
0009bc01 8b01                     mov eax, dword ptr [ecx]
0009bc03 ff504c                   call dword ptr [eax + 0x4c]
0009bc06 8b4f04                   mov ecx, dword ptr [edi + 4]
0009bc09 8b01                     mov eax, dword ptr [ecx]
0009bc0b ff5024                   call dword ptr [eax + 0x24]
0009bc0e 8b4f04                   mov ecx, dword ptr [edi + 4]
0009bc11 8d44240c                 lea eax, [esp + 0xc]
0009bc15 50                       push eax
0009bc16 6a01                     push 1
0009bc18 6a00                     push 0
0009bc1a 6a00                     push 0
0009bc1c 6a00                     push 0
0009bc1e e8ed95ffff               call 0xf15210
0009bc23 8b4f04                   mov ecx, dword ptr [edi + 4]
0009bc26 8d442410                 lea eax, [esp + 0x10]
0009bc2a 50                       push eax
0009bc2b e89096ffff               call 0xf152c0
0009bc30 8b471c                   mov eax, dword ptr [edi + 0x1c]
0009bc33 83f801                   cmp eax, 1
0009bc36 7405                     je 0xf1bc3d
0009bc38 83f802                   cmp eax, 2
0009bc3b 7507                     jne 0xf1bc44
0009bc3d 807c241300               cmp byte ptr [esp + 0x13], 0
0009bc42 744f                     je 0xf1bc93
0009bc44 807c241500               cmp byte ptr [esp + 0x15], 0
0009bc49 7448                     je 0xf1bc93
0009bc4b 817c241850c30000         cmp dword ptr [esp + 0x18], 0xc350
0009bc53 723e                     jb 0xf1bc93
0009bc55 8b4f04                   mov ecx, dword ptr [edi + 4]
0009bc58 83f801                   cmp eax, 1
0009bc5b 8b01                     mov eax, dword ptr [ecx]
0009bc5d 741a                     je 0xf1bc79
0009bc5f 6aff                     push -1
0009bc61 6a09                     push 9
0009bc63 ff504c                   call dword ptr [eax + 0x4c]
0009bc66 b001                     mov al, 1
0009bc68 5f                       pop edi
0009bc69 5e                       pop esi
0009bc6a 8b4c2414                 mov ecx, dword ptr [esp + 0x14]
0009bc6e 33cc                     xor ecx, esp
0009bc70 e8ff717700               call 0x1692e74
0009bc75 83c418                   add esp, 0x18
0009bc78 c3                       ret 
0009bc79 6afe                     push -2
0009bc7b 6a09                     push 9
0009bc7d ff504c                   call dword ptr [eax + 0x4c]
0009bc80 b001                     mov al, 1
0009bc82 5f                       pop edi
0009bc83 5e                       pop esi
0009bc84 8b4c2414                 mov ecx, dword ptr [esp + 0x14]
0009bc88 33cc                     xor ecx, esp
0009bc8a e8e5717700               call 0x1692e74
0009bc8f 83c418                   add esp, 0x18
0009bc92 c3                       ret 
0009bc93 51                       push ecx
0009bc94 8bf4                     mov esi, esp
0009bc96 6a38                     push 0x38
0009bc98 6880bd6f01               push 0x16fbd80
0009bc9d e84e3d6000               call 0x151f9f0
0009bca2 83c408                   add esp, 8
0009bca5 8906                     mov dword ptr [esi], eax
0009bca7 8b4f08                   mov ecx, dword ptr [edi + 8]
0009bcaa 6a07                     push 7
0009bcac e88f7effff               call 0xf13b40
0009bcb1 8b4c241c                 mov ecx, dword ptr [esp + 0x1c]
0009bcb5 32c0                     xor al, al
0009bcb7 5f                       pop edi
0009bcb8 5e                       pop esi
0009bcb9 33cc                     xor ecx, esp
0009bcbb e8b4717700               call 0x1692e74
0009bcc0 83c418                   add esp, 0x18
0009bcc3 c3                       ret 
