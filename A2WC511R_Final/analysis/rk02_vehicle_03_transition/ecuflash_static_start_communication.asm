; Input C:\Dev\Astra_A2WC511R\work\ecuflash_dynamic\discovery_003\loaded_ecuflash_image.bin
; SHA256 1c9b664dd8c27bc0db4fdc3dcb07e8b8e3e8abd39152c4f89f8367e508380c18; capture base 0x00E80000; addresses below are RVAs
00041ac0 b82c100000               mov eax, 0x102c
00041ac5 e866387d00               call 0x1695330
00041aca a1c04ba701               mov eax, dword ptr [0x1a74bc0]
00041acf 33c4                     xor eax, esp
00041ad1 89842428100000           mov dword ptr [esp + 0x1028], eax
00041ad8 56                       push esi
00041ad9 57                       push edi
00041ada 8d442408                 lea eax, [esp + 8]
00041ade c744240820100000         mov dword ptr [esp + 8], 0x1020
00041ae6 50                       push eax
00041ae7 8d442414                 lea eax, [esp + 0x14]
00041aeb 8bf9                     mov edi, ecx
00041aed 50                       push eax
00041aee 6a00                     push 0
00041af0 6a00                     push 0
00041af2 51                       push ecx
00041af3 8bf4                     mov esi, esp
00041af5 6a12                     push 0x12
00041af7 68c8286f01               push 0x16f28c8
00041afc e8efde6500               call 0x151f9f0
00041b01 83c408                   add esp, 8
00041b04 8906                     mov dword ptr [esi], eax
00041b06 8bcf                     mov ecx, edi
00041b08 e8430c0000               call 0xec2750
00041b0d 8b8c2430100000           mov ecx, dword ptr [esp + 0x1030]
00041b14 5f                       pop edi
00041b15 5e                       pop esi
00041b16 33cc                     xor ecx, esp
00041b18 e857137d00               call 0x1692e74
00041b1d 81c42c100000             add esp, 0x102c
00041b23 c3                       ret 
