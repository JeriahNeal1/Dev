; Input C:\Dev\Astra_A2WC511R\work\ecuflash_dynamic\discovery_003\loaded_ecuflash_image.bin
; SHA256 1c9b664dd8c27bc0db4fdc3dcb07e8b8e3e8abd39152c4f89f8367e508380c18; capture base 0x00E80000; addresses below are RVAs
0009b5fe 8b4f0c                   mov ecx, dword ptr [edi + 0xc]
0009b601 e8ba64faff               call 0xec1ac0
0009b606 84c0                     test al, al
0009b608 0f84ebfeffff             je 0xf1b4f9
0009b60e 8b4f0c                   mov ecx, dword ptr [edi + 0xc]
0009b611 8d442428                 lea eax, [esp + 0x28]
0009b615 50                       push eax
0009b616 8d442440                 lea eax, [esp + 0x40]
0009b61a c744242c20100000         mov dword ptr [esp + 0x2c], 0x1020
0009b622 50                       push eax
0009b623 6a00                     push 0
0009b625 6a00                     push 0
0009b627 6a00                     push 0
0009b629 e89260faff               call 0xec16c0
0009b62e 84c0                     test al, al
0009b630 0f84c3feffff             je 0xf1b4f9
0009b636 8bcf                     mov ecx, edi
0009b638 e893f9ffff               call 0xf1afd0
0009b63d 84c0                     test al, al
0009b63f 0f84b4feffff             je 0xf1b4f9
0009b645 8b4f04                   mov ecx, dword ptr [edi + 4]
0009b648 68c8000000               push 0xc8
0009b64d e84e9cffff               call 0xf152a0
0009b652 8b4f04                   mov ecx, dword ptr [edi + 4]
0009b655 68d0070000               push 0x7d0
0009b65a 8b01                     mov eax, dword ptr [ecx]
0009b65c ff5068                   call dword ptr [eax + 0x68]
0009b65f 33c0                     xor eax, eax
0009b661 c644241802               mov byte ptr [esp + 0x18], 2
0009b666 6a01                     push 1
0009b668 668944241d               mov word ptr [esp + 0x1d], ax
0009b66d 8844241f                 mov byte ptr [esp + 0x1f], al
0009b671 8d44241c                 lea eax, [esp + 0x1c]
0009b675 50                       push eax
0009b676 51                       push ecx
0009b677 8bf4                     mov esi, esp
0009b679 6a12                     push 0x12
0009b67b 68e0296f01               push 0x16f29e0
0009b680 e86b436000               call 0x151f9f0
0009b685 83c408                   add esp, 8
0009b688 8906                     mov dword ptr [esi], eax
0009b68a 8b4f0c                   mov ecx, dword ptr [edi + 0xc]
0009b68d e84e65faff               call 0xec1be0
0009b692 84c0                     test al, al
0009b694 0f845ffeffff             je 0xf1b4f9
0009b69a 837f1c01                 cmp dword ptr [edi + 0x1c], 1
0009b69e b8093d0000               mov eax, 0x3d09
0009b6a3 7505                     jne 0xf1b6aa
0009b6a5 b880250000               mov eax, 0x2580
0009b6aa 8b4f04                   mov ecx, dword ptr [edi + 4]
0009b6ad 6a64                     push 0x64
0009b6af 898720140000             mov dword ptr [edi + 0x1420], eax
0009b6b5 e8e69bffff               call 0xf152a0
0009b6ba 8b4f04                   mov ecx, dword ptr [edi + 4]
0009b6bd ffb720140000             push dword ptr [edi + 0x1420]
0009b6c3 8b01                     mov eax, dword ptr [ecx]
0009b6c5 ff5034                   call dword ptr [eax + 0x34]
0009b6c8 c7471803000000           mov dword ptr [edi + 0x18], 3
0009b6cf b001                     mov al, 1
0009b6d1 8b8c2460100000           mov ecx, dword ptr [esp + 0x1060]
0009b6d8 64890d00000000           mov dword ptr fs:[0], ecx
0009b6df 59                       pop ecx
0009b6e0 5f                       pop edi
0009b6e1 5e                       pop esi
0009b6e2 5d                       pop ebp
0009b6e3 5b                       pop ebx
0009b6e4 8b8c2448100000           mov ecx, dword ptr [esp + 0x1048]
0009b6eb 33cc                     xor ecx, esp
0009b6ed e882777700               call 0x1692e74
0009b6f2 81c458100000             add esp, 0x1058
