import struct
import os
from collections import defaultdict

# Dictionary of Opcode -> (Name, Description of Arguments)

OPCODE_MAP = {
    0x00: ("NOP", "No operation"),
    0x01: ("Display", "Text ID (1b)"),
    0x02: ("DoorTextSml", "Text ID (1b)"),
    0x03: ("DoorTextLrg", "Text ID (1b)"),
    0x04: ("SignText", "Text ID (1b)"),
    0x05: ("NPC", "Name ID, Conv ID, FaceID, Confirm, [NextLine]"),
    0x06: ("PlayFX", "Effect ID"),
    0x07: ("TeleportExit", "MapID, X, Y"),
    0x08: ("If_Type1", "CompType, Value(2b), DestLine"),
    0x09: ("If_Type2", "CompType, Value(2b), DestLine"),
    0x0A: ("If_Type3", "CompType, Value(2b), DestLine"),
    0x0B: ("MoveObj", "ObjNum, X, Y"),
    0x0C: ("TakeOrGive", "TakeType, Obj1(2b), GiveType, Obj2(2b)"),
    0x0D: ("NoAction", "-"),
    0x0E: ("Remove", "-"),
    0x0F: ("SetChar", "CharIndex"),
    0x10: ("Spawn", "MonsterID, X, Y, Unk"),
    0x11: ("DoTownEvent", "TownEventID"),
    0x12: ("Exit", "-"),
    0x13: ("AlterMap", "X, Y, Wall, Val"),
    0x14: ("GiveExtended", "Unknown"),
    0x15: ("ConfirmWord", "Word1 ID, Dest, Word2 ID, Prompt ID"),
    0x16: ("Damage", "Amount (uint16), Type"),
    0x17: ("JumpRnd", "Max, Comp, DestLine"),
    0x18: ("AlterEvent", "LineNum, NewOpcode"),
    0x19: ("CallEvent", "X, Y, Facing"),
    0x1A: ("Return", "-"),
    0x1B: ("SetVar", "VarID, Value(2b)"),
    0x1C: ("TakeOrGive", "GiveType, Comp(2b), GiveType2, Obj2(2b)"),
    0x1D: ("TakeOrGive", "TakeType, Obj1(2b), GiveType, Obj2(2b)"),
    0x1E: ("CutsceneClouds", "-"),
    0x1F: ("TeleportCont", "MapID, X, Y"),
    0x20: ("WhoWill", "WhatIdx, Desc ID"),
    0x21: ("RndDamage", "Type, Max"),
    0x22: ("MoveWallObj", "WallObjNum, X, Y"),
    0x23: ("AlterCellFlag", "X, Y, NewVal"),
    0x24: ("AlterHed", "NewVal (uint16)"),
    0x25: ("DisplayStat", "Text ID"),
    0x26: ("TakeOrGive", "GiveType, Obj1(2b), GiveType2, Obj2(2b)"),
    0x27: ("SeaTextSml", "Text ID"),
    0x28: ("PlayEventVoc", "VocIndex"),
    0x29: ("DisplayBottom", "Desc ID"),
    0x2A: ("IfMapFlag", "MonsterID, DestLine"),
    0x2B: ("SelRndChar", "-"),
    0x2C: ("GiveEnchanted", "Type, Base, Extra, Unk"),
    0x2D: ("ItemType", "ItemType"),
    0x2E: ("MakeNothing", "-"),
    0x2F: ("NoAction", "-"),
    0x30: ("ChooseNum", "OptCount, Array[LineNums]"),
    0x31: ("DisplayBtm2", "Line1 ID, Line2 ID"),
    0x32: ("DisplayLarge", "Text ID"),
    0x33: ("ExchObj", "Obj1, Obj2"),
    0x34: ("FallToMap", "MapID, X, Y, Damage"),
    0x35: ("DisplayMain", "Text ID"),
    0x36: ("Goto", "Surface, DestLine"),
    0x37: ("ConfirmWord2", "W1 ID, Dest1, W2 ID, Dest2"),
    0x38: ("GotoRandom", "Count, Array[LineNums]"),
    0x39: ("CutsceneDark", "-"),
    0x3A: ("CutsceneWorld", "-"),
    0x3B: ("FlipWorld", "SideFlag"),
    0x3C: ("PlayCD", "Track, Start(2b), End(2b)"),
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

    def to_data(self):
        out = bytearray()
        out.append(self.length)
        out.append(self.x)
        out.append(self.y)
        out.append(self.facing)
        out.append(self.line_number)
        out.append(self.opcode)
        out.extend(self.raw_args)
        return out


def group_by_location(lines):
    map_events = defaultdict(list)
    for line in lines:
        # Group by X and Y coordinate
        map_events[(line.x, line.y)].append(line)
    
    # Sort lines within each location by line_number
    for loc in map_events:
        map_events[loc].sort(key=lambda l: l.line_number)
        
    return map_events

def parse_evt_lines(file_path):
    print(f"parsing {file_path}")
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

            if length<5:
                print(f"abnormally short line: {line_payload}")
                continue
                
            # Combine length byte and payload for processing
            full_line_data = length_byte + line_payload
            line_obj = XeenEventLine(full_line_data)
            events.append(line_obj)
            
    return events

def convert_3to4(event_line):

    modified = False

    if event_line.opcode==0x01:
        #mm3 display 0x01 -> mm4 DisplayBottom 0x29
        event_line.opcode = 0x29
        modified = True
    # elif event_line.opcode==0x03:
    #     #mm3 DoorTextLrg -> mm4 DisplayMain
    #     event_line.opcode = 0x35
    #     modified = True
    elif event_line.opcode==0x1B:
        if event_line.raw_args[0]==0x54 and len(event_line.raw_args)==2:
            #temp workaround for setvar script interruption
            event_line.raw_args = [0x00, 0x00]
            modified = True
    elif event_line.opcode==0x11:
        #MM3 ID type shop (0:bank/1:blacksmith/2:magicguild/3:inn/4:pub/5:temple/6:training)
        #mm4:
        # Byte Value
        # 0x00 Bank
        # 0x01 Blacksmith
        # 0x02 Guild
        # 0x03 Tavern
        # 0x04 Temple
        # 0x05 Trainer
        # 0x06 Arena Event
        # 0x07 Unknown
        # 0x08 Reaper Event (Enter Tower)
        # 0x09 Golem Event (Enter Dungeon)
        # 0x0A Dwarf Event (Enter Dwarf's Mines in Clouds)
        # 0x0B Sphinx Event
        # 0x0C Pyramid
        # 0x0D Dwarf Event (Enter Town in Darkside)
        #mm3to4:
        #0->0
        #1->1
        #2->2
        #3->3
        #4->3
        #5->4
        #6->5
        if event_line.raw_args[0] > 3:
            event_line.raw_args = [event_line.raw_args[0]-1]
            modified = True

    
    # Event facing: 0(N),1(E),2(S),3(W),4(any) -> E&S are swapped!
    if event_line.facing == 1:
        event_line.facing = 2
        modified = True
    elif event_line.facing == 2:
        event_line.facing = 1
        modified = True

    if modified:
        print("** LINE CONVERTED TO: **")
        print(event_line)

def parse_evt_file(file_path, out_path="mm3to4evt.bin"):
    lines = parse_evt_lines(file_path)

    mm3to4 = bytearray()
    for line in lines:
        print(line)
        convert_3to4(line)
        mm3to4.extend(line.to_data())

    # grouped = group_by_location(lines)
    # for loc, script in grouped.items():
    #     print(f"\nEvent at {loc}:")
    #     for line in script:
    #         print(f"  {line}")

    with open(out_path, "wb") as f:
        f.write(mm3to4)


# Example Usage:
# parse_evt_file('WIP_MM3_REPACK/MAZE0028.EVT')
# parse_evt_file("mm3_default.sav-files/MAZE01.EVT")
# parse_evt_file("mm3_default.sav-files/MAZE41.EVT")
# parse_evt_file("mm3_default.sav-files/MAZE03.EVT")

# parse_evt_file('WIP_MM3_REPACK/MAZE0001.EVT')

# parse_evt_file("ext_cld_world/MAZE0028.EVT")

parse_evt_file('mm3out/MAZE01.EVT')
parse_evt_file('mm3out/MAZE41.EVT')
parse_evt_file('mm3out/MAZE16.EVT')
