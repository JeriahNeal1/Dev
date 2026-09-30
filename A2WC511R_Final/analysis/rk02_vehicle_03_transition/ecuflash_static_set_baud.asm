; Input C:\Dev\Astra_A2WC511R\work\ecuflash_dynamic\discovery_003\loaded_ecuflash_image.bin
; SHA256 1c9b664dd8c27bc0db4fdc3dcb07e8b8e3e8abd39152c4f89f8367e508380c18; capture base 0x00E80000; addresses below are RVAs
00097a30 6aff                     push -1
00097a32 68f8a96c01               push 0x16ca9f8
00097a37 64a100000000             mov eax, dword ptr fs:[0]
00097a3d 50                       push eax
00097a3e 51                       push ecx
00097a3f 56                       push esi
00097a40 57                       push edi
00097a41 a1c04ba701               mov eax, dword ptr [0x1a74bc0]
00097a46 33c4                     xor eax, esp
00097a48 50                       push eax
00097a49 8d442410                 lea eax, [esp + 0x10]
00097a4d 64a300000000             mov dword ptr fs:[0], eax
00097a53 8bf1                     mov esi, ecx
00097a55 8b7c2420                 mov edi, dword ptr [esp + 0x20]
00097a59 3bbe70020000             cmp edi, dword ptr [esi + 0x270]
00097a5f 0f84ab000000             je 0xf17b10
00097a65 8b06                     mov eax, dword ptr [esi]
00097a67 8b00                     mov eax, dword ptr [eax]
00097a69 ffd0                     call eax
00097a6b 84c0                     test al, al
00097a6d 7475                     je 0xf17ae4
00097a6f 6a0e                     push 0xe
00097a71 6830b86f01               push 0x16fb830
00097a76 e8757f6000               call 0x151f9f0
00097a7b 89442428                 mov dword ptr [esp + 0x28], eax
00097a7f 83c404                   add esp, 4
00097a82 c744241c00000000         mov dword ptr [esp + 0x1c], 0
00097a8a 8bcc                     mov ecx, esp
00097a8c ba20000000               mov edx, 0x20
00097a91 51                       push ecx
00097a92 8bc4                     mov eax, esp
00097a94 6a0a                     push 0xa
00097a96 6a00                     push 0
00097a98 57                       push edi
00097a99 51                       push ecx
00097a9a 8d4c2438                 lea ecx, [esp + 0x38]
00097a9e 668910                   mov word ptr [eax], dx
00097aa1 e8cabaf6ff               call 0xe83570
00097aa6 8b4e14                   mov ecx, dword ptr [esi + 0x14]
00097aa9 e8c2c3ffff               call 0xf13e70
00097aae 8b442420                 mov eax, dword ptr [esp + 0x20]
00097ab2 c7442418ffffffff         mov dword ptr [esp + 0x18], 0xffffffff
00097aba 8b08                     mov ecx, dword ptr [eax]
00097abc 85c9                     test ecx, ecx
00097abe 7417                     je 0xf17ad7
00097ac0 83f9ff                   cmp ecx, -1
00097ac3 741f                     je 0xf17ae4
00097ac5 83c9ff                   or ecx, 0xffffffff
00097ac8 f00fc108                 lock xadd dword ptr [eax], ecx
00097acc 0f95c0                   setne al
00097acf 84c0                     test al, al
00097ad1 7511                     jne 0xf17ae4
00097ad3 8b442420                 mov eax, dword ptr [esp + 0x20]
00097ad7 6a04                     push 4
00097ad9 6a02                     push 2
00097adb 50                       push eax
00097adc e85f1f6000               call 0x1519a40
00097ae1 83c40c                   add esp, 0xc
00097ae4 8d4e24                   lea ecx, [esi + 0x24]
00097ae7 e81429faff               call 0xeba400
00097aec 84c0                     test al, al
00097aee 7420                     je 0xf17b10
00097af0 83be6802000000           cmp dword ptr [esi + 0x268], 0
00097af7 89be70020000             mov dword ptr [esi + 0x270], edi
00097afd 740a                     je 0xf17b09
00097aff 8b06                     mov eax, dword ptr [esi]
00097b01 8bce                     mov ecx, esi
00097b03 57                       push edi
00097b04 6a01                     push 1
00097b06 ff505c                   call dword ptr [eax + 0x5c]
00097b09 8b06                     mov eax, dword ptr [esi]
00097b0b 8bce                     mov ecx, esi
00097b0d ff5024                   call dword ptr [eax + 0x24]
00097b10 8b4c2410                 mov ecx, dword ptr [esp + 0x10]
00097b14 64890d00000000           mov dword ptr fs:[0], ecx
00097b1b 59                       pop ecx
00097b1c 5f                       pop edi
00097b1d 5e                       pop esi
00097b1e 83c410                   add esp, 0x10
00097b21 c20400                   ret 4
