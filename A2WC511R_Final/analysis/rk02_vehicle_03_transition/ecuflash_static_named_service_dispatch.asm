; Input C:\Dev\Astra_A2WC511R\work\ecuflash_dynamic\discovery_003\loaded_ecuflash_image.bin
; SHA256 1c9b664dd8c27bc0db4fdc3dcb07e8b8e3e8abd39152c4f89f8367e508380c18; capture base 0x00E80000; addresses below are RVAs
00042750 6aff                     push -1
00042752 68101d6c01               push 0x16c1d10
00042757 64a100000000             mov eax, dword ptr fs:[0]
0004275d 50                       push eax
0004275e 51                       push ecx
0004275f 53                       push ebx
00042760 56                       push esi
00042761 57                       push edi
00042762 a1c04ba701               mov eax, dword ptr [0x1a74bc0]
00042767 33c4                     xor eax, esp
00042769 50                       push eax
0004276a 8d442414                 lea eax, [esp + 0x14]
0004276e 64a300000000             mov dword ptr fs:[0], eax
00042774 8bd9                     mov ebx, ecx
00042776 8b432c                   mov eax, dword ptr [ebx + 0x2c]
00042779 83cfff                   or edi, 0xffffffff
0004277c c744241c00000000         mov dword ptr [esp + 0x1c], 0
00042784 8b00                     mov eax, dword ptr [eax]
00042786 8b480c                   mov ecx, dword ptr [eax + 0xc]
00042789 85c9                     test ecx, ecx
0004278b 0f8481000000             je 0xec2812
00042791 8d442424                 lea eax, [esp + 0x24]
00042795 50                       push eax
00042796 e895e32500               call 0x1120b30
0004279b 85c0                     test eax, eax
0004279d 7473                     je 0xec2812
0004279f 83c00c                   add eax, 0xc
000427a2 50                       push eax
000427a3 8d442428                 lea eax, [esp + 0x28]
000427a7 50                       push eax
000427a8 e863a36500               call 0x151cb10
000427ad 83c408                   add esp, 8
000427b0 84c0                     test al, al
000427b2 755e                     jne 0xec2812
000427b4 8b432c                   mov eax, dword ptr [ebx + 0x2c]
000427b7 8b00                     mov eax, dword ptr [eax]
000427b9 8b480c                   mov ecx, dword ptr [eax + 0xc]
000427bc 85c9                     test ecx, ecx
000427be 742e                     je 0xec27ee
000427c0 8d442424                 lea eax, [esp + 0x24]
000427c4 50                       push eax
000427c5 e866e32500               call 0x1120b30
000427ca 8bf0                     mov esi, eax
000427cc 85f6                     test esi, esi
000427ce 741e                     je 0xec27ee
000427d0 8d4e0c                   lea ecx, [esi + 0xc]
000427d3 51                       push ecx
000427d4 8d442428                 lea eax, [esp + 0x28]
000427d8 50                       push eax
000427d9 e832a36500               call 0x151cb10
000427de 83c408                   add esp, 8
000427e1 84c0                     test al, al
000427e3 7509                     jne 0xec27ee
000427e5 8a4610                   mov al, byte ptr [esi + 0x10]
000427e8 88442410                 mov byte ptr [esp + 0x10], al
000427ec eb05                     jmp 0xec27f3
000427ee c644241000               mov byte ptr [esp + 0x10], 0
000427f3 ff742434                 push dword ptr [esp + 0x34]
000427f7 8bcb                     mov ecx, ebx
000427f9 ff742434                 push dword ptr [esp + 0x34]
000427fd ff742434                 push dword ptr [esp + 0x34]
00042801 ff742434                 push dword ptr [esp + 0x34]
00042805 ff742420                 push dword ptr [esp + 0x20]
00042809 e8c2fcffff               call 0xec24d0
0004280e 8ad8                     mov bl, al
00042810 eb6b                     jmp 0xec287d
00042812 8b0da01ea801             mov ecx, dword ptr [0x1a81ea0]
00042818 8d4908                   lea ecx, [ecx + 8]
0004281b e810ef6800               call 0x1551730
00042820 84c0                     test al, al
00042822 7457                     je 0xec287b
00042824 8d442434                 lea eax, [esp + 0x34]
00042828 50                       push eax
00042829 8d4c2428                 lea ecx, [esp + 0x28]
0004282d e82e116700               call 0x1533960
00042832 8b00                     mov eax, dword ptr [eax]
00042834 c644241c01               mov byte ptr [esp + 0x1c], 1
00042839 8b480c                   mov ecx, dword ptr [eax + 0xc]
0004283c 03c8                     add ecx, eax
0004283e 51                       push ecx
0004283f 68f4376f01               push 0x16f37f4
00042844 ff33                     push dword ptr [ebx]
00042846 e805120500               call 0xf13a50
0004284b 8b442440                 mov eax, dword ptr [esp + 0x40]
0004284f 83c40c                   add esp, 0xc
00042852 8b08                     mov ecx, dword ptr [eax]
00042854 85c9                     test ecx, ecx
00042856 7416                     je 0xec286e
00042858 83f9ff                   cmp ecx, -1
0004285b 741e                     je 0xec287b
0004285d 8bcf                     mov ecx, edi
0004285f f00fc108                 lock xadd dword ptr [eax], ecx
00042863 0f95c0                   setne al
00042866 84c0                     test al, al
00042868 7511                     jne 0xec287b
0004286a 8b442434                 mov eax, dword ptr [esp + 0x34]
0004286e 6a04                     push 4
00042870 6a01                     push 1
00042872 50                       push eax
00042873 e8c8716500               call 0x1519a40
00042878 83c40c                   add esp, 0xc
0004287b 32db                     xor bl, bl
0004287d 8b442424                 mov eax, dword ptr [esp + 0x24]
00042881 8b08                     mov ecx, dword ptr [eax]
00042883 85c9                     test ecx, ecx
00042885 7415                     je 0xec289c
00042887 83f9ff                   cmp ecx, -1
0004288a 741d                     je 0xec28a9
0004288c f00fc138                 lock xadd dword ptr [eax], edi
00042890 4f                       dec edi
00042891 0f95c0                   setne al
00042894 84c0                     test al, al
00042896 7511                     jne 0xec28a9
00042898 8b442424                 mov eax, dword ptr [esp + 0x24]
0004289c 6a04                     push 4
0004289e 6a02                     push 2
000428a0 50                       push eax
000428a1 e89a716500               call 0x1519a40
000428a6 83c40c                   add esp, 0xc
000428a9 8ac3                     mov al, bl
000428ab 8b4c2414                 mov ecx, dword ptr [esp + 0x14]
000428af 64890d00000000           mov dword ptr fs:[0], ecx
000428b6 59                       pop ecx
000428b7 5f                       pop edi
000428b8 5e                       pop esi
000428b9 5b                       pop ebx
000428ba 83c410                   add esp, 0x10
000428bd c21400                   ret 0x14
