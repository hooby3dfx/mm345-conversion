import struct
import sys


def transcode_step_by_step(mm3_data):
    mm3_stream = bytearray(mm3_data)
    xeen_stream = bytearray()

    chan_last_note_map = {}
    
    i = 0
    while i < len(mm3_stream):
        cmd = mm3_stream[i]
        cmd_type = cmd & 0xF0
        chan = cmd & 0x0F

        print(f"cmd_type {hex(cmd_type)} chan {hex(chan)}")

        xeen_cmd = bytearray()
        
        # --- COMMAND 0x20: INSTRUMENT DEFINITION ---
        if cmd_type == 0x20:
            # inst_id = cmd & 0x0F

            if i + 14 >= len(mm3_stream):
                print("Error: Truncated MM3 instrument payload at end of stream.")
                break
                
            # Extract the MM3 payload bytes
            mm3_opl = mm3_stream[i+1:i+12]       # 11 bytes (00 to 0A)
            tandy_env = mm3_stream[i+12:i+14]    # 2 bytes (0B to 0C)
            mt32_inst = mm3_stream[i+14]         # 1 byte (0D)
            
            # --- CONSTRUCT THE 26-BYTE XEEN INSTRUMENT PATCH ---
            xeen_patch = bytearray(26)
            
            # Global Metadata Block
            # xeen_patch[0] = 0x01        # Voice Type Flags (0x01 = Single OPL voice active)
            # xeen_patch[1] = 0x00        # Fine Tuning / Detune (0 = Neutral)
            # xeen_patch[2] = 0x00        # Pan (0 = Centered/Default layout)
            # xeen_patch[3] = 0x7F        # Volume Scaling Factor (Full dynamic range)
            
            # Voice 1 Block: Direct copy of the 11 OPL parameters
            # xeen_patch[4:15] = mm3_opl
            
            # Voice 2 Block: Left as 0x00 (Disabled)
            # xeen_patch[15:26] = mm3_opl

            xeen_patch[0:11] = mm3_opl
            xeen_patch[24] = mt32_inst
            
            # --- EMIT TO THE XEEN STREAM ---
            # Xeen uses a clean 0xA0 command flag for instrument changes/definitions
            # along with the target instrument ID
            xeen_cmd.append(cmd) #(0x20 | inst_id)
            xeen_cmd.extend(xeen_patch)
            
            # Advance the pointer past the command byte + 14 payload bytes

            i += 15 # Consumes 1 command + 14 payload bytes
            
        # --- COMMAND 0x90: NOTE ON ---
        elif cmd_type == 0x90:
            # We know from the doc this is exactly 2 bytes total (cmd + nn)
            note_payload = mm3_stream[i+1]
            
            # TODO: Add the NOTE_LUT translation and OPL frequency math here
            # For now, let's keep it structurally sound to avoid corruption
            
            xeen_cmd.append(cmd)
            xeen_cmd.append(note_payload)
            xeen_cmd.append(0x7F)#midi fade in rate?
            chan_last_note_map[chan] = note_payload

            i += 2
            
        # --- ALL OTHER COMMANDS: LOOK UP BYTES TO ADVANCE SAFELY ---
        else:
            payload_size = 0
            if cmd_type == 0x00:      
                payload_size = 2  # 00 ll mm
                subroutine_pos = struct.unpack('<H', mm3_stream[i+1 : i + payload_size+1])[0]
                print(f"subroutine_pos {subroutine_pos}")
                #TODO this address will need to be adjusted ... is this used?
                xeen_cmd.extend(mm3_stream[i : i + payload_size+1])

            elif cmd_type == 0x10:   
                payload_size = 1  # 10 dd
                xeen_cmd.extend(mm3_stream[i : i + payload_size+1])

            elif cmd_type == 0x30: 
                payload_size = 1  # 30 vv
                #midi volume - (in xeen this is part of cmd 0xA)
                xeen_cmd.append((0xA0 | chan))
                xeen_cmd.append(0x00)
                xeen_cmd.append(mm3_stream[i+1])

            elif cmd_type == 0x40: 
                payload_size = 2  # 40 mm ll
                xeen_cmd.extend(mm3_stream[i : i + payload_size+1])

            elif cmd_type == 0x50: 
                payload_size = 0
                #unknown - skip
                print(f"unknown cmd 5")

            elif cmd_type == 0x60: 
                payload_size = 1  # 60 pp
                xeen_cmd.extend(mm3_stream[i : i + payload_size+1])

            elif cmd_type == 0x70: 
                payload_size = 0
                #unknown - skip
                print(f"unknown cmd 7")

            elif cmd_type == 0x80: 
                payload_size = 0  # 8# (Standard version is 1 byte total)
                xeen_cmd.extend(mm3_stream[i : i + payload_size+1])
                xeen_cmd.append(chan_last_note_map[chan])#this is the midi note to stop (...last note?)

            elif cmd_type == 0xA0: 
                payload_size = 1  # A# vv
                xeen_cmd.append(cmd)
                xeen_cmd.append(mm3_stream[i+1])
                xeen_cmd.append(0x05)

            elif cmd_type == 0xB0: 
                payload_size = 1  # B# vv
                #tandy volume - skip

            elif cmd_type == 0xC0: 
                payload_size = 1  # C# ii
                xeen_cmd.extend(mm3_stream[i : i + payload_size+1])

            elif cmd_type == 0xD0: 
                payload_size = 0  # D#
                xeen_cmd.extend(mm3_stream[i : i + payload_size+1])

            elif cmd_type == 0xE0: 
                payload_size = 3  # E# tt mm ll
                xeen_cmd.extend(mm3_stream[i : i + payload_size+1])

            elif cmd_type == 0xF0:      
                payload_size = 0  # FE/FF
                xeen_cmd.extend(mm3_stream[i : i + payload_size+1])
            

            total_len = 1 + payload_size
            
            # Temporary: Preserve completely unchanged for commands we aren't editing yet
            # xeen_stream.extend(mm3_stream[i : i + total_len])

            i += total_len

        xeen_stream.extend(xeen_cmd)
            
    return xeen_stream


def convert_m_file(in_path, out_path):

    with open(in_path, "rb") as infile:
        xeen_stream = transcode_step_by_step(infile.read())

        with open(out_path, "wb") as outfile:
            outfile.write(xeen_stream)
            print(f"wrote {len(xeen_stream)} bytes to {outfile}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python this_file.py <mm3_input.m> <mmx_output.m>")
        sys.exit(1)

    convert_m_file(sys.argv[1], sys.argv[2])

