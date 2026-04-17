import struct

def merge_mm4_multi_frame(file1_path, file2_path, output_path):
    def get_full_sprite_info(path):
        with open(path, "rb") as f:
            data = f.read()
        
        num_frames = struct.unpack("<H", data[:2])[0]
        # Frame table is: [Count(2)] + [Frame1_Cell1(2), Frame1_Cell2(2), ...]
        table_size = 2 + (num_frames * 4)
        
        # We need the actual offsets to know where the pixel data is
        offsets = struct.unpack("<" + "H" * (num_frames * 2), data[2:table_size])
        pixel_data = data[table_size:]
        
        return num_frames, list(offsets), pixel_data

    # 1. Parse both files
    f1_count, f1_offsets, f1_pixels = get_full_sprite_info(file1_path)
    f2_count, f2_offsets, f2_pixels = get_full_sprite_info(file2_path)

    total_frames = f1_count + f2_count
    new_header_size = 2 + (total_frames * 4)
    
    # 2. Rebuild the Offset Table
    combined_offsets = []

    # Shift Sprite 1 offsets
    # Original offsets were relative to (2 + f1_count * 4)
    # New offsets are relative to (2 + total_frames * 4)
    shift_amount = (total_frames - f1_count) * 4
    
    for off in f1_offsets:
        if off != 0:
            combined_offsets.append(off + shift_amount)
        else:
            combined_offsets.append(0)

    # Calculate starting point for Sprite 2 data
    # It starts after the header + all of Sprite 1's pixels
    s2_base_shift = new_header_size + len(f1_pixels)
    
    # Sprite 2's internal offsets are relative to its own old header
    s2_old_header_size = 2 + (f2_count * 4)
    
    for off in f2_offsets:
        if off != 0:
            # Shift the offset to its new global position
            combined_offsets.append(off - s2_old_header_size + s2_base_shift)
        else:
            combined_offsets.append(0)

    # 3. Write the new file
    with open(output_path, "wb") as f:
        f.write(struct.pack("<H", total_frames))
        for off in combined_offsets:
            f.write(struct.pack("<H", off))
        f.write(f1_pixels)
        f.write(f2_pixels)

    print(f"Merged {f1_count} frames and {f2_count} frames into {output_path}.")

if __name__ == "__main__":
    # merge_mm4_multi_frame("base_monster.ccx", "new_attack_frame.ccx", "final.ccx")
    pass