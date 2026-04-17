import struct
import os

def merge_mm4_sprites(file1_path, file2_path, output_path):
    def get_sprite_data(path):
        with open(path, "rb") as f:
            data = f.read()
        
        # Read number of frames from the first 2 bytes
        num_frames = struct.unpack("<H", data[:2])[0]
        # Frame table size is 2 bytes (count) + (num_frames * 4 bytes for 2 cells)
        header_size = 2 + (num_frames * 4)
        # Extract just the pixel/cell data (skipping the original header)
        pixel_data = data[header_size:]
        
        return num_frames, pixel_data

    # 1. Extract data from both files
    try:
        frames1, pixels1 = get_sprite_data(file1_path)
        frames2, pixels2 = get_sprite_data(file2_path)
    except Exception as e:
        print(f"Error reading files: {e}")
        return

    total_frames = frames1 + frames2
    
    # 2. Build the new Frame Table
    # The first cell of the first sprite starts immediately after the new header
    new_header_size = 2 + (total_frames * 4)
    new_offsets = []

    # Offsets for Sprite 1
    # We assume each frame has 1 active cell and 1 null cell (offset 0)
    # The original offsets in pixels1 are relative to the old header. 
    # We must shift them to be relative to the NEW header.
    current_offset = new_header_size
    
    # Re-calculate offsets for Sprite 1
    # Note: Since we are stripping the old header and keeping the raw cell data,
    # the first cell of Sprite 1 starts at exactly new_header_size.
    # If Sprite 1 had multiple frames, we'd need to parse its internal cell headers 
    # to find subsequent offsets, but for 1-cell sprites, this is straightforward:
    new_offsets.append(current_offset) # Frame 1, Cell 1
    new_offsets.append(0)              # Frame 1, Cell 2 (Null)

    # Offsets for Sprite 2
    # Sprite 2 starts exactly where Sprite 1's pixel data ends
    sprite2_start_offset = current_offset + len(pixels1)
    new_offsets.append(sprite2_start_offset) # Frame 2, Cell 1
    new_offsets.append(0)                    # Frame 2, Cell 2 (Null)

    # 3. Assemble the file
    with open(output_path, "wb") as f:
        # Write Total Frames
        f.write(struct.pack("<H", total_frames))
        
        # Write the Frame Table (Offsets)
        for off in new_offsets:
            f.write(struct.pack("<H", off))
            
        # Write Pixel Data
        f.write(pixels1)
        f.write(pixels2)

    print(f"Successfully merged {file1_path} and {file2_path} into {output_path}")
    print(f"Total Frames: {total_frames}")

if __name__ == "__main__":
    # Example usage:
    # merge_mm4_sprites("witch_f1.ccx", "witch_f2.ccx", "combined.ccx")
    pass