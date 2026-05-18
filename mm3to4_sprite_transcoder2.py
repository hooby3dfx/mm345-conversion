import struct
import argparse
import os

class MMTranscoder:
    def __init__(self, verbose=False):
        self.verbose = verbose

    def log(self, message):
        if self.verbose: print(message)

    def transcode_cell(self, data, offset, cell_id, out_width=0, out_height_off=0, y_start=0, y_end=0):
        if offset <= 0 or offset >= len(data): return b""
        
        self.log(f"\n--- Transcoding {cell_id} ---")
        header = data[offset:offset+8]
        x_off, width, y_off, height = struct.unpack("<HHHH", header)
        
        dp = offset + 8
        y_ptr = y_off
        total_h = y_off + height
        total_w = x_off + width
        print(f"cell total size: {total_w}x{total_h}")

        # mm4_width_diff = 100 - total_w
        # x_off += mm4_width_diff

        # x_off = 0

        if out_height_off:
            mm4_height_diff = out_height_off
            y_off += mm4_height_diff

        # y_off = 0
        # height = 100

        x_skip = 0
        if out_width:
            width = out_width #MM4 sprites seem to all have a width of 250
            x_skip = 50 #MM4 sprites seem to all be inset 50 px

        if y_end:
            height = y_end
    
        total_w = x_off + width
        total_h = y_off + height
        print(f"adjusted input cell total size: {total_w}x{total_h}")

        if y_start:
            # y_ptr = y_start
            height = height - y_start

        print(f"adjusted output cell total size: {x_off + width}x{y_off + height}")

        header = struct.pack("<HHHH", x_off, width, y_off, height)
        # struct.pack_into("<H", header, 0, x_off)
        # struct.pack_into("<H", header, 2, width)

        new_cell = bytearray(header)

        
        while y_ptr < total_h and dp < len(data):
            self.log(f"line: {y_ptr}")
            new_line = bytearray()
            mm3_len = struct.unpack("<H", data[dp:dp+2])[0]
            dp += 2
            line_end_src = dp + mm3_len

            if mm3_len:
                mm3_off = struct.unpack("<H", data[dp:dp+2])[0]
                dp += 2
            else:
                mm3_off = data[dp]
                dp += 2

            self.log(f"mm3_len {mm3_len} mm3_off {mm3_off}")
            if y_start > y_ptr:
                self.log(f"skipping input line {y_ptr} because starting at {y_start}")
                dp = line_end_src
                y_ptr += 1
                continue

            # MM3 Stop/V-Skip Logic
            if mm3_len == 0:
                if mm3_off == 0: # End of Cell
                    new_cell.extend([0, total_h-y_ptr]) # MM4 Stop: Len 0, V-Skip 0
                    # print(f"vstop at {y_ptr} of {height}/{total_h} in {cell_id}")
                    # wait = input("MM3 VEND - Press Enter to continue.")
                    break
                self.log(f"vskip {mm3_off}")
                new_cell.extend([0, mm3_off]) # MM4 V-Skip
                y_ptr += mm3_off
                continue
                
            # print(f"line_end_src {line_end_src}")
            x_pos = mm3_off + x_off
            if x_pos > total_w:
                print(f"LINE ERROR (x_pos {x_pos}) - writing line skip(s)")
                # new_cell.extend([0, 1])
                # y_ptr += 1
                # dp = line_end_src
                new_cell.extend([0, total_h-y_ptr])
                break
            
            # --- START MM4 LINE ---
            len_byte_pos = len(new_cell)

            new_cell.append(0) # Placeholder for MM4 Length
            new_cell.append(min(mm3_off+x_skip, 255)) # X-Skip
            
            payload_start = len(new_cell)
            
            stop_cell = False
            TMP_STORED_LEN = 0

            while dp < line_end_src and dp < len(data):
                opcode = data[dp]
                dp += 1
                cmd = (opcode & 0xE0) >> 5
                val = opcode & 0x1F
                
                self.log("Processing cmd opcode: "+str(cmd)+" ("+str(opcode)+")")

                new_cmd = bytearray()

                if cmd == 0: # Raw
                    new_cmd.append(opcode)#0x00 | (val)) #map to CMD0
                    count = (val + 1) #if cmd == 0 else (val + 33)
                    new_cmd.extend(data[dp:dp+count])
                    # for _ in range(count):
                    #     new_cell.append(100)
                    dp += count

                elif cmd == 1: # Raw
                    # wait = input("MM3 CMD1 - Press Enter to continue.")
                    # new_cell.append(0x00 | (val)) #map to CMD0
                    # count = (opcode + 1) #if cmd == 0 else (val + 33)
                    # new_cell.extend(data[dp:dp+count]); dp += count

                    # count = (opcode + 1)
                    # for _ in range(count):
                    #     self.log(f"converting cmd 1 to 0: (dp {dp} count {count} datalen {len(data)})")
                    #     if dp < len(data):
                    #         new_cell.append(0x00)
                    #         new_cell.append(data[dp])
                    #         # new_cell.append(110)
                    #         dp += 1
                    #     else:
                    #         print("ERROR - out of bounds")

                    #map cmd 1 to cmd 1
                    count = (val + 33)
                    self.log(f"converting cmd 1 to 1: (dp {dp} val {val} count {count})")
                    new_cmd.append(0x20 | val)
                    new_cmd.extend(data[dp:dp+count])
                    dp += count
                
                elif cmd == 2: # MM3 Stop
                    # wait = input("MM3 Stop - Press Enter to continue.")
                    # stop_cell = True
                    # self.log(f"skipping cmd 2 val {val}")
                    # break

                    TMP_STORED_LEN = 2

                    #map cmd 2 to cmd 0
                    count = (val + 1)
                    self.log(f"converting cmd 2 to 0: (dp {dp} val {val} count {count})")
                    new_cmd.append(0x00 | val)
                    new_cmd.extend(data[dp:dp+count])
                    if val:
                        dp += count

                
                elif cmd == 3: # Stream CMD3
                    # new_cell.append(opcode)
                    # new_cell.extend(data[dp:dp+2]); dp += 2

                    # continue

                    # count = (opcode + 1)
                    # for _ in range(count):
                    #     self.log(f"converting cmd 3 to 0: (dp {dp} count {count} datalen {len(data)})")
                    #     if dp < len(data):
                    #         new_cell.append(0x00)
                    #         new_cell.append(data[dp])
                    #         # new_cell.append(110)
                    #         dp += 1
                    #     else:
                    #         print("ERROR - out of bounds")

                    #map cmd 3 to cmd 1
                    count = opcode+1
                    extraval = count - 97
                    # print(f"val {val} extraval {extraval}")
                    assert extraval==val
                    self.log(f"converting cmd 3 to 1: (dp {dp} val {val} count {count})")
                    new_cmd.append(0x20 | 31)
                    new_cmd.extend(data[dp:dp+64])
                    dp += 64
                    new_cmd.append(0x20 | extraval)
                    new_cmd.extend(data[dp:dp+extraval+33])
                    dp += (extraval+33)

                
                elif cmd == 4: # MM3 Skip -> MM4 Skip
                    new_cmd.append(0xA0 | val) #map to CMD5

                    # new_cell.append(0x00 | val) #map to CMD2
                    # for _ in range(val+1):
                    #     new_cell.append(120)

                elif cmd == 5: # MM3 Long Skip
                    new_cmd.append(0xA0 | 31); #map to CMD5
                    new_cmd.append(0xA0 | (val))

                    # new_cell.append(0x40 | 27) #map to CMD2
                    # new_cell.append(130)
                    # new_cell.append(0x40 | (val))
                    # new_cell.append(140)
                
                elif cmd == 6: # MM3 RLE -> MM4 RLE
                    new_cmd.append(0x40 | val) #map to CMD2
                    new_cmd.append(data[dp])
                    # new_cell.append(150)
                    dp += 1

                elif cmd == 7: # -Pattern CMD7-
                    # new_cell.append(opcode); 
                    # new_cell.append(data[dp]); dp += 1

                    if TMP_STORED_LEN:
                        #map to CMD2
                        # new_cmd.append(0x40 | 0) #map to CMD2
                        # new_cmd.append(data[dp])
                        # dp += 1

                        #map to CMD0!
                        new_cmd.append(0x00 | 0)
                        new_cmd.append(data[dp])
                        new_cmd.append(0x00 | 0)
                        new_cmd.append(data[dp])
                        dp += 1

                    else:
                        #map to CMD2
                        #(length+35)
                        new_cmd.append(0x40 | 29) #map to CMD2
                        new_cmd.append(data[dp])
                        new_cmd.append(0x40 | val) #map to CMD2
                        new_cmd.append(data[dp])
                        # new_cell.append(0x40 | 2) #map to CMD2
                        # new_cell.append(data[dp])
                        dp += 1


                    # color = data[dp]
                    # dp += 1
                    # lenth = val+35
                    # self.log(f"converting cmd 7 to 0: (color {color} count {lenth})")
                    # for _ in range(lenth):
                    #     new_cell.append(0x00)
                    #     new_cell.append(color)
                        


                self.log(f"command processed; dp: {dp}")

                if dp<=line_end_src:

                    if len(new_cmd)+len(new_line)<256:
                        new_line.extend(new_cmd)
                    else:
                        print(f"WARNING: THIS CMD WOULD EXCEED MAX LINE LEN! line#: {y_ptr} dp:{dp} line_end_src:{line_end_src}")

                else:
                    print(f"WARNING: THIS COMMAND EXCEEDED SRC LINE LEN! line#: {y_ptr} dp:{dp} line_end_src:{line_end_src}")

                
                # wait = input("Press Enter to continue.")

            new_cell.extend(new_line)

            # Finalize MM4 Length (MUST be payload bytes only)
            payload_size = len(new_cell) - payload_start + 1
            # assert payload_size < 256
            if payload_size > 255:
                #TODO prevent this situation
                print(f"WARNING: LINE PAYLOAD TOO LARGE! line# {y_ptr} ({payload_size})")
                # self.log(f"WARNING: LINE PAYLOAD TOO LARGE! ({payload_size})")
                over_size = payload_size - 255
                self.log(f"REDUCING SIZE BY {over_size}")
                del new_cell[-over_size:]
                payload_size = len(new_cell) - payload_start + 1
                self.log(f"NEW SIZE: {payload_size}")

            new_cell[len_byte_pos] = payload_size

            self.log(f"updated line: mm4_len {payload_size} mm4_off {mm3_off}")

            dp = line_end_src
            y_ptr += 1
            if stop_cell:
                #add skip to end of cell height
                new_cell.extend([0, total_h-y_ptr])
                break
            
        # Verify the cell structure before returning
        if not self.verify_mm4_struct(new_cell, cell_id):
            self.log(f"!!! Structural Sanity Check FAILED for {cell_id}")
            
        return bytes(new_cell)

    def verify_mm4_struct(self, cell_bytes, cell_id):
        """Simulates an MM4 parser to check for pointer desync."""
        try:
            _, _, _, height = struct.unpack("<HHHH", cell_bytes[:8])
            ptr = 8
            y_count = 0
            while ptr < len(cell_bytes):
                line_len = cell_bytes[ptr]
                if line_len == 0: # Vertical Skip / Stop
                    v_skip = cell_bytes[ptr+1]
                    if v_skip == 0: return True # Clean Stop
                    ptr += 2
                    y_count += v_skip
                    continue
                # Standard line jump
                ptr += (2 + line_len)
                y_count += 1
            return True
        except Exception as e:
            self.log(f"Sanity Check Error: {e}")
            return False

