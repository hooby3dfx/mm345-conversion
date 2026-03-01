import struct

def generate_checkerboard_sprite(filename, width=100, height=100):

    colors = [120, 50]
    
    # 1. Frame Table (1 Frame, 1 Cell)
    num_frames = 1
    cell_offset = 6  # 2 (num) + 4 (frame1)
    file_header = struct.pack("<H", num_frames) + struct.pack("<HH", cell_offset, 0)

    # 2. Cell Header
    x_off = 0
    y_off = 0

    x_skip = 10

    cell_header = struct.pack("<HHHH",  x_off, width+x_skip, y_off, height)

    # 3. Image Data
    pixel_data = bytearray()
    
    for y in range(height):
        line_payload = bytearray()
        x = 0
        
        # We process the line in chunks of 32 (Max for MM4 Cmd 0)
        while x < width:
            chunk_w = min(32, width - x)
            # Opcode: Cmd 0 (Raw) | (Length - 1)
            line_payload.append(0x00 | (chunk_w - 1))
            
            for i in range(chunk_w):
                # Checkerboard logic: flip color based on X and Y
                color = colors[((x + i) // 5 + (y // 5)) % 2]
                line_payload.append(color)
            
            x += chunk_w
            
        # Line Header: [Payload Length] [X-Skip]
        pixel_data.append(len(line_payload)+1)
        pixel_data.append(x_skip)
        pixel_data.extend(line_payload)

    # 4. Termination (Len 0, V-Skip 0)
    # pixel_data.extend([0, 0])

    full_data = file_header + cell_header + pixel_data
    
    with open(filename, "wb") as f:
        f.write(full_data)
        
    print(f"Checkerboard sprite '{filename}' created ({len(full_data)} bytes).")

if __name__ == "__main__":
    generate_checkerboard_sprite("check_test.ccx", 50, 50)

