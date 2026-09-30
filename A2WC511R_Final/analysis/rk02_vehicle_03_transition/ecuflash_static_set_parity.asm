; Input C:\Dev\Astra_A2WC511R\work\ecuflash_dynamic\discovery_003\loaded_ecuflash_image.bin
; SHA256 1c9b664dd8c27bc0db4fdc3dcb07e8b8e3e8abd39152c4f89f8367e508380c18; capture base 0x00E80000; addresses below are RVAs
00097be0 6aff                     push -1
00097be2 6808dd6c01               push 0x16cdd08
00097be7 64a100000000             mov eax, dword ptr fs:[0]
00097bed 50                       push eax
00097bee 51                       push ecx
00097bef 56                       push esi
00097bf0 a1c04ba701               mov eax, dword ptr [0x1a74bc0]
00097bf5 33c4                     xor eax, esp
00097bf7 50                       push eax
00097bf8 8d44240c                 lea eax, [esp + 0xc]
00097bfc 64a300000000             mov dword ptr fs:[0], eax
00097c02 8bf1                     mov esi, ecx
00097c04 8b44241c                 mov eax, dword ptr [esp + 0x1c]
00097c08 898674020000             mov dword ptr [esi + 0x274], eax
00097c0e 8b06                     mov eax, dword ptr [esi]
00097c10 8b00                     mov eax, dword ptr [eax]
00097c12 ffd0                     call eax
00097c14 84c0                     test al, al
00097c16 747a                     je 0xf17c92
00097c18 6a10                     push 0x10
00097c1a 6840b86f01               push 0x16fb840
00097c1f e8cc7d6000               call 0x151f9f0
00097c24 89442424                 mov dword ptr [esp + 0x24], eax
00097c28 83c404                   add esp, 4
00097c2b c744241800000000         mov dword ptr [esp + 0x18], 0
00097c33 8bcc                     mov ecx, esp
00097c35 ba20000000               mov edx, 0x20
00097c3a 51                       push ecx
00097c3b 8bc4                     mov eax, esp
00097c3d 6a0a                     push 0xa
00097c3f 6a00                     push 0
00097c41 668910                   mov word ptr [eax], dx
00097c44 ffb674020000             push dword ptr [esi + 0x274]
00097c4a 51                       push ecx
00097c4b 8d4c2434                 lea ecx, [esp + 0x34]
00097c4f e81cb9f6ff               call 0xe83570
00097c54 8b4e14                   mov ecx, dword ptr [esi + 0x14]
00097c57 e814c2ffff               call 0xf13e70
00097c5c 8b44241c                 mov eax, dword ptr [esp + 0x1c]
00097c60 c7442414ffffffff         mov dword ptr [esp + 0x14], 0xffffffff
00097c68 8b08                     mov ecx, dword ptr [eax]
00097c6a 85c9                     test ecx, ecx
00097c6c 7417                     je 0xf17c85
00097c6e 83f9ff                   cmp ecx, -1
00097c71 741f                     je 0xf17c92
00097c73 83c9ff                   or ecx, 0xffffffff
00097c76 f00fc108                 lock xadd dword ptr [eax], ecx
00097c7a 0f95c0                   setne al
00097c7d 84c0                     test al, al
00097c7f 7511                     jne 0xf17c92
00097c81 8b44241c                 mov eax, dword ptr [esp + 0x1c]
00097c85 6a04                     push 4
00097c87 6a02                     push 2
00097c89 50                       push eax
00097c8a e8b11d6000               call 0x1519a40
00097c8f 83c40c                   add esp, 0xc
00097c92 ffb674020000             push dword ptr [esi + 0x274]
00097c98 8b06                     mov eax, dword ptr [esi]
00097c9a 8bce                     mov ecx, esi
00097c9c 6a16                     push 0x16
00097c9e ff505c                   call dword ptr [eax + 0x5c]
00097ca1 8b4c240c                 mov ecx, dword ptr [esp + 0xc]
00097ca5 64890d00000000           mov dword ptr fs:[0], ecx
00097cac 59                       pop ecx
00097cad 5e                       pop esi
00097cae 83c410                   add esp, 0x10
00097cb1 c20400                   ret 4
