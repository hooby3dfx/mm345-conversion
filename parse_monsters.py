import struct
import csv
import os

# The fixed list of 90 monsters (Rows)
MONSTER_SPRITES = [
    "bat", "bublman", "goblin", "orc", "skel", "head", "wasp", "rat", "shriek", "zombie",
    "candle", "dwarf", "ninja", "mantis", "hamr", "bugeye", "repthed", "spider", "sprite", "beetle",
    "cobra", "scorpia", "flytrap", "jester", "minidrgn", "plasmoid", "hand", "ghoul", "gatekepr", "phantom",
    "pirana", "ranger", "thief", "treeglum", "witch", "robo2", "dthlocus", "archer", "ballface", "barbaran",
    "cleric", "firelzrd", "firemon", "gargoyle", "ghost", "lizard", "sonicnja", "beholder", "cris", "paladin",
    "pegasus", "reaper", "sorc", "lich", "shield", "troll", "demon", "dino", "robo", "blknight",
    "martface", "mummy", "powsorc", "cataplr", "undragon", "cyclop", "devil", "grndrgn", "wizard", "worm",
    "vampire", "werewolf", "termnatr", "hydra", "roc", "kudo", "medusa", "minotaur", "octobest", "draglord",
    "x1", "x2", "x3", "x4", "x5", "x6", "x7", "x8", "x9", "x10",
]

MONSTER_NAMES = [
    'Vampire Bat','Bubble Man','Goblin','Orc Warrior','Skeleton','Screamer','Oh No Bug','Moose Rat',
    'Wild Fungus','Zombie','Candle Creep','Mad Dwarf','Ninja','Magic Mantis','Ogre','Bugaboo',
    'Phase Head','Giant Spider','Sprite','Dino Beetle','Cobra Fiend','Scorpia','Cryo Spore','Cursed Fool',
    'Mini Dragon','Plasmoid','Carnage Hand','Ghoul','Castle Guard','Phantom','Pirana','Evil Ranger',
    'Shadow Rogue','Tree Golem','Wicked Witch','Iron Wizard','Death Locust','Archer','Mystic Cloud','Barbarian',
    'Cleric of Moo','Fire Lizard','Fire Stalker','Gargoyle','Ghost','Draconi','Sonic Ninja','Evil Eye',
    'Guardian','Paladin','Dark Pegasus','Reaper','Sorcerer','Lich','Spirit Shield','Troll',
    'Major Demon','Dinosaur','ED-409','Black Knight','Death Agent','Mummy','Priest of Moo','Toxic Worm',
    'Dragon Worm','Cyclops','Major Devil','Green Dragon','Jouster','Death Snake','Vampire','Werewolf',
    'Terminator','Great Hydra','Vulture Roc','Kudo Crab','Medusa','Minotaur','Octobeast','Dragon Lord',
    'Rat Overlord','Mummy King','Cyclops King','Minotaur King','Vampire King','Moo Master','Top Jouster','Eye Master','Cult Leader'
]

files = [
    "MonAC.dat", "MonAcid.dat", "MonAttP.dat", "MonCold.dat", "MonDmgN.dat",
    "MonDmgS.dat", "MonDmgT.dat", "MonElec.dat", "MonEner.dat", "MonExp.dat",
    "MonFire.dat", "MonGems.dat", "MonGold.dat", "MonHitB.dat", "MonHP.dat",
    "MonMagi.dat", "MonNumA.dat", "MonPhys.dat", "MonRang.dat", "MonSpd.dat",
    "MonSpec.dat", "MonTrea.dat"
]

files = [
    #name 16b

    "MonExp.dat",#4b

    "MonHP.dat",#2b
    "MonAC.dat", #1b
    "MonSpd.dat",#1b

    "MonNumA.dat", #1b
    #hates 
    "dummy-hates",#1b
    "MonDmgN.dat",#strikes? 
    "dummy-strikes2",#1b fill

    "MonDmgS.dat",#dmg per strike?
    "MonDmgT.dat",#dmg/att type?
    "MonSpec.dat",#special
    "MonAttP.dat",#hit chance? attack probability. crash if this is 0 for phase head???

    "MonRang.dat", 
    #mon type
    "dummy-montype",
    "MonFire.dat",
    "MonElec.dat", 

    "MonCold.dat", 
    "MonAcid.dat", 
    "MonEner.dat",
    "MonMagi.dat", 

    "MonPhys.dat", 
    #field29?
    "dummy-f29",#"MonHitB.dat", #not sure what this is for...
    "MonGold.dat", #4b -> should be 2b

    "MonGems.dat", #2b -> should be 1b
    "MonTrea.dat",#treasure/item?
    #flying
    "dummy-fly",
    #img num
    "dummy-img#",

    #loop
    "dummy-loop",
    #anim
    "dummy-anim",

    #fx
    #voc sfx
    # "dummy-voc", #last 10 bytes added in loop
    # "dummy-voc",
    # "dummy-voc",
    # "dummy-voc",
    # "dummy-voc",
    # "dummy-voc",
    # "dummy-voc",
    # "dummy-voc",
    # "dummy-voc",
]

