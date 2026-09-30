; Input C:\Dev\Astra_A2WC511R\work\ecuflash_dynamic\discovery_003\loaded_ecuflash_image.bin
; SHA256 1c9b664dd8c27bc0db4fdc3dcb07e8b8e3e8abd39152c4f89f8367e508380c18; capture base 0x00E80000; addresses below are RVAs
00096920 56                       push esi
00096921 8bf1                     mov esi, ecx
00096923 57                       push edi
00096924 8d4e24                   lea ecx, [esi + 0x24]
00096927 e8d43afaff               call 0xeba400
0009692c 84c0                     test al, al
0009692e 746f                     je 0xf1699f
00096930 8b06                     mov eax, dword ptr [esi]
00096932 8bce                     mov ecx, esi
00096934 8b4008                   mov eax, dword ptr [eax + 8]
00096937 ffd0                     call eax
00096939 84c0                     test al, al
0009693b 7462                     je 0xf1699f
0009693d 8b06                     mov eax, dword ptr [esi]
0009693f 8bce                     mov ecx, esi
00096941 8b00                     mov eax, dword ptr [eax]
00096943 ffd0                     call eax
00096945 84c0                     test al, al
00096947 7410                     je 0xf16959
00096949 6818ba6f01               push 0x16fba18
0009694e ff7614                   push dword ptr [esi + 0x14]
00096951 e8fad0ffff               call 0xf13a50
00096956 83c408                   add esp, 8
00096959 6a00                     push 0
0009695b 6a00                     push 0
0009695d 6a07                     push 7
0009695f ffb668020000             push dword ptr [esi + 0x268]
00096965 8d4e24                   lea ecx, [esi + 0x24]
00096968 c786b012000000000000     mov dword ptr [esi + 0x12b0], 0
00096972 c786b412000000000000     mov dword ptr [esi + 0x12b4], 0
0009697c e88f25faff               call 0xeb8f10
00096981 85c0                     test eax, eax
00096983 751a                     jne 0xf1699f
00096985 50                       push eax
00096986 50                       push eax
00096987 6a08                     push 8
00096989 ffb668020000             push dword ptr [esi + 0x268]
0009698f 8d4e24                   lea ecx, [esi + 0x24]
00096992 e87925faff               call 0xeb8f10
00096997 85c0                     test eax, eax
00096999 5f                       pop edi
0009699a 0f94c0                   sete al
0009699d 5e                       pop esi
0009699e c3                       ret 
0009699f 5f                       pop edi
000969a0 32c0                     xor al, al
000969a2 5e                       pop esi
000969a3 c3                       ret 
