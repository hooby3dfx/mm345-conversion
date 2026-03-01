import struct
import argparse
import os

def inspect_sprite(filename):
    if not os.path.exists(filename):
        print(f"Error: File {filename} not found.")
        return

    with open(filename, "rb") as f:
        data = f.read()

    file_size = len(data)
    num_frames = struct.unpack("<H", data[0:2])[0]
    # The frame table consists of 2 offsets (Cell1, Cell2) per frame
    table_end = 2 + (num_frames * 4)

    print(f"File: {filename}")
    print(f"File Size: {file_size} bytes")
    print(f"Total Frames: {num_frames}")
    print(f"Header/Table Ends At: {table_end} (0x{table_end:X})")
    print("-" * 60)
    print(f"{'Frame':<8} | {'Cell 1 Offs':<12} | {'Cell 2 Offs':<12}")
    print("-" * 60)

    unique_offsets = set()
    frame_map = []

    # 1. Parse the Frame Table
    for i in range(num_frames):
        entry_ptr = 2 + (i * 4)
        off1, off2 = struct.unpack("<HH", data[entry_ptr:entry_ptr+4])
        frame_map.append((off1, off2))
        print(f"{i:<8} | 0x{off1:04X} ({off1:<5}) | 0x{off2:04X} ({off2:<5})")
        if off1 != 0: unique_offsets.add(off1)
        if off2 != 0: unique_offsets.add(off2)

    print("\n" + "="*60)
    print("CELL METADATA (Unique Offsets)")
    print("="*60)
    print(f"{'Offset':<10} | {'X_Off':<6} | {'Width':<6} | {'Y_Off':<6} | {'Height':<6} | {'Rel_Check'}")
    print("-" * 60)

    # 2. Inspect the unique cells
    for off in sorted(list(unique_offsets)):
        # Check both Absolute and Relative (Relative to end of table)
        # Some MM files use offsets relative to the start of data (table_end)
        abs_ptr = off
        rel_ptr = off + table_end
        
        # We'll try to parse the header at the offset provided
        if abs_ptr + 8 <= file_size:
            try:
                x, w, y, h = struct.unpack("<HHHH", data[abs_ptr:abs_ptr+8])
                
                # Heuristic check: are the dimensions sane for a 320x200 screen?
                is_sane = (w < 640 and h < 480)
                sanity = "OK" if is_sane else "???"
                
                print(f"0x{off:04X} ({off:<4}) | {x:<6} | {w:<6} | {y:<6} | {h:<6} | {sanity}")
            except:
                print(f"0x{off:04X} ({off:<4}) | ERROR PARSING")
        else:
            print(f"0x{off:04X} ({off:<4}) | OUT OF BOUNDS")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect MM3/MM4 Sprite Metadata")
    parser.add_argument("file", help="The .MON or .CCX file to inspect")
    args = parser.parse_args()
    inspect_sprite(args.file)