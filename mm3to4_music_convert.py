import struct

def transcode_m_file(mm3_data):
    # MM3 usually starts with a 2-byte count or ID (like 0x10 0x02)
    # followed by one or more 26-byte instrument patches.
    # We'll assume a standard 2-patch header (54 bytes total).
    header_size = 54 
    mm3_patches = mm3_data[2:header_size]
    mm3_payload = mm3_data[header_size:]
    
    mm4_output = bytearray()

    # --- PHASE 1: MM4 INITIALIZATION ---
    # We prepend the "Known Good" initialization sequence you found in the MM4 dump
    # This primes the Xeen driver's registers.
    mm4_output.extend(bytes.fromhex("20711C51030021005417000E711C51030021005417000E"))
    
    # --- PHASE 2: CONVERT MM3 PATCHES TO MM4 COMMANDS ---
    # We turn the static MM3 FM data into "Register Write" commands (Opcode 0xA)
    opl_registers = [0x20, 0x23, 0x40, 0x43, 0x60, 0x63, 0x80, 0x83, 0xE0, 0xE3, 0xC0]
    
    for p in range(2): # Assuming 2 patches
        patch_offset = p * 26
        for i, reg in enumerate(opl_registers):
            val = mm3_patches[patch_offset + i]
            mm4_output.append(0xA0 | p) # Opcode 0xA (Reg Write) | Channel p
            mm4_output.append(reg)
            mm4_output.append(val)

    # --- PHASE 3: COMMAND STREAM TRANSCODING ---
    i = 0
    while i < len(mm3_payload):
        byte = mm3_payload[i]
        cmd = (byte & 0xF0) >> 4
        chan = byte & 0x0F
        
        # Note On: Transpose +2 semitones for Xeen engine
        if cmd == 0x0: 
            mm4_output.append(byte)
            note = mm3_payload[i+1]
            velocity = mm3_payload[i+2]
            mm4_output.append(min(note + 2, 127)) # Shift pitch up
            mm4_output.append(velocity)
            i += 3
        
        # Delay / Wait
        elif cmd == 0x1:
            mm4_output.append(byte)
            mm4_output.append(mm3_payload[i+1])
            i += 2
            
        # Note Off
        elif cmd == 0x2:
            mm4_output.append(byte)
            mm4_output.append(mm3_payload[i+1] + 2) # Shift pitch up
            i += 2
            
        # Program Change / Volume / Panning (Direct Copy)
        elif cmd in [0x3, 0x4, 0x5]:
            mm4_output.append(byte)
            mm4_output.append(mm3_payload[i+1])
            i += 2
            
        else:
            # Safe copy for unknown or single-byte commands
            mm4_output.append(byte)
            i += 1

    # --- PHASE 4: TERMINATION ---
    # Ensure the file ends with a clean stop
    mm4_output.extend([0x10, 0x00]) # Wait 0
    mm4_output.extend([0x20, 0x00]) # All Notes Off/End
    
    return bytes(mm4_output)

# To use:
with open("mm3theme.m", "rb") as f: data = f.read()
mm4_ready = transcode_m_file(data)
with open("music_mm4.m", "wb") as f: f.write(mm4_ready)