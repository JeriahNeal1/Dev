; Input C:\Dev\Astra_A2WC511R\work\ecuflash_dynamic\discovery_003\loaded_ecuflash_image.bin
; SHA256 1c9b664dd8c27bc0db4fdc3dcb07e8b8e3e8abd39152c4f89f8367e508380c18; capture base 0x00E80000; addresses below are RVAs
000424d0 56                       push esi
000424d1 ff742410                 push dword ptr [esp + 0x10]
000424d5 8bf1                     mov esi, ecx
000424d7 ff742410                 push dword ptr [esp + 0x10]
000424db ff742410                 push dword ptr [esp + 0x10]
000424df 6a01                     push 1
000424e1 e87a0f0000               call 0xec3460
000424e6 84c0                     test al, al
000424e8 7526                     jne 0xec2510
000424ea a1a01ea801               mov eax, dword ptr [0x1a81ea0]
000424ef 8d4808                   lea ecx, [eax + 8]
000424f2 e839f26800               call 0x1551730
000424f7 84c0                     test al, al
000424f9 740f                     je 0xec250a
000424fb 6814386f01               push 0x16f3814
00042500 ff36                     push dword ptr [esi]
00042502 e849150500               call 0xf13a50
00042507 83c408                   add esp, 8
0004250a 32c0                     xor al, al
0004250c 5e                       pop esi
0004250d c21400                   ret 0x14
00042510 8a461c                   mov al, byte ptr [esi + 0x1c]
00042513 57                       push edi
00042514 8b7c241c                 mov edi, dword ptr [esp + 0x1c]
00042518 84c0                     test al, al
0004251a 0f94442414               sete byte ptr [esp + 0x14]
0004251f 8b0f                     mov ecx, dword ptr [edi]
00042521 894c241c                 mov dword ptr [esp + 0x1c], ecx
00042525 84c0                     test al, al
00042527 0f84e5000000             je 0xec2612
0004252d 53                       push ebx
0004252e 8b5c241c                 mov ebx, dword ptr [esp + 0x1c]
00042532 55                       push ebp
00042533 890f                     mov dword ptr [edi], ecx
00042535 8b4604                   mov eax, dword ptr [esi + 4]
00042538 85c0                     test eax, eax
0004253a 741b                     je 0xec2557
0004253c 83780806                 cmp dword ptr [eax + 8], 6
00042540 0f94c0                   sete al
00042543 84c0                     test al, al
00042545 7510                     jne 0xec2557
00042547 57                       push edi
00042548 53                       push ebx
00042549 8d442420                 lea eax, [esp + 0x20]
0004254d 8bce                     mov ecx, esi
0004254f 50                       push eax
00042550 e88b080000               call 0xec2de0
00042555 eb0e                     jmp 0xec2565
00042557 57                       push edi
00042558 53                       push ebx
00042559 8d442420                 lea eax, [esp + 0x20]
0004255d 8bce                     mov ecx, esi
0004255f 50                       push eax
00042560 e8bb090000               call 0xec2f20
00042565 84c0                     test al, al
00042567 0f8482000000             je 0xec25ef
0004256d ff37                     push dword ptr [edi]
0004256f 8bce                     mov ecx, esi
00042571 53                       push ebx
00042572 ff742420                 push dword ptr [esp + 0x20]
00042576 e875faffff               call 0xec1ff0
0004257b 8b542414                 mov edx, dword ptr [esp + 0x14]
0004257f 8b4c2418                 mov ecx, dword ptr [esp + 0x18]
00042583 0fb6c2                   movzx eax, dl
00042586 0fb6e9                   movzx ebp, cl
00042589 83c040                   add eax, 0x40
0004258c 3be8                     cmp ebp, eax
0004258e 7458                     je 0xec25e8
00042590 80f97f                   cmp cl, 0x7f
00042593 7424                     je 0xec25b9
00042595 8b0da01ea801             mov ecx, dword ptr [0x1a81ea0]
0004259b 8d4908                   lea ecx, [ecx + 8]
0004259e e88df16800               call 0x1551730
000425a3 84c0                     test al, al
000425a5 7431                     je 0xec25d8
000425a7 55                       push ebp
000425a8 6860386f01               push 0x16f3860
000425ad ff36                     push dword ptr [esi]
000425af e89c140500               call 0xf13a50
000425b4 83c40c                   add esp, 0xc
000425b7 eb1f                     jmp 0xec25d8
000425b9 833f02                   cmp dword ptr [edi], 2
000425bc 7252                     jb 0xec2610
000425be 3813                     cmp byte ptr [ebx], dl
000425c0 754e                     jne 0xec2610
000425c2 8a4301                   mov al, byte ptr [ebx + 1]
000425c5 3c78                     cmp al, 0x78
000425c7 7404                     je 0xec25cd
000425c9 3c23                     cmp al, 0x23
000425cb 7543                     jne 0xec2610
000425cd 8b4e04                   mov ecx, dword ptr [esi + 4]
000425d0 ff7624                   push dword ptr [esi + 0x24]
000425d3 8b01                     mov eax, dword ptr [ecx]
000425d5 ff5068                   call dword ptr [eax + 0x68]
000425d8 807e1c00                 cmp byte ptr [esi + 0x1c], 0
000425dc 8b4c2424                 mov ecx, dword ptr [esp + 0x24]
000425e0 0f854dffffff             jne 0xec2533
000425e6 eb28                     jmp 0xec2610
000425e8 c644241c01               mov byte ptr [esp + 0x1c], 1
000425ed eb21                     jmp 0xec2610
000425ef 8b0da01ea801             mov ecx, dword ptr [0x1a81ea0]
000425f5 8d4908                   lea ecx, [ecx + 8]
000425f8 e833f16800               call 0x1551730
000425fd 84c0                     test al, al
000425ff 740f                     je 0xec2610
00042601 6838386f01               push 0x16f3838
00042606 ff36                     push dword ptr [esi]
00042608 e843140500               call 0xf13a50
0004260d 83c408                   add esp, 8
00042610 5d                       pop ebp
00042611 5b                       pop ebx
00042612 8b4e04                   mov ecx, dword ptr [esi + 4]
00042615 ff7620                   push dword ptr [esi + 0x20]
00042618 8b11                     mov edx, dword ptr [ecx]
0004261a ff5268                   call dword ptr [edx + 0x68]
0004261d 8a442414                 mov al, byte ptr [esp + 0x14]
00042621 5f                       pop edi
00042622 5e                       pop esi
00042623 c21400                   ret 0x14
