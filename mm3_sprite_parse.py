import struct
import os
from PIL import Image

PATTERN_STEPS = [0, 1, 1, 1, 2, 2, 3, 3, 0, -1, -1, -1, -2, -2, -3, -3]

Test = False
Transcode = False

def decompress_cell(data, offset, is_mm3=False, transcode_data=None):
    if offset == 0 or offset >= len(data): return None, 0, 0, (0,0)
    
    # Cell Header (8 bytes)
    x_off, width, y_off, height = struct.unpack("<HHHH", data[offset:offset+8])
    total_w, total_h = x_off + width, y_off + height
    print("cell info:")
    print(f"x_off: {x_off}")
    print(f"width: {width}")
    print(f"y_off: {y_off}")
    print(f"height: {height}")
    print(f"total_w: {total_w}")
    print(f"total_h: {total_h}")

    if transcode_data:
        transcode_data += data[offset:offset+8]

    pixels = bytearray([0] * (total_w * total_h))

    dp = offset + 8
    y_pos = y_off
    
    while y_pos < total_h and dp < len(data):
        print(f"line: {y_pos}")
        # LINE HEADER DIFFERENTIATION
        if is_mm3:
            # MM3 uses 16-bit Length and 16-bit X-Skip
            line_len = struct.unpack("<H", data[dp:dp+2])[0]
            if transcode_data:
                transcode_data += data[dp:dp+1]
            dp += 2
            if transcode_data:
                transcode_data += data[dp:dp+1]
            if line_len == 0: # MM3 vertical skip
                if dp < len(data):
                    print(f"vskip {data[dp]}")
                    if data[dp]:
                        y_pos += data[dp]
                        dp += 1
                    else:
                        print("ZERO VSKIP, STOPPING")
                        break
                continue
            line_end = dp + line_len
            line_x_off = struct.unpack("<H", data[dp:dp+2])[0]
            x_pos = line_x_off + x_off
            print(f"mm3_len {line_len} mm3_off {line_x_off}")
            if x_pos > total_w:
                print("ERROR - ENDING CELL")
                break
            dp += 2
        else:
            # Xeen uses 8-bit Length and 8-bit X-Skip
            line_len = data[dp]
            dp += 1
            if line_len == 0: # Xeen vertical skip
                y_pos += data[dp]
                dp += 1
                continue
            line_end = dp + line_len
            x_pos = data[dp] + x_off
            dp += 1

        while dp < line_end and dp < len(data):
            opcode = data[dp]
            dp += 1
            cmd = (opcode & 0xE0) >> 5
            length = opcode & 0x1F
            
            def put(color, count=1):
                nonlocal x_pos
                print(f"put color {color} count {count} @x {x_pos}")
                for _ in range(count):
                    if 0 <= x_pos < total_w and 0 <= y_pos < total_h:
                        pixels[y_pos * total_w + x_pos] = color
                        x_pos += 1
                    else:
                        print("ERROR put color - out of bounds")

            print("Processing cmd opcode: "+str(cmd)+" ("+str(opcode)+")")

            if cmd == 0:
                count = (opcode + 1)
                for _ in range(count):
                    if dp < len(data):
                        if Test:
                            put(200); dp += 1 #red (one pix)
                        else:
                            put(data[dp]); dp += 1
            elif cmd == 1:
                count = (opcode + 1)#33?
                for _ in range(count):
                    if dp < len(data):
                        if Test:
                            put(201); dp += 1 #green (multi pix)
                        else:
                            put(data[dp]); dp += 1
            elif cmd == 2:
                print("STOP?")
                break

                # color = data[dp]; dp += 1
                # if Test:
                #     put(color, length + 3) # (three pix?)
                # else:
                #     put(color, length + 3)
            elif cmd == 3:
                back_off = struct.unpack("<H", data[dp:dp+2])[0]; dp += 2
                src = dp - back_off
                for i in range(length + 4):
                    if 0 <= src + i < len(data): put(data[src + i]) #stream copy
            # elif cmd == 4:
            #     c1, c2 = data[dp], data[dp+1]; dp += 2
            #     if Test:
            #         for _ in range(length + 2): put(203); put(204) #pair
            #     else:
            #         for _ in range(length + 2): put(c1); put(c2)
            elif cmd == 4:
                for _ in range(length + 1):
                    if Test:
                        put(203, 1) #yellow ("mm4 pair") - for mm3 skip 1?
                    else:
                        x_pos += 1
            elif cmd == 5:
                if Test:
                    put(204, length + 33) #cyan (skip)
                else:
                    x_pos += (length + 33)
            elif cmd == 6:
                color = data[dp]; dp += 1
                if Test:
                    put(205, length + 3) # (three pix?)
                else:
                    put(color, length + 3)
            elif cmd == 7:
                val = data[dp]; dp += 1
                idx = (opcode >> 2) & 0x0E
                s1, s2 = PATTERN_STEPS[idx], PATTERN_STEPS[(idx+1)%16]

                for i in range((opcode & 0x07) + 3):
                    if Test:
                        put(202) #blue (pattern)
                    else:
                        put(val & 0xFF)
                    val += s1 if (i % 2 == 0) else s2
            else:
                print("UNHANDLED OPCODE!")

            print(f"command processed; dp: {dp}")
        
        dp = line_end
        y_pos += 1
            
    print(f"Processed cell {total_w}x{total_h}, ({x_off}, {y_off})")
    return pixels, total_w, total_h, (x_off, y_off)