def remap_special(mm3val):
    #xeen special values:
    # SA_NONE = 0, SA_MAGIC = 1, SA_FIRE = 2, SA_ELEC = 3, SA_COLD = 4,
    # SA_POISON = 5, SA_ENERGY = 6, SA_DISEASE = 7, SA_INSANE = 8,
    # SA_SLEEP = 9, SA_CURSEITEM = 10, SA_INLOVE = 11, SA_DRAINSP = 12,
    # SA_CURSE = 13, SA_PARALYZE = 14, SA_UNCONSCIOUS = 15,
    # SA_CONFUSE = 16, SA_BREAKWEAPON = 17, SA_WEAKEN = 18,
    # SA_ERADICATE = 19, SA_AGING = 20, SA_DEATH = 21, SA_STONE = 22

    #xeen damage type values:
    # DT_PHYSICAL = 0, DT_MAGICAL = 1, DT_FIRE = 2, DT_ELECTRICAL = 3,
    # DT_COLD = 4, DT_POISON = 5, DT_ENERGY = 6, DT_SLEEP = 7,
    # DT_FINGEROFDEATH = 8, DT_HOLYWORD = 9, DT_MASS_DISTORTION = 10,
    # DT_UNDEAD = 11, DT_BEASTMASTER = 12, DT_DRAGONSLEEP = 13,
    # DT_GOLEMSTOPPER = 14, DT_HYPNOTIZE = 15, DT_INSECT_SPRAY = 16,
    # DT_POISON_VOLLEY = 17, DT_MAGIC_ARROW = 18

    return 0



def parse_variable_binary(filename):
    """Parses file based on total byte size to determine row width."""

    # filename = "mm3out/"+filename

    if not os.path.exists(filename):
        print(f"Skipping: {filename} (not found)")
        return [None] * 90, [b'\x00'] * 90
    
    file_size = os.path.getsize(filename)
    values_dec = []
    values_raw = []
    
    with open(filename, "rb") as f:
        if file_size == 90:
            # 1 byte per row (Unsigned Byte)
            data = f.read(90)
            values_dec = list(data)
            for i in range(90):
                if filename.endswith("MonAttP.dat") and i==16:
                    #crash if this is 0 for phase head???
                    values_raw.append(bytes([0x01]))
                else:
                    values_raw.append(bytes([data[i]]))
        elif file_size == 180:
            # 2 bytes per row (Little-Endian Unsigned Short)
            for _ in range(90):
                chunk = f.read(2)
                values_dec.append(struct.unpack('<H', chunk)[0])
                if filename.endswith("MonGems.dat"):
                    values_raw.append(chunk[0:1])
                else:
                    values_raw.append(chunk)
        elif file_size == 360:
            # 4 bytes per row (Little-Endian Unsigned Integer)
            for _ in range(90):
                chunk = f.read(4)
                values_dec.append(struct.unpack('<I', chunk)[0])
                if filename.endswith("MonGold.dat"):
                    values_raw.append(chunk[0:2])
                else:
                    values_raw.append(chunk)
        else:
            print(f"Warning: {filename} has unexpected size ({file_size} bytes).")
            # values = [0] * 90
            
    return values_dec, values_raw

#xeen format:
'''
60 bytes per row

16 bytes    name (i0)
4 bytes     exp (i16)
2 bytes     HP (i20)
1 byte      AC (i22)
1 byte      spd (i23)
1 byte      num att (i24)
1 byte      hates (i25)
2 bytes     strikes (i26)
1 byte      dmg per strike (i28)
1 byte      d type (i29)
1 byte      special att (i30)
1 byte      hit chance (i31)
1 byte      range att (i32)
1 byte      mon type (i33)
1            fire res (i34)
1            elec res (i35)
1            cold res (i36)
1            pois res (i37)
1            energ res (i38)
1            mag res (i39)
1            phys res (i40)
1            unknown f29 (i41)
2            gold (i42)
1            gems (i44)
1            item (i45)
1            flying (i46)
1            img# (i47)
1            loop (i48)
1            anim (i49)
1            fx/id (100-189) (i50)
8 bytes     sfx fname (i51)
1 byte      0x00 term (i59)

'''



def parse_monsters(indir, outfile):
    # Dictionary to hold the columns: { "FileName": [values...] }
    data_columns = {}

    for file in files:
        data_columns[file] = parse_variable_binary(indir+"/"+file)

    output_csv_file = "mm3_monster_data_compiled.csv"
    # output_xeen_mon_file = "mm3mondata.mon"
    output_mm4_struct = bytearray()

    with open(output_csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        
        # Header: "MonsterName" followed by all filenames
        writer.writerow(["MonsterName"] + files)
        
        # Rows: Monster Name + the value from each file for that index
        for i, monster in enumerate(MONSTER_NAMES):
            print(f"processing {monster}")
            row = [monster]
            row_raw = bytearray()

            monster_name_bytes = bytearray([0x00]) * 16
            monster_name_enc = monster.encode('utf-8')
            end_idx = 0 + len(monster_name_enc)
            monster_name_bytes[0:end_idx] = monster_name_enc
            row_raw.extend(monster_name_bytes)

            for file in files:
                row.append(data_columns[file][0][i])
                mon_raw_data = bytearray(data_columns[file][1][i])
                if file=="dummy-img#":
                    print(f"placing img id {i}")
                    row_raw.append(i)
                else:
                    row_raw.extend(mon_raw_data)

                print(f"data for {file} len {len(mon_raw_data)}")

            #dSlime
            row_raw.extend(bytes.fromhex("6453 6C696D65 00000000"))

            writer.writerow(row)
            print(f"{monster} | data length: {len(row_raw)}")
            output_mm4_struct.extend(row_raw)

    with open(outfile, "wb") as f:
        f.write(output_mm4_struct)

    print(f"Successfully compiled {len(files)} files into {output_csv_file}")

if __name__ == "__main__":
    parse_monsters("mm3out", "mm3mondata.mon")