def convert_sprite_3to4(filepath, outpath, verbose=False, frame_number=-1, out_width=0, out_height_off=0, y_start=0, y_end=0):

    print(f"convert_sprite_3to4 {filepath} to {outpath}")

    with open(filepath, "rb") as f:
        data = f.read()

    new_file = bytearray()

    if frame_number >= 0:
        #we want to trascode only one frame from the input into the output
        num_frames = 1
        new_file.append(num_frames)
        new_file.append(0)
        header_start = 2 + (frame_number * 4)
        header_end = 2 + ((frame_number+1) * 4)
        print(f"transcoding only frame #{frame_number}, header_start {header_start} header_end {header_end}")
        new_file.extend(data[header_start:header_end])
    else:
        #transcode all frames from input into output
        num_frames = struct.unpack("<H", data[:2])[0]
        header_end = 2 + (num_frames * 4)
        new_file.extend(data[:header_end])

    '''
    #TEMP HACK TO GET A WORKING SPRITE IN XEEN
    num_frames = 8
    header_end = 2 + (num_frames * 4)
    new_file = bytearray(data[:header_end])
    #TEMP HACK TO GET A WORKING SPRITE IN XEEN
    new_file = bytearray()
    new_file.append(num_frames)
    new_file.append(0)
    new_file.extend(data[2:header_end])
    '''

    transcoder = MMTranscoder(verbose=verbose)
    offset_map = {}
    write_ptr = len(new_file)

    for index in range(num_frames):
        i_in_frame = index
        i_out_frame = index
        if frame_number >= 0 and num_frames == 1:
            #this is ugly but should work
            i_in_frame = frame_number

        off1, off2 = struct.unpack("<HH", data[2+i_in_frame*4:6+i_in_frame*4])
        print(f"INPUT frame {i_in_frame} off1 {off1} off2 {off2}")
        
        # if args.relative:
        #     if off1 != 0: off1 += header_end
        #     if off2 != 0: off2 += header_end

        new_offs = []
        for j, old_off in enumerate([off1, off2]):
            if old_off == 0 or old_off >= len(data):
                new_offs.append(0); continue
            
            if old_off in offset_map:
                new_offs.append(offset_map[old_off])
            else:
                cid = f"Frame{i_in_frame}_Cell{j+1}"
                res = transcoder.transcode_cell(data, old_off, cid, out_width, out_height_off, y_start, y_end)

                if res:
                    offset_map[old_off] = write_ptr
                    new_offs.append(write_ptr)
                    new_file.extend(res)
                    write_ptr += len(res)
                else:
                    new_offs.append(0)

        print(f"writing to TOC: {new_offs}")
        struct.pack_into("<HH", new_file, 2+i_out_frame*4, *new_offs)


    with open(outpath, "wb") as f:
        f.write(new_file)
    print(f"\nSuccessfully saved to {outpath}")


