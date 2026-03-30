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
	mm3to4.extend(bytearray([0x10]) * 256)#cell flags
	mm3to4.extend(bytearray(60))#properties
	mm3to4.extend(bytearray([0xFF]) * 64)#seen/stepped fog (set to true for testing)
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
	#example: 	cell	 17 (0x11) (0b00010001)
	#FLAG_AUTOEXECUTE_EVENT = 0x10 (0b00010000)


def parse_mazeinfo(mazeinfo):

	is_mm3 = False

	if (len(mazeinfo)==64):
		is_mm3 = True

	mm3id = mazeinfo[31]
	print(f"mm3 map id: {mm3id}")
	mm4id = mazeinfo[0]
	print(f"mm4 map id: {mm4id}")
	# print(f"mm4 map id: {mazeinfo[1]}")

	# if mm3id and not mm4id:
	# 	#very dumb "detection"
	# 	is_mm3 = True

	if is_mm3:
		print("parsing as mm3")
		i07 = mazeinfo[7]
		# i12~i15 010101
		i16 = mazeinfo[16]
		i17 = mazeinfo[17]
		i18 = mazeinfo[18]
		i19 = mazeinfo[19]
		# i20~i23 010101
		i24 = mazeinfo[24]
		i25 = mazeinfo[25]
		i26 = mazeinfo[26]
		i27 = mazeinfo[27]

		i28 = mazeinfo[28]
		i29 = mazeinfo[29]
		i30 = mazeinfo[30]
		mm3id = mazeinfo[31]

		mm3fog = mazeinfo[32:]#seen?

	else:
		print("parsing as mm4")

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


		mm4fog = mazeinfo[60:] #64 bytes (32 seen, 32 stepped on)

	

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
			print("converting 3to4:")
			convert_3to4(mazedat)

		print("")


'''
MM3 has 90 monster types?

list1: monsters
list2: sprite objects (fountain, chest)

'''
def parse_mm3_mob(filepath):
	print(f"parsing {filepath}")
	with open(filepath, "rb") as f:
		data = f.read()
		fsize = len(data)

		mm4_mids = bytearray()
		mm4_monsters = bytearray()
		mm4_oids = bytearray()
		mm4_objects = bytearray()

		print(f"mm3 mob list size: {fsize} {':)' if fsize%3==0 else ':('}")

		skip1 = False
		print("monster list ids: ???")
		for iobj in range(fsize//3):
			if skip1:
			    skip1 = False
			    continue

			i = iobj*3

			ox = data[i]
			oy = data[i+1]
			oid = data[i+2]

			if ox==255:
				# print(f"list_type: {list_type}")
				oid0 = data[i+1]
				oid1 = data[i+2]
				oid2 = data[i+3]
				oid3 = data[i+4]
				oid4 = data[i+5]

				print(f"object list ids: \n0: {oid0:2d}\n1: {oid1:2d}\n2: {oid2:2d}\n3: {oid3:2d}{'' if oid4==255 else f'\n4: {oid4:2d}'}")
				# mm4_oids.extend([oid0, oid1, oid2, oid3, oid4])
				mm4_oids.extend([0x00, 0x01, 0x02, 0x03, 0x04])
				mm4_oids.extend(bytearray([0xFF]) * 11)

				mm4_mids.extend([0x02, 0x00, 0xFF, 0xFF, 0xFF])
				mm4_mids.extend(bytearray([0xFF]) * 11)

				skip1 = True
			else:
				print(f"({ox:2d}, {oy:2d}) id: {oid}")
				if mm4_oids:
					if ox<16 and oy<16 and oid<16:
						mm4_objects.extend([ox, oy, oid, 0x00])
				else:
					if ox<16 and oy<16 and oid<16:
						mm4_monsters.extend([ox, oy, oid, 0x00])


		mm4_mob = bytearray()

		mm4_mob.extend(mm4_oids)#object sprite id list
		mm4_mob.extend(mm4_mids)#monster id list
		mm4_mob.extend(bytearray([0xFF]) * 16)#wall object sprite id list

		mm4_mob.extend(mm4_objects)#objects list
		mm4_mob.extend(bytearray([0xFF]) * 4)

		mm4_mob.extend(mm4_monsters)#monsters list
		mm4_mob.extend(bytearray([0xFF]) * 4)

		mm4_mob.extend(bytearray([128,128,0,0]))#wall sprites list
		mm4_mob.extend(bytearray([0xFF]) * 4)

		with open("mm3to4mob.bin", "wb") as f:
			f.write(mm4_mob)


parse_mazefile("ext_cld_world/MAZE0028.DAT")
parse_mazefile("scummvmxeen/mazex255-og.dat")

parse_mazefile("scummvmxeen/mazex255.dat")

parse_mazefile("mm3_default.sav-files/MAZE01.DAT")
# parse_mazefile("mm3_default.sav-files/MAZE02.DAT")

parse_mm3_mob("mm3_default.sav-files/MAZE01.MOB")
# parse_mm3_mob("mm3_default.sav-files/MAZE02.MOB")
# parse_mm3_mob("mm3_default.sav-files/MAZE03.MOB")
# parse_mm3_mob("mm3_default.sav-files/MAZE04.MOB")
# parse_mm3_mob("mm3_default.sav-files/MAZE05.MOB")
# parse_mm3_mob("mm3_default.sav-files/MAZE06.MOB")
# parse_mm3_mob("mm3_default.sav-files/MAZE07.MOB")
# parse_mm3_mob("mm3_default.sav-files/MAZE08.MOB")
# parse_mm3_mob("mm3_default.sav-files/MAZE09.MOB")