def hex_palette():
    #mm4
    # hex_pal = "0000003F 3F3F3D3D 3D3B3B3B 39393937 37373535 35333333 3131312F 2F2F2D2D 2D2B2B2B 29292927 27272525 25232323 2121211F 1F1F1D1D 1D1B1B1B 19191917 17171515 15131313 1111110F 0F0F0D0D 0D0B0B0B 09090907 07070505 05030303 383B3F33 393F2D35 3F27303F 212B3F1C 253F161F 3F10183F 0A103F07 0C390509 3404072E 02042901 02230001 1E000018 3E3F303D 3F293D3F 223D3F1B 3B3E133A 3C0F3839 0B363708 3233042F 30012C2B 00272500 2220001C 1A001715 00131000 313A3F2B 373E2534 3D1F313D 192F3C14 2C3B0E29 3B09263A 04243900 2139001E 34001B2F 00172900 14240011 1E000E19 353E3330 3E2D2B3E 27263E21 203D1A1A 3B141538 0E0E3608 0D34060B 3004092C 03072802 05240104 2000031C 00021800 2F3E3F2A 3B3C2638 39223536 1E32331A 3030172D 2D142A2B 1128280F 24250E21 220C1D1F 0B1A1C09 17190814 16071113 3C363F39 2E3E3627 3D33203C 30193C2D 123B2B0B 3A280539 24003722 00341E00 2F1A002A 17002513 00201000 1B0D0016 3F363F3E 2E3E3D27 3D3C203C 3B193C3A 123B3A0B 3A370538 35003633 00342E00 2F29002A 2400251F 00201B00 1B160016 3F3A373D 37343C35 313B332E 3A312B39 2E28372C 25362A23 35282034 261E3324 1B312319 3021172F 1F152E1D 132D1C11 2B1B1029 1A0F2819 0E26180E 24170D23 160C2115 0C20140B 1E130A1C 120A1B11 09191008 170F0816 0E07140D 06130C06 3F35353D 2E2E3B28 283A2222 381C1C36 17173511 11330C0C 32080830 05052E02 022A0000 25000020 00001B00 00160000 3F372F3F 34293F31 233F2E1D 3F2C173F 29113F26 0B3E2305 3B200237 1E01331B 002D1800 27140021 11001B0E 00160B00 313E0D2D 3A0A2A37 08263405 23300320 2D021D2A 001A2700 11240008 2200011F 00001D02 001A0700 180B0015 0E001311 100B070C 09071620 03091002 060F1105 0D0F3B3A 00373400 342F0031 2A002E26 002B2200 271E0024 1A002116 001E1300 3F27003F 2C003F31 003F3600 3F3C003D 3F003F39 003F3200 3F2B003F 23003F1C 003F1500 3F0D003F 06003F00 003F3F3F"
    #mirror
    # hex_pal = "0000003F 3F3F3D3D 3D3B3B3B 39393937 37373535 35333333 3131312F 2F2F2D2D 2D2B2B2B 29292927 27272525 25232323 2121211F 1F1F1D1D 1D1B1B1B 19191917 17171515 15131313 1111110F 0F0F0D0D 0D0B0B0B 09090907 07070505 05030303 383B3F33 393F2D35 3F27303F 212B3F1C 253F161F 3F10183F 0A103F07 0C390509 3404072E 02042901 02230001 1E000018 3E3F303D 3F293D3F 223D3F1B 3B3E133A 3C0F3839 0B363708 3233042F 30012C2B 00272500 2220001C 1A001715 00131000 313A3F2B 373E2534 3D1F313D 192F3C14 2C3B0E29 3B09263A 04243900 2139001E 34001B2F 00172900 14240011 1E000E19 353E3330 3E2D2B3E 27263E21 203D1A1A 3B141538 0E0E3608 0D34060B 3004092C 03072802 05240104 2000031C 00021800 2F3E3F2A 3B3C2638 39223536 1E32331A 3030172D 2D142A2B 1128280F 24250E21 220C1D1F 0B1A1C09 17190814 16071113 3C363F39 2E3E3627 3D33203C 30193C2D 123B2B0B 3A280539 24003722 00341E00 2F1A002A 17002513 00201000 1B0D0016 3F363F3E 2E3E3D27 3D3C203C 3B193C3A 123B3A0B 3A370538 35003633 00342E00 2F29002A 2400251F 00201B00 1B160016 3F3A373D 37343C35 313B332E 3A312B39 2E28372C 25362A23 35282034 261E3324 1B312319 3021172F 1F152E1D 132D1C11 2B1B1029 1A0F2819 0E26180E 24170D23 160C2115 0C20140B 1E130A1C 120A1B11 09191008 170F0816 0E07140D 06130C06 3F35353D 2E2E3B28 283A2222 381C1C36 17173511 11330C0C 32080830 05052E02 022A0000 25000020 00001B00 00160000 3F372F3F 34293F31 233F2E1D 3F2C173F 29113F26 0B3E2305 3B200237 1E01331B 002D1800 27140021 11001B0E 00160B00 313E0D2D 3A0A2A37 08263405 23300320 2D021D2A 001A2700 11240008 2200011F 00001D02 001A0700 180B0015 0E001311 100B070C 09071620 03091002 060F1105 0D0F3B3A 00373400 342F0031 2A002E26 002B2200 271E0024 1A002116 001E1300 3F27003F 2C003F31 003F3600 3F3C003D 3F003F39 003F3200 3F2B003F 23003F1C 003F1500 3F0D003F 06003F00 003F3F3F"
    #dark
    hex_pal = "0000003F 3F3F3D3D 3D3B3B3B 39393937 37373535 35333333 3131312F 2F2F2D2D 2D2B2B2B 29292927 27272525 25232323 2121211F 1F1F1D1D 1D1B1B1B 19191917 17171515 15131313 1111110F 0F0F0D0D 0D0B0B0B 09090907 07070505 05030303 383B3F33 393F2D35 3F27303F 212B3F1C 253F161F 3F10183F 0A103F07 0C390509 3404072E 02042901 02230001 1E000018 3E3F303D 3F293D3F 223D3F1B 3B3E133A 3C0F3839 0B363708 3233042F 30012C2B 00272500 2220001C 1A001715 00131000 313A3F2B 373E2534 3D1F313D 192F3C14 2C3B0E29 3B09263A 04243900 2139001E 34001B2F 00172900 14240011 1E000E19 353E3330 3E2D2B3E 27263E21 203D1A1A 3B141538 0E0E3608 0D34060B 3004092C 03072802 05240104 2000031C 00021800 2F3E3F2A 3B3C2638 39223536 1E32331A 3030172D 2D142A2B 1128280F 24250E21 220C1D1F 0B1A1C09 17190814 16071113 3C363F39 2E3E3627 3D33203C 30193C2D 123B2B0B 3A280539 24003722 00341E00 2F1A002A 17002513 00201000 1B0D0016 3F363F3E 2E3E3D27 3D3C203C 3B193C3A 123B3A0B 3A370538 35003633 00342E00 2F29002A 2400251F 00201B00 1B160016 3F3A373D 37343C35 313B332E 3A312B39 2E28372C 25362A23 35282034 261E3324 1B312319 3021172F 1F152E1D 132D1C11 2B1B1029 1A0F2819 0E26180E 24170D23 160C2115 0C20140B 1E130A1C 120A1B11 09191008 170F0816 0E07140D 06130C06 3F35353D 2E2E3B28 283A2222 381C1C36 17173511 11330C0C 32080830 05052E02 022A0000 25000020 00001B00 00160000 3F372F3F 34293F31 233F2E1D 3F2C173F 29113F26 0B3E2305 3B200237 1E01331B 002D1800 27140021 11001B0E 00160B00 313E0D2D 3A0A2A37 08263405 23300320 2D021D2A 001A2700 11240008 2200011F 00001D02 001A0700 180B0015 0E001311 100B070C 09071620 03091002 060F1105 0D0F3F3A 00393300 3F00003F 04003F09 003F0E00 3F13003F 18003F1D 003F2200 3F27003F 2C003F31 003F3600 3F3C003D 3F003F39 003F3200 3F2B003F 23003F1C 003F1500 3F0D003F 06003F00 003F3F3F"
    #mm4e
    # hex_pal = "0000003F 3F3F3D3D 3D3B3B3B 39393937 37373535 35333333 3131312F 2F2F2D2D 2D2B2B2B 29292927 27272525 25232323 2121211F 1F1F1D1D 1D1B1B1B 19191917 17171515 15131313 1111110F 0F0F0D0D 0D0B0B0B 09090907 07070505 05030303 383B3F33 393F2D35 3F27303F 212B3F1C 253F161F 3F10183F 0A103F07 0C390509 3404072E 02042901 02230001 1E000018 3F3E323E 3D2B3D3C 243D3C1D 3C3B1636 3A0F3538 09343603 33350231 33012E30 012D2C00 29280025 2200201E 001B1900 313A3F2B 373E2534 3D1F313D 192F3C14 2C3B0E29 3B09263A 04243900 2139001E 34001B2F 00172900 14240011 1E000E19 353E3330 3E2D2B3E 27263E21 203D1A1A 3B141538 0E0E3608 0D34060A 31050A2F 04082B02 06260104 2201031E 00021800 2F3E3F27 3B3C2038 3A193638 1333360D 3033082E 31032B2F 00292D01 25290321 25051E21 061B1E07 171A0714 16071113 3C363F39 2E3E3627 3D33203C 30193C2D 123B2B0B 3A280539 24003722 00341E00 2F1A002A 17002513 00201000 1B0D0016 3F363F3E 2E3E3D27 3D3C203C 3B193C3A 123B3A0B 3A370538 35003633 00342E00 2F29002A 2400251F 00201B00 1B160016 3F3A373D 37343C35 313B332E 3A312B39 2E28372C 25362A23 35282034 261E3324 1B312319 3021172F 1F152E1D 132D1C11 2B1B1029 1A0F2819 0E26180E 24170D23 160C2115 0C20140B 1E130A1C 120A1B11 09191008 170F0816 0E07140D 06130C06 3F35353E 2D2D3D26 263C1F1F 3B19193A 1212390C 0C380606 34000031 01012E02 022A0000 25000020 00001B00 00160000 22333A1C 3038182D 36112A35 1128330A 26320724 3009212F 02202C01 1E2A011C 28011A26 00192400 17220015 2000141E 003C3800 38350035 3200322F 002F2C00 2C290029 26002623 00242100 221F0020 1D001E1C 001C1A00 1A180018 16001715 3F3C033F 39033F36 043F3103 3F2B033F 26033F21 033F1B03 3F16033F 11033F18 033F2003 3F28033F 2F033F37 033F3F03 3F2D003B 22003718 01331001 2F09022B 03032F07 02330D01 3714013B 1B003F24 003F2E04 3F36093F 3E0E3F36 063F3F3F"

    #MM3?!
    hex_pal = "0000003F 3F3F3C3C 3C3A3A3A 38383835 35353333 33313131 2F2F2F2C 2C2C2A2A 2A282828 25252523 23232121 211F1F1F 1D1D1D1B 1B1B1919 19171717 15151513 13131111 110F0F0F 0D0D0D0B 0B0B0909 09070707 05050503 03030101 01000000 3F3A3A3E 35353D30 303C2C2C 3B28283A 2323391F 1F391B1B 38171737 13133610 10350C0C 34080833 05053202 02320000 2E00002A 00002600 00210000 1D000019 00001500 00110000 0D00003F 1D003719 00301600 28120021 0F00190B 00120800 3F3F363F 3F2E3E3F 263E3F1E 3E3F163D 3F0E3D3F 063B3D00 3B3B0038 37003533 00322E00 2F2A002C 26002922 00261F00 221A001E 16001A12 00160F00 120B000E 08000A05 00060300 363F1631 3B112D38 0D29340A 25310621 2D031D2A 011A2700 15240013 2100121F 00111D00 101B000E 19000D17 000C1500 0B13002F 3E2F273C 26203A1F 17381710 37100B35 0A0A3209 082F0807 2D07062A 06052704 04240403 2203021F 02021C02 011A0101 17010114 00001100 000F0000 0C000009 00000700 3C3C3F38 383F3333 3F2F2F3F 2B2C3F27 283F2323 3F1F203F 1B1C3F17 183F1314 3F0F103F 0B0C3F07 083F0304 3F00013F 00003F00 003B0000 37000033 00002F00 002B0000 27000024 00002000 001C0000 18000014 00001000 000C0000 08000005 3C363F39 2E3F3627 3F341F3F 32173F2F 103F2D08 3F2A003F 26003920 00321B00 2B150023 0F001B0A 00140600 0C020005 333F3F2D 3B3B2738 38223535 1D323219 2F2F142B 2B112828 0D242409 1F1F071B 1B041717 02131301 0F0F000B 0B000707 3A3C3E36 3A3D3137 3D2D353D 29333C25 313C2130 3C1D2E3B 192C3B15 2B3B1129 3A0D283A 0A263A06 25390224 39012136 011F3300 1D30001B 2D00192B 00172800 15250014 2200121F 00101C00 0E18000C 15000A12 00080F00 060C0005 09000306 3F3A373F 37333F35 303F332C 3F31293F 2F253F2D 223F2B1F 3F291B3F 27183C25 173A2416 38221536 21143420 14321F13 2F1D112C 1B10291A 0E26180D 23160C20 150A1D13 091A1108 170F0714 0D06110C 050E0A03 0B080309 06020604 013F3F3F"

    raw_palette = bytes.fromhex(hex_pal)
    if max(raw_palette) <= 63:
        raw_palette = bytes([v * 4 for v in raw_palette])
    return raw_palette

