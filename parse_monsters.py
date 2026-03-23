import struct
import csv
import os

# The fixed list of 90 monsters (Rows)
MONSTERS = [
    "bat", "bublman", "goblin", "orc", "skel", "head", "wasp", "rat", "shriek", "zombie",
    "candle", "dwarf", "ninja", "mantis", "hamr", "bugeye", "repthed", "spider", "sprite", "beetle",
    "cobra", "scorpia", "flytrap", "jester", "minidrgn", "plasmoid", "hand", "ghoul", "gatekepr", "phantom",
    "pirana", "ranger", "thief", "treeglum", "witch", "robo2", "dthlocus", "archer", "ballface", "barbaran",
    "cleric", "firelzrd", "firemon", "gargoyle", "ghost", "lizard", "sonicnja", "beholder", "cris", "paladin",
    "pegasus", "reaper", "sorc", "lich", "shield", "troll", "demon", "dino", "robo", "blknight",
    "martface", "mummy", "powsorc", "cataplr", "undragon", "cyclop", "devil", "grndrgn", "wizard", "worm",
    "vampire", "werewolf", "termnatr", "hydra", "roc", "kudo", "medusa", "minotaur", "octobest", "draglord",
    "x1", "x2", "x3", "x4", "x5", "x6", "x7", "x8", "x9", "x10"
]

files = [
    "MonAC.dat", "MonAcid.dat", "MonAttP.dat", "MonCold.dat", "MonDmgN.dat",
    "MonDmgS.dat", "MonDmgT.dat", "MonElec.dat", "MonEner.dat", "MonExp.dat",
    "MonFire.dat", "MonGems.dat", "MonGold.dat", "MonHitB.dat", "MonHP.dat",
    "MonMagi.dat", "MonNumA.dat", "MonPhys.dat", "MonRang.dat", "MonSpd.dat",
    "MonSpec.dat", "MonTrea.dat"
]

def parse_variable_binary(filename):
    """Parses file based on total byte size to determine row width."""

    filename = "mm3out/"+filename

    if not os.path.exists(filename):
        print(f"Skipping: {filename} (not found)")
        return [None] * 90
    
    file_size = os.path.getsize(filename)
    values = []
    
    with open(filename, "rb") as f:
        if file_size == 90:
            # 1 byte per row (Unsigned Byte)
            values = list(f.read(90))
        elif file_size == 180:
            # 2 bytes per row (Little-Endian Unsigned Short)
            for _ in range(90):
                chunk = f.read(2)
                values.append(struct.unpack('<H', chunk)[0])
        elif file_size == 360:
            # 4 bytes per row (Little-Endian Unsigned Integer)
            for _ in range(90):
                chunk = f.read(4)
                values.append(struct.unpack('<I', chunk)[0])
        else:
            print(f"Warning: {filename} has unexpected size ({file_size} bytes). Filling with 0.")
            values = [0] * 90
            
    return values

def main():
    # Dictionary to hold the columns: { "FileName": [values...] }
    data_columns = {}

    for file in files:
        data_columns[file] = parse_variable_binary(file)

    output_file = "monster_data_compiled.csv"
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        
        # Header: "MonsterName" followed by all filenames
        writer.writerow(["MonsterName"] + files)
        
        # Rows: Monster Name + the value from each file for that index
        for i, monster in enumerate(MONSTERS):
            row = [monster]
            for file in files:
                row.append(data_columns[file][i])
            writer.writerow(row)

    print(f"Successfully compiled {len(files)} files into {output_file}")

if __name__ == "__main__":
    main()

