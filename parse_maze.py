'''
MM4: 892

512 bytes: WallData, 16x16 uint16 values comprising the visual map data (floors, walls, etc...)
256 bytes: CellFlag, 16x16 bytes, each byte holding the flags for one tile
60
64 ("Fog")

2 bytes: mazenumber, uint16 value indicating this map ID (see above)
"SurrMazes":
	2 bytes: uint16 value indicating the map ID to the north
	2 bytes: uint16 value indicating the map ID to the east
	2 bytes: uint16 value indicating the map ID to the south
	2 bytes: uint16 value indicating the map ID to the west
2 bytes: mazeFlags
2 bytes: mazeFlags2
16 bytes: wallTypes, 16 byte array of wall types, used for indirect lookup
16 bytes: surfaceTypes, 16 byte array of surface types (ie, floors) used for indirect lookup
1 byte: floor type, the default floor type (lookup table, used by indoor maps)
1 byte: runX, the X coordinate the party will land at if they run from a fight
1 byte: wallNoPass, wall values greater than or equal to this value cannot be walked through at all.
1 byte: surfNoPass, suface values greater than or equal to this value cannot be stepped on (typically only ever 0x0F, space).
1 byte: unlockDoor, the difficulty of unlocking a door on this map
1 byte: unlockBox, the difficulty of unlocking a chest on this map
1 byte: bashDoor, the difficulty of bashing through a door
1 byte: bashGrate, the difficulty of bashing through a grate
1 byte: bashWall, the difficulty of bashing through a wall (note that there are other requirements to bash through a wall, even if the party is strong enough)
1 byte: chanceToRun, the difficulty of running from a fight
1 byte: runY, the Y coordinate the party will land at if they run from a fight
1 byte: trapDamage, the level of damage the party will receive from traps on this map
1 byte: wallKind, the type of walls, used in a lookup table
1 byte: tavernTips, lookup table for the text file used by the tavern, if any
"Fog":
32 bytes: 16x16 bit array indicating which tiles have been "seen"
32 bytes: 16x16 bit array indicating which tiles have been "stepped on"

indoor wall tiles:

0: empty
2: column
4: small door
7: large door
8: wall
9: gate
10: flag
12: torch

'''



'''
MM3: 832
512
256

64?

indoor wall tiles:

0: empty
2: door
6: gate
7: columns
9: wall
11: art?
12: gate


'''
def combine_nibbles(high_nibble, low_nibble):
    # 1. Shift high_nibble 4 bits to the left
    # 2. Use the OR (|) operator to merge it with low_nibble
    return (high_nibble << 4) | low_nibble

def wall3to4(wall3):
	match wall3:
		case 0: #empty
			return 0
		case 2: #door
			return 4
		case 6: #gate
			return 9
		case 7: #columns
			return 2
		case 9: #wall
			return 8
		case 11: #torch?
			return 12
		case 12: #gate (alt)
			return 6
		case _:
			print("unhandled wall3")
			return 0


def convert_3to4(map):
	mm3to4 = bytearray()

	for y in range(16):#do NOT reverse y
		for x in range(16):
			walladdr = (y*16 + x)*2
			#for outdoors, base/middle/top/overlay type ids
			#for indoors, north/east/south/west wall type ids
			WestiBase = (map[walladdr] & 0x0F);
			SouthiMiddle = (map[walladdr]>>4 & 0x0F);
			EastiTop = (map[walladdr+1] & 0x0F);
			NorthiOverlay = (map[walladdr+1]>>4 & 0x0F);

			# celladdr = y*16 + x + 512
			# cflags = map[celladdr]
			
			# print(f"{NorthiOverlay}|{EastiTop}|{SouthiMiddle}|{WestiBase}({cflags}) ", end="")

			# convert from MM3 enums to MM4 enums
			mm3to4.append(combine_nibbles(wall3to4(SouthiMiddle), wall3to4(WestiBase)))
			mm3to4.append(combine_nibbles(wall3to4(NorthiOverlay), wall3to4(EastiTop)))

	# print(f"mm3to4: {mm3to4}")
	# print("")
	mm3to4.extend(bytearray(256))
	parse_mazedat(mm3to4)
	with open("mm3to4dat.bin", "wb") as f:
		f.write(mm3to4)


