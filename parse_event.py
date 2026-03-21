import struct
import os
from collections import defaultdict

# Dictionary of Opcode -> (Name, Description of Arguments)
# Based on the Xeen Wiki documentation
OPCODE_MAP = {
    #from xeen
    0x00: ("NOP", "No operation"),
    0x01: ("Display0x01", "Message index (1 byte)"),
    0x02: ("DoorTextSml", "Message index (1 byte)"),
    0x05: ("NPC", "NPC ID (1 byte)"),
    0x09: ("IfMapFlag", "Flag (2 bytes), Line If True (1 byte), Line If False (1 byte)"),
    0x0C: ("TakeOrGive", "Type, Compare, Give Type, Give Val"),
    0x12: ("Exit", "End script execution"),
    0x13: ("AlterMap", "X, Y, Wall, Value"),
    0x16: ("Damage", "Amount (2 bytes), Type (1 byte)"),
    0x1A: ("Return", "Return from CallEvent"),
    0x1C: ("TakeOrGive", "Item/Value exchange"),
    0x20: ("WhoWill", "Who will perform action? (Select Char)"),
    0x25: ("DisplayStat", "Stat index (1 byte)"),
    0x2E: ("MakeNothingHere", "Replaces script with 'Nothing here'"),
    0x33: ("ExchObj", "Obj1 ID (1 byte), Obj2 ID (1 byte)"),
    0x36: ("Goto", "Surface (1 byte), Line (1 byte)"),
    0x38: ("GotoRandom", "Count (1 byte), followed by N Line numbers"),
    0x3B: ("FlipWorld", "Side flag (1 byte): 0=Clouds, 1=Darkside"),
    0x3C: ("PlayCD", "Track (1 byte), Start (2 bytes), End (2 bytes)"),
    #mm3
    0x11: ("Shop", "ID type shop (0:bank/1:blacksmith/2:magicguild/3:inn/4:pub/5:temple/6:training)"),

    #0x03
    #0x07
    #0x08
    #0x0E
    #0x0F
    #0x10
    #0x14
    #0x15
    #0x19
    #0x1B
    #0x1F
}

class XeenEventLine:
    def __init__(self, data):
        self.length = data[0]
        self.x = data[1]
        self.y = data[2]
        self.facing = data[3]
        self.line_number = data[4]
        self.opcode = data[5]
        self.raw_args = data[6:]

    def get_opcode_name(self):
        # Returns the name and description from the map, or 'Unknown'
        return OPCODE_MAP.get(self.opcode, (f"UNKNOWN (0x{self.opcode:02X})", "Unknown arguments"))

    def __repr__(self):
        args_hex = ' '.join(f'{b:02X}' for b in self.raw_args)
        name, desc = self.get_opcode_name()

        return (f"Line {self.line_number:02d} | Pos: ({self.x:2d}, {self.y:2d}) | "
                f"Dir: {self.facing} | Op: 0x{self.opcode:02X} | {name:<15} | Args: [{args_hex:<12}] # {desc}") #Args: [{args_hex}]")

    # def format_line(self):
    #     name, desc = self.get_opcode_name()
    #     args_hex = ' '.join(f'{b:02X}' for b in self.raw_args)
        
    #     return (f"Line {self.line_num:02d}: {name:<15} | Args: [{args_hex:<12}] # {desc}")


def group_by_location(lines):
    map_events = defaultdict(list)
    for line in lines:
        # Group by X and Y coordinate
        map_events[(line.x, line.y)].append(line)
    
    # Sort lines within each location by line_number
    for loc in map_events:
        map_events[loc].sort(key=lambda l: l.line_number)
        
    return map_events

def parse_xeen_evt_lines(file_path):
    events = []
    with open(file_path, 'rb') as f:
        while True:
            # Read the length byte
            length_byte = f.read(1)
            if not length_byte:
                break
            
            length = struct.unpack('B', length_byte)[0]
            # Read the rest of the line based on the length byte
            line_payload = f.read(length)
            
            if len(line_payload) < length:
                break # End of file or corrupt
                
            # Combine length byte and payload for processing
            full_line_data = length_byte + line_payload
            line_obj = XeenEventLine(full_line_data)
            events.append(line_obj)
            
    return events

def parse_xeen_evt_file(file_path):
    lines = parse_xeen_evt_lines(file_path)
    for line in lines:
        print(line)

    # grouped = group_by_location(lines)
    # for loc, script in grouped.items():
    #     print(f"\nEvent at {loc}:")
    #     for line in script:
    #         print(f"  {line}")


# Example Usage:
# parse_xeen_evt_file('WIP_MM3_REPACK/MAZE0028.EVT')
parse_xeen_evt_file("mm3_default.sav-files/MAZE01.EVT")


