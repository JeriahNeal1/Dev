; Input C:\Dev\Astra_A2WC511R\work\ecuflash_dynamic\discovery_003\loaded_ecuflash_image.bin
; SHA256 1c9b664dd8c27bc0db4fdc3dcb07e8b8e3e8abd39152c4f89f8367e508380c18; capture base 0x00E80000; addresses below are RVAs
00097b50 83ec10                   sub esp, 0x10
00097b53 56                       push esi
00097b54 8bf1                     mov esi, ecx
00097b56 57                       push edi
00097b57 8d4e24                   lea ecx, [esi + 0x24]
00097b5a e8a128faff               call 0xeba400
00097b5f 84c0                     test al, al
00097b61 746e                     je 0xf17bd1
00097b63 8b06                     mov eax, dword ptr [esi]
00097b65 8bce                     mov ecx, esi
00097b67 8b4008                   mov eax, dword ptr [eax + 8]
00097b6a ffd0                     call eax
00097b6c 84c0                     test al, al
00097b6e 7461                     je 0xf17bd1
00097b70 8b8668020000             mov eax, dword ptr [esi + 0x268]
00097b76 85c0                     test eax, eax
00097b78 7457                     je 0xf17bd1
00097b7a 53                       push ebx
00097b7b 8b5c2420                 mov ebx, dword ptr [esp + 0x20]
00097b7f 8d4c240c                 lea ecx, [esp + 0xc]
00097b83 55                       push ebp
00097b84 8b6c2428                 mov ebp, dword ptr [esp + 0x28]
00097b88 894c241c                 mov dword ptr [esp + 0x1c], ecx
00097b8c 8d4c2418                 lea ecx, [esp + 0x18]
00097b90 6a00                     push 0
00097b92 51                       push ecx
00097b93 6a02                     push 2
00097b95 50                       push eax
00097b96 8d4e24                   lea ecx, [esi + 0x24]
00097b99 895c2420                 mov dword ptr [esp + 0x20], ebx
00097b9d 896c2424                 mov dword ptr [esp + 0x24], ebp
00097ba1 c744242801000000         mov dword ptr [esp + 0x28], 1
00097ba9 e86213faff               call 0xeb8f10
00097bae 85c0                     test eax, eax
00097bb0 0f94c0                   sete al
00097bb3 84c0                     test al, al
00097bb5 7410                     je 0xf17bc7
00097bb7 83fb03                   cmp ebx, 3
00097bba 750b                     jne 0xf17bc7
00097bbc 85ed                     test ebp, ebp
00097bbe 0f95c1                   setne cl
00097bc1 888ec0120000             mov byte ptr [esi + 0x12c0], cl
00097bc7 5d                       pop ebp
00097bc8 5b                       pop ebx
00097bc9 5f                       pop edi
00097bca 5e                       pop esi
00097bcb 83c410                   add esp, 0x10
00097bce c20800                   ret 8
00097bd1 5f                       pop edi
00097bd2 32c0                     xor al, al
00097bd4 5e                       pop esi
00097bd5 83c410                   add esp, 0x10