def parse_mazedat(map, is_mm3=False):

	for y in range(15,-1,-1):#reverse y
		for x in range(16):
			walladdr = (y*16 + x)*2
			#for outdoors, base/middle/top/overlay type ids
			#for indoors, north/east/south/west wall type ids
			WestiBase = (map[walladdr] & 0x0F);
			SouthiMiddle = (map[walladdr]>>4 & 0x0F);
			EastiTop = (map[walladdr+1] & 0x0F);
			NorthiOverlay = (map[walladdr+1]>>4 & 0x0F);

			celladdr = y*16 + x + 512
			cflags = map[celladdr]
			# {x*10},{128-(y*8)}

			# print(f"cell {x},{y}: {iBase}|{iMiddle}|{iTop}|{iOverlay} ({walladdr}) [{cflags}] ({celladdr})")
			
			print(f"{NorthiOverlay}|{EastiTop}|{SouthiMiddle}|{WestiBase}({cflags}) ", end="")

			# disp = iBase
			# print(f"{'{:2d}'.format(disp) if disp!=0 else "  "} ", end="")

		print("")
		print("")
	print(f"cell flags: {map[512:]}")


def parse_mazeinfo(mazeinfo):

	is_mm3 = False

	mm3id = mazeinfo[31]
	print(f"mm3 map id: {mm3id}")
	mm4id = mazeinfo[0]
	print(f"mm4 map id: {mm4id}")
	# print(f"mm4 map id: {mazeinfo[1]}")

	if mm3id and not mm4id:
		#very dumb "detection"
		is_mm3 = True



	print(f"mm4 surr N: {mazeinfo[2]}")
	print(f"mm4 surr E: {mazeinfo[4]}")
	print(f"mm4 surr S: {mazeinfo[6]}")
	print(f"mm4 surr W: {mazeinfo[8]}")

	print(f"mm4 mazeFlags00: {mazeinfo[10]}")
	print(f"mm4 mazeFlags01: {mazeinfo[11]}")
	print(f"mm4 mazeFlags02: {mazeinfo[12]}") #dark, outdoors
	print(f"mm4 mazeFlags03: {mazeinfo[13]}")
	wallTypes = mazeinfo[14:30]
	surfTypes = mazeinfo[30:46]
	floorType = mazeinfo[46]
	runX = mazeinfo[47]
	wallNoPass = mazeinfo[48]
	surfNoPass = mazeinfo[49]
	unlockDoor = mazeinfo[50]
	unlockBox = mazeinfo[51]
	bashDoor = mazeinfo[52]
	bashGrate = mazeinfo[53]
	bashWall = mazeinfo[54]
	chanceToRun = mazeinfo[55]
	runY = mazeinfo[56]
	trapDmg = mazeinfo[57]
	wallKind = mazeinfo[58]
	tavernTips = mazeinfo[59]

	print(f"wallTypes: {wallTypes}")
	print(f"surfTypes: {surfTypes}")
	print(f"floorType: {floorType}")
	print(f"wallKind: {wallKind}")


	fog = mazeinfo[60:]
	# print(f"mazeinfo remainder {len(fog)}")
	if len(fog) != 64:
		print(f"mm3 mazeinfo remainder: {fog}")

	return is_mm3




def parse_mazefile(filepath):
	print(f"parsing {filepath}")
	with open(filepath, "rb") as f:
		data = f.read()

		mazedat = data[0:768]
		mazeinfo = data[768:]#64 for mm3 (124 for mm4)

		# print(f"mm3 map id: {data[799]}")
		# print(f"mm3 map id: {mazeinfo[31]}")

		# print(f"mm4 map id: {data[768]}")
		# print(f"mm4 map id: {mazeinfo[0]}")
		
		is_mm3 = parse_mazeinfo(mazeinfo)

		parse_mazedat(mazedat, is_mm3)

		if is_mm3:
			convert_3to4(mazedat)

		print("")


'''
MM3 has 90 monsters?

list1: monsters?
list2: sprite objects (fountain, chest)

'''
def parse_mob(filepath):
	print(f"parsing {filepath}")
	with open(filepath, "rb") as f:
		data = f.read()
		fsize = len(data)
		print(f"mob list size: {fsize} {':)' if fsize%3==0 else ':('}")
		list_type = 0
		for iobj in range(fsize//3):
			i = iobj*3
			ox = data[i]
			oy = data[i+1]
			oid = data[i+2]
			if oid > 6:
				list_type+=1
				# print(f"list_type: {list_type}")
				print(f"next list with ids: {oid} {ox} {oy}")
			else:
				print(f"object {oid} at x: {ox}, y: {oy}")



parse_mazefile("ext_cld_world/MAZE0028.DAT")
parse_mazefile("scummvmxeen/mazex255-og.dat")

parse_mazefile("scummvmxeen/mazex255.dat")

parse_mazefile("mm3_default.sav-files/MAZE01.DAT")
# parse_mazefile("mm3_default.sav-files/MAZE02.DAT")

parse_mob("mm3_default.sav-files/MAZE01.MOB")
parse_mob("mm3_default.sav-files/MAZE02.MOB")
parse_mob("mm3_default.sav-files/MAZE03.MOB")