def main():
    parser = argparse.ArgumentParser(description="MM3 to MM4 Sprite Transcoder")
    parser.add_argument("-i", "--input", required=True, help="Input MM3 .MON file")
    parser.add_argument("-o", "--output", help="Output MM4 .CCX file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose debug output")
    
    args = parser.parse_args()
    if not args.output:
        args.output = os.path.splitext(args.input)[0] + ".ccx"

    if args.input=="runtests":
        runtests()
    else:
        convert_sprite_3to4(args.input, args.output, args.verbose)


def runtests():
    # parse_sprite("mm3out/town.pic", "out_mm3_test01", mode="mm3")
    # parse_sprite("mm3out/town2.pic", "out_mm3_test02", mode="mm3")
    # parse_sprite("mm3out/FOUNTHED.pic", "out_mm3_test03", mode="mm3")
    # parse_sprite("mm3out/DESK.pic", "out_mm3_test04", mode="mm3")
    # parse_sprite("mm3out/troll.mon", "out_mm3_test05", mode="mm3")
    # parse_sprite("mm3out/bublman.mon", "out_mm3_test06", mode="mm3")
    # parse_sprite("mm3out/road.vga", "out_mm3_test07", mode="mm3")
    # parse_sprite("mm3out/dirt.vga", "out_mm3_test08", mode="mm3")
    convert_sprite_3to4("mm3out/FOUNTHED.pic", "test/03_FOUNTHED.pic.ccx", True)
    convert_sprite_3to4("mm3out/troll.mon", "test/05_troll.mon.ccx", True, out_width=250, out_height_off=50)
    

if __name__ == "__main__":
    main()