def get_vga_default_palette():
    # 16 standard colors + grayscale + 216 color cube
    palette = []
    # Simplified version of the 6x6x6 color cube used in VGA
    for r in range(6):
        for g in range(6):
            for b in range(6):
                palette.extend([r*42, g*42, b*42])
    # Pad to 768 bytes if necessary
    return (palette + [0]*768)[:768]

def parse_sprite(filepath, out_dir, mode="xeen"):
    is_mm3 = (mode.lower() == "mm3")
    with open(filepath, "rb") as f:
        data = f.read()
    
    num_f = struct.unpack("<H", data[:2])[0]
    os.makedirs(out_dir, exist_ok=True)
    
    # Generic Palette (VGA index approximation)
    palette = [j for i in range(256) for j in (i, i, i)]
    if Test:
        palette[200*3+0]=255 #red
        palette[200*3+1]=0
        palette[200*3+2]=0

        palette[201*3+0]=0
        palette[201*3+1]=255 #green
        palette[201*3+2]=0

        palette[202*3+0]=0
        palette[202*3+1]=0
        palette[202*3+2]=255 #blue

        palette[203*3+0]=255 #red/green = yellow
        palette[203*3+1]=255
        palette[203*3+2]=0

        palette[204*3+0]=0
        palette[204*3+1]=255 #green/blue = cyan
        palette[204*3+2]=255

        palette[205*3+0]=255 #red/blue = pink
        palette[205*3+1]=0
        palette[205*3+2]=255
    else:
        palette = hex_palette()
        # palette = get_vga_default_palette()

        # print(palette)

    print("sprite TOC:")
    for i in range(num_f):
        o1, o2 = struct.unpack("<HH", data[2+i*4:6+i*4])
        print(f"Frame {i} cell {0} at {o1}")
        print(f"Frame {i} cell {1} at {o2}")

    if Transcode:
        #open out ccx file
        mm4_cells = []
        for i in range(num_f*2):
            mm4_cells.append(bytearray())
        


    for i in range(num_f):
        o1, o2 = struct.unpack("<HH", data[2+i*4:6+i*4])
        print(f"Processing frame {i} cell {0}")
        p1, w1, h1, _ = decompress_cell(data, o1, is_mm3)#, mm4_cells[i*2])
        print(f"Processing frame {i} cell {1}")
        p2, w2, h2, _ = decompress_cell(data, o2, is_mm3)#, mm4_cells[i*2+1])
        
        mw, mh = max(w1, w2 if p2 else 0), max(h1, h2 if p2 else 0)
        if mw == 0: continue
        
        img = Image.new("P", (mw, mh), 0)
        img.putpalette(palette)
        if p1: 
            img.putdata(p1)
        if p2:
            ovl = Image.new("P", (w2, h2)); ovl.putdata(p2)
            mask = Image.new("L", (w2, h2), 0); mask.putdata([255 if x != 0 else 0 for x in p2])
            img.paste(ovl, (0,0), mask)
            
        img.save(os.path.join(out_dir, f"frame_{i:02d}.png"))

    if Transcode:
        mm4_out = bytearray()
        mm4_out += data[0:2]
        #for each frame,
        # cell1 offset cell2 offset
        offset1 = 2+num_f*4
        # for i in range(num_f):
        #     mm4_out += offset1
        #     mm4_out += offset1


        with open("transcode.ccx", "wb") as transcode_file:
            transcode_file.write(mm4_out)

    print(f"Done! Extracted {num_f} frames to {out_dir}")

# EXECUTION
# parse_sprite("witch.mon", "out_witch", mode="mm3")
# parse_sprite("d_7818.ccx", "out_xeen", mode="xeen")

# Usage examples:
# parse_sprite("WIP_MM3_REPACK/d_7818.ccx", "out_xeen", mode="xeen")
# parse_sprite("out_witch.mm4", "text_3to4", mode="xeen")

parse_sprite("mm3out/troll.mon", "out_troll", mode="mm3")
parse_sprite("mm3out/witch.mon", "out_witch", mode="mm3")

# parse_sprite("mm3out/town.pic", "out_town", mode="mm3")
# parse_sprite("mm3out/sci.sky", "out_scisky", mode="mm3")
# parse_sprite("mm3out/temple.out", "out_temple", mode="mm3")

parse_sprite("MM3-CC-Files/mm3-cc-files/0xf053.ccx", "out_unknown", mode="mm3")



# Usage
# convert_xeen_sprite("002.ATT", "out_frames")
# convert_xeen_sprite("001.ATT", "sprite_out")

# convert_sprite("mm3out/witch.mon", "monster_sprite")
# convert_sprite("WIP_MM3_REPACK/d_7818.ccx", "monster_sprite")


