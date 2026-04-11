import sys

def rotl16(value, shift):
    """Circularly shift a 16-bit value to the left."""
    # Masking ensures we stay within 16-bit bounds
    shift &= 15
    return ((value << shift) | (value >> (16 - shift))) & 0xFFFF

def hash_file_name_mm4(name):
    length = len(name)
    if length < 1:
        return -1

    # Convert string to list of ordinals for processing
    name_bytes = [ord(c) for c in name]
    h = name_bytes[0]

    for i in range(1, length):
        # Emulate the manual bit rotation from the C code
        # h = ( h & 0x007F ) << 9 | ( h & 0xFF80 ) >> 7;
        part1 = (h & 0x007F) << 9
        part2 = (h & 0xFF80) >> 7
        h = (part1 | part2) & 0xFFFF # Keep it 16-bit
        
        # Add the next character
        h = (h + name_bytes[i]) & 0xFFFF

    return h

def hash_file_name_mm3(name):
    hash_val = 0
    for char in name:
        c_ord = ord(char)
        # Check if character should be converted to uppercase (basic ASCII logic)
        c = c_ord if (c_ord & 0x7F) < 0x60 else c_ord - 0x20
        
        # Rotate left 9 bits
        hash_val = rotl16(hash_val, 9)
        # Add the processed character
        hash_val = (hash_val + c) & 0xFFFF
        
    return hash_val

def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <string>")
        return

    input_str = sys.argv[1]

    mm4 = hash_file_name_mm4(input_str)
    print(f"MM4 Hash: {mm4}")
    print(f"MM4 Hex : {mm4 & 0xFFFF:04x}")

    mm3 = hash_file_name_mm3(input_str)
    print(f"MM3 Hash: {mm3}")
    print(f"MM3 Hex : {mm3 & 0xFFFF:04x}")

if __name__ == "__main__":
    main()