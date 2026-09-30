; Input C:\Dev\Astra_A2WC511R\work\ecuflash_dynamic\discovery_003\loaded_ecuflash_image.bin
; SHA256 1c9b664dd8c27bc0db4fdc3dcb07e8b8e3e8abd39152c4f89f8367e508380c18; capture base 0x00E80000; addresses below are RVAs
000416c0 53                       push ebx
000416c1 55                       push ebp
000416c2 56                       push esi
000416c3 8b742418                 mov esi, dword ptr [esp + 0x18]
000416c7 8bd9                     mov ebx, ecx
000416c9 57                       push edi
000416ca 8d7e01                   lea edi, [esi + 1]
000416cd 57                       push edi
000416ce e860d17c00               call 0x168e833
000416d3 8a542418                 mov dl, byte ptr [esp + 0x18]
000416d7 8be8                     mov ebp, eax
000416d9 56                       push esi
000416da ff742420                 push dword ptr [esp + 0x20]
000416de 8d4d01                   lea ecx, [ebp + 1]
000416e1 885500                   mov byte ptr [ebp], dl
000416e4 51                       push ecx
000416e5 e8f61b7d00               call 0x16932e0
000416ea 83c410                   add esp, 0x10
000416ed ff742424                 push dword ptr [esp + 0x24]
000416f1 ff742424                 push dword ptr [esp + 0x24]
000416f5 57                       push edi
000416f6 55                       push ebp
000416f7 51                       push ecx
000416f8 8bf4                     mov esi, esp
000416fa 6a16                     push 0x16
000416fc 68f8286f01               push 0x16f28f8
00041701 e8eae26500               call 0x151f9f0
00041706 83c408                   add esp, 8
00041709 8906                     mov dword ptr [esi], eax
0004170b 8bcb                     mov ecx, ebx
0004170d e83e100000               call 0xec2750
00041712 55                       push ebp
00041713 8ad8                     mov bl, al
00041715 e8c6337d00               call 0x1694ae0
0004171a 83c404                   add esp, 4
0004171d 8ac3                     mov al, bl
0004171f 5f                       pop edi
00041720 5e                       pop esi
00041721 5d                       pop ebp
00041722 5b                       pop ebx
00041723 c21400                   ret 0x14
