import struct
import argparse
import os

class MMTranscoder:
    def __init__(self, verbose=False):
        self.verbose = verbose

    def log(self, message):
        if self.verbose: print(message)

    def transcode_cell(self, data, offset, cell_id):
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
        x_off = 0
        # mm4_height_diff = 148 - total_h
        mm4_height_diff = 50
        y_off += mm4_height_diff
        # y_off = 0
        #TEMP HACK TO GET A WORKING SPRITE IN XEEN
        width = 250
        # height = 100
        x_skip = 50
        total_w = x_off + width
        total_h = y_off + height
        print(f"adjusted cell total size: {total_w}x{total_h}")

        header = struct.pack("<HHHH", x_off, width, y_off, height)
        # struct.pack_into("<H", header, 0, x_off)
        # struct.pack_into("<H", header, 2, width)

        new_cell = bytearray(header)

        
        while y_ptr < total_h and dp < len(data):
            self.log(f"line: {y_ptr}")
            mm3_len = struct.unpack("<H", data[dp:dp+2])[0]
            dp += 2
            line_end_src = dp + mm3_len

            if mm3_len:
                mm3_off = struct.unpack("<H", data[dp:dp+2])[0]
                dp += 2
            else:
                mm3_off = data[dp]
                dp += 1

            self.log(f"mm3_len {mm3_len} mm3_off {mm3_off}")

            # MM3 Stop/V-Skip Logic
            if mm3_len == 0:
                if mm3_off == 0: # End of Cell
                    new_cell.extend([0, total_h-y_ptr]) # MM4 Stop: Len 0, V-Skip 0
                    # print(f"vstop at {y_ptr} of {height}/{total_h} in {cell_id}")
                    # wait = input("MM3 VEND - Press Enter to continue.")
                    break
                new_cell.extend([0, mm3_off]) # MM4 V-Skip
                y_ptr += mm3_off
                continue
                
            # print(f"line_end_src {line_end_src}")
            
            # --- START MM4 LINE ---
            len_byte_pos = len(new_cell)

            new_cell.append(0) # Placeholder for MM4 Length
            new_cell.append(min(mm3_off+x_skip, 255)) # X-Skip
            
            payload_start = len(new_cell)
            
            stop_cell = False
            while dp < line_end_src and dp < len(data):
                opcode = data[dp]
                dp += 1
                cmd = (opcode & 0xE0) >> 5
                val = opcode & 0x1F
                
                self.log("Processing cmd opcode: "+str(cmd)+" ("+str(opcode)+")")

                if cmd == 0: # Raw
                    new_cell.append(opcode)#0x00 | (val)) #map to CMD0
                    count = (opcode + 1) #if cmd == 0 else (val + 33)
                    new_cell.extend(data[dp:dp+count])
                    # for _ in range(count):
                    #     new_cell.append(100)
                    dp += count

                elif cmd == 1: # Raw
                    # wait = input("MM3 CMD1 - Press Enter to continue.")
                    # new_cell.append(0x00 | (val)) #map to CMD0
                    count = (opcode + 1) #if cmd == 0 else (val + 33)
                    # new_cell.extend(data[dp:dp+count]); dp += count

                    for _ in range(count):
                        new_cell.append(0x00)
                        new_cell.append(data[dp])
                        # new_cell.append(110)
                        dp += 1
                
                elif cmd == 2: # MM3 Stop
                    # wait = input("MM3 Stop - Press Enter to continue.")
                    stop_cell = True
                    break
                
                elif cmd == 4: # MM3 Skip -> MM4 Skip
                    new_cell.append(0xA0 | val) #map to CMD5

                    # new_cell.append(0x00 | val) #map to CMD2
                    # for _ in range(val+1):
                    #     new_cell.append(120)

                elif cmd == 5: # MM3 Long Skip
                    new_cell.append(0xA0 | 31); #map to CMD5
                    new_cell.append(0xA0 | (val))

                    # new_cell.append(0x40 | 27) #map to CMD2
                    # new_cell.append(130)
                    # new_cell.append(0x40 | (val))
                    # new_cell.append(140)
                
                elif cmd == 6: # MM3 RLE -> MM4 RLE
                    new_cell.append(0x40 | val) #map to CMD2
                    new_cell.append(data[dp])
                    # new_cell.append(150)
                    dp += 1

                #no conversion
                elif cmd == 3: # Stream CMD3
                    new_cell.append(opcode)
                    new_cell.extend(data[dp:dp+2]); dp += 2
                elif cmd == 7: # Pattern CMD7
                    new_cell.append(opcode); new_cell.append(data[dp]); dp += 1

                self.log(f"command processed; dp: {dp}")

                # wait = input("Press Enter to continue.")

            # Finalize MM4 Length (MUST be payload bytes only)
            payload_size = len(new_cell) - payload_start + 1
            new_cell[len_byte_pos] = min(payload_size, 255)

            self.log(f"mm4_len {payload_size} mm4_off {mm3_off}")

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




def main():
    parser = argparse.ArgumentParser(description="MM3 to MM4 Sprite Transcoder")
    parser.add_argument("-i", "--input", required=True, help="Input MM3 .MON file")
    parser.add_argument("-o", "--output", help="Output MM4 .CCX file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose debug output")
    parser.add_argument("--relative", action="store_true", help="Toggle relative offsets")
    
    args = parser.parse_args()
    if not args.output:
        args.output = os.path.splitext(args.input)[0] + ".ccx"

    with open(args.input, "rb") as f:
        data = f.read()

    num_frames = struct.unpack("<H", data[:2])[0]
    #TEMP HACK TO GET A WORKING SPRITE IN XEEN
    num_frames = 8
    header_end = 2 + (num_frames * 4)
    new_file = bytearray(data[:header_end])
    #TEMP HACK TO GET A WORKING SPRITE IN XEEN
    new_file = bytearray()
    new_file.append(num_frames)
    new_file.append(0)
    new_file.extend(data[2:header_end])
    
    transcoder = MMTranscoder(verbose=args.verbose)
    offset_map = {}
    write_ptr = len(new_file)

    for i in range(num_frames):
        off1, off2 = struct.unpack("<HH", data[2+i*4:6+i*4])
        print(f"INPUT frame {i} off1 {off1} off2 {off2}")
        
        if args.relative:
            if off1 != 0: off1 += header_end
            if off2 != 0: off2 += header_end

        new_offs = []
        for j, old_off in enumerate([off1, off2]):
            if old_off == 0 or old_off >= len(data):
                new_offs.append(0); continue
            
            if old_off in offset_map:
                new_offs.append(offset_map[old_off])
            else:
                cid = f"Frame{i}_Cell{j+1}"
                res = transcoder.transcode_cell(data, old_off, cid)
                if res:
                    offset_map[old_off] = write_ptr
                    new_offs.append(write_ptr)
                    new_file.extend(res)
                    write_ptr += len(res)
                else:
                    new_offs.append(0)

        print(f"writing to TOC: {new_offs}")
        struct.pack_into("<HH", new_file, 2+i*4, *new_offs)

    with open(args.output, "wb") as f:
        f.write(new_file)
    print(f"\nSuccessfully saved to {args.output}")

if __name__ == "__main__":
    main()