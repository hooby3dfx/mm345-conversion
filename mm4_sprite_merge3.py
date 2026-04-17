import struct
import hashlib

def merge_mm4_optimized(file1_path, file2_path, output_path):
    def get_cells(path):
        with open(path, "rb") as f:
            data = f.read()
        
        num_frames = struct.unpack("<H", data[:2])[0]
        offsets = struct.unpack("<" + "H" * (num_frames * 2), data[2:2 + num_frames * 4])
        
        cells = []
        for i in range(len(offsets)):
            off = offsets[i]
            if off == 0:
                cells.append(None)
                continue
            
            # MM4 Cell: Header(8 bytes) + RLE Data + Termination(2 bytes)
            # We need to find the end of the RLE stream to capture the full cell
            # The simplest way is to read until the next offset or the end of file
            # A more robust way is parsing the RLE, but for merging, we'll use offsets:
            sorted_offs = sorted([o for o in offsets if o > off])
            next_off = sorted_offs[0] if sorted_offs else len(data)
            cells.append(data[off:next_off])
            
        return cells

    # 1. Extract all cells from both files
    all_cells_raw = get_cells(file1_path) + get_cells(file2_path)
    
    unique_cells = {} # Hash -> Offset
    final_cell_data = bytearray()
    final_offsets = []
    
    # 2. Determine Frame Table size
    num_frames = len(all_cells_raw) // 2
    header_size = 2 + (num_frames * 4)
    current_write_pos = header_size

    # 3. Deduplicate and rebuild
    for cell_data in all_cells_raw:
        if cell_data is None:
            final_offsets.append(0)
            continue
            
        # Create a unique fingerpint for the cell
        cell_hash = hashlib.md5(cell_data).hexdigest()
        
        if cell_hash in unique_cells:
            # REUSE: Point to the existing offset
            final_offsets.append(unique_cells[cell_hash])
        else:
            # NEW: Write the data and record the offset
            unique_cells[cell_hash] = current_write_pos
            final_offsets.append(current_write_pos)
            final_cell_data.extend(cell_data)
            current_write_pos += len(cell_data)

    # 4. Write the optimized file
    if current_write_pos > 65535:
        print(f"WARNING: File size ({current_write_pos}) exceeds 16-bit offset limit!")

    with open(output_path, "wb") as f:
        f.write(struct.pack("<H", num_frames))
        for off in final_offsets:
            f.write(struct.pack("<H", off))
        f.write(final_cell_data)

    print(f"Merged into {output_path}. Unique cells: {len(unique_cells)} / {len(all_cells_raw)}")

if __name__ == "__main__":
    # merge_mm4_optimized("monster_walk.ccx", "monster_idle.ccx", "optimized.ccx")
    pass