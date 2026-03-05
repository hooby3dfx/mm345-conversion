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
'''


'''
MM3: 832
512
256

64?


'''

def parse_mazedat(map):
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

	print(f"mm3 map id: {mazeinfo[31]}")


	print(f"mm4 map id: {mazeinfo[0]}")
	# print(f"mm4 map id: {mazeinfo[1]}")

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
		
		parse_mazedat(mazedat)

		parse_mazeinfo(mazeinfo)

		print("")



parse_mazefile("ext_cld_world/MAZE0028.DAT")
parse_mazefile("scummvmxeen/mazex255-og.dat")

parse_mazefile("scummvmxeen/mazex255.dat")

parse_mazefile("mm3_default.sav-files/MAZE01.DAT")
parse_mazefile("mm3_default.sav-files/MAZE02.DAT")

