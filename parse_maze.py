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
		case 12: #town gate?
			return 9 #7
		case _:
			print(f"unhandled wall3: {wall3}")
			return 0

def top3to4(top3):
	match top3:
		case 0: #empty
			return 0
		case 3: #temple
			return 9
		case 6: #caravan
			return 6
		case 8: #empty
			return 0
		case 9: #houses/village
			return 8
		case 14: #caravan
			return 6
		case _:
			print(f"unhandled top3: {top3}")
			return 0


'''
MM4 base layer values (surface type index):

0 = no surface drawn, the default ground sprite shows through
1 = DIRT.SRF
2 = GRASS.SRF
3 = SNOW.SRF
4 = SWAMP.SRF
5 = LAVA.SRF
6 = DESERT.SRF
7 = ROAD.SRF
8 = WATER.SRF
9 = TFLR.SRF
10 = SKY.SRF
11 = CROAD.SRF
12 = SEWER.SRF
13 = CLOUD.SRF
14 = SCORTCH.SRF 
15 = SPACE.SRF
16. space			00	middle layer (wall type index)
17. mountain		01
18. trees			02
19. forest			03
20. tall grass		04
21. pine trees		05
22. pine forest		06
23. mountain2		07
24. birch trees		08
25. hill			09
26. volcano			10
27. palm			11
28. dune			12
29. dead trees		13
30. dead trees2		14
31. space			15
32. space			00	top layer (direct reference)
33. tower			01
34. tent			02
35. hut				03
36. fountain		04
37. castle			05
38. caravan			06
39. pyramid 		07
40. houses			08
41. temple			09
42. wood?			10
43. straw hut		11
44. cave			12
45. temple			13
46. space			14
47. space			15


MM3 OUT.TIL:
0. water
1. mountain
2. trees
3. forest
4. tall grass
5. trees		->	2
6. mountain2	->	1
7. trees
8. hill
9. volcano
10. palm
11. dune
12. grass
13. dirt		->	2
14. snow		->	1
15. swamp
16. lava
17. sand
18. road
19. up
20. down
21. right
22. left
23. houses
24. castle
25. temple
26. hut
27. pyramid
28. caravan
29. gold house?
30. x


'''

def is_mm3_indoor(maze_id):
	if maze_id < 41 or maze_id > 64:
		indoor = True
	else:
		indoor = False
		
	return indoor


def convert_3to4(map, outpath, maze_id):
	indoor = is_mm3_indoor(maze_id) #temp hack
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

			if indoor:
				# convert from MM3 enums to MM4 enums
				mm3to4.append(combine_nibbles(wall3to4(SouthiMiddle), wall3to4(WestiBase)))
				mm3to4.append(combine_nibbles(wall3to4(NorthiOverlay), wall3to4(EastiTop)))
			else:
				# outdoor
				# convert from MM3 enums to MM4 enums

				# mm3to4.append(combine_nibbles(SouthiMiddle, WestiBase))
				# mm3to4.append(combine_nibbles(NorthiOverlay, EastiTop))

				# mm3to4.append(combine_nibbles(WestiBase, SouthiMiddle))
				# mm3to4.append(combine_nibbles(EastiTop, NorthiOverlay))

				# MM3 nibble is actually a 3 bit number?
				# index into 7 byte array at byte offset 768
				# 4th bit purpose TBC...

				#								middle		base
				mm3to4.append(combine_nibbles(WestiBase, SouthiMiddle))
				#								overlay		top
				mm3to4.append(combine_nibbles(0,		 top3to4(EastiTop)))#EastiTop, NorthiOverlay


	# print(f"mm3to4: {mm3to4}")
	# print("")
	mm3to4.extend(bytearray([0x10]) * 256)#cell flags
	mazeinfo = convert_mazeinfo(maze_id)#len60
	mm3to4.extend(mazeinfo)#properties
	mm3to4.extend(bytearray([0xFF]) * 64)#seen/stepped fog (set to true for testing)
	parse_mazedat(mm3to4)
	with open(outpath, "wb") as f:
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

	# if mm3id and not mm4id:
	# 	#very dumb "detection"
	# 	is_mm3 = True

	if is_mm3:
		print("parsing as mm3")
		#hopefully in here we can find flags such as:
		#indoor vs outdoor 
		#surrounding mazes for outdoor areas
		#list of monster ids?

		i00 = mazeinfo[0]
		i01 = mazeinfo[1]
		i02 = mazeinfo[2]
		i03 = mazeinfo[3]
		i04 = mazeinfo[4]
		i05 = mazeinfo[5]
		i06 = mazeinfo[6]

		i07 = mazeinfo[7] #0x64
		# i12~i15 010101
		i16 = mazeinfo[16]
		i17 = mazeinfo[17]
		i18 = mazeinfo[18]
		i19 = mazeinfo[19]
		# i20~i23 010101
		i24 = mazeinfo[24]#0x01
		i25 = mazeinfo[25]#0x01
		i26 = mazeinfo[26]#0x01
		i27 = mazeinfo[27]

		i28 = mazeinfo[28]
		i29 = mazeinfo[29]
		i30 = mazeinfo[30]
		maze_id = mazeinfo[31]
		print(f"mm3 map id: {maze_id}")

		mm3fog = mazeinfo[32:]#seen?

	else:
		print("parsing as mm4")

		maze_id = mazeinfo[0]
		print(f"mm4 map id: {maze_id}")
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

		mm4fog = mazeinfo[60:] #64 bytes (32 seen, 32 stepped on)

	
	return is_mm3, maze_id


def convert_mazeinfo(maze_id):

	mazeinfo = bytearray(60)

	indoor = is_mm3_indoor(maze_id) #temp hack

	# maze_id = 41
	maze_surr_N = 0
	maze_surr_E = 0
	maze_surr_S = 0
	maze_surr_W = 0
	maze_flags00 = 0
	maze_flags01 = 0
	maze_flags02 = 0
	maze_flags03 = 0 if indoor else 128 #indoor 0; outdoor 128

	if indoor:	
		wallTypes = [0x00, 0x01, 0x02, 0x03, 0x00, 0x05, 0x00, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x00, 0x0D, 0x0E, 0x0F]
		surfTypes = [0x00, 0x01, 0x02, 0x03, 0x00, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x00, 0x00, 0x0D, 0x0E, 0x0F]
	else:
		wallTypes = [0x00, 0x01, 0x02, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x00, 0x00, 0x00, 0x00]
		surfTypes = [0x00, 0x01, 0x02, 0x03, 0x04, 0x02, 0x01, 0x07, 0x08, 0x09, 0x0A, 0x00, 0x00, 0x02, 0x01, 0x0F]

	floorType = 0
	runX = 0
	wallNoPass = 7
	surfNoPass = 0
	unlockDoor = 0
	unlockBox = 0
	bashDoor = 0
	bashGrate = 0
	bashWall = 0
	chanceToRun = 0
	runY = 0
	trapDmg = 0
	wallKind = 0
	tavernTips = 0



	mazeinfo[0] = maze_id
	mazeinfo[2] = maze_surr_N
	mazeinfo[4] = maze_surr_E
	mazeinfo[6] = maze_surr_S
	mazeinfo[8] = maze_surr_W
	mazeinfo[10] = maze_flags00
	mazeinfo[11] = maze_flags01
	mazeinfo[12] = maze_flags02
	mazeinfo[13] = maze_flags03
	
	mazeinfo[14:30] = wallTypes
	mazeinfo[30:46] = surfTypes

	mazeinfo[46] = floorType
	mazeinfo[47] = runX
	mazeinfo[48] = wallNoPass
	mazeinfo[49] = surfNoPass
	mazeinfo[50] = unlockDoor
	mazeinfo[51] = unlockBox
	mazeinfo[52] = bashDoor
	mazeinfo[53] = bashGrate
	mazeinfo[54] = bashWall
	mazeinfo[55] = chanceToRun
	mazeinfo[56] = runY
	mazeinfo[57] = trapDmg
	mazeinfo[58] = wallKind
	mazeinfo[59] = tavernTips

	return mazeinfo


def parse_mazefile(filepath, outpath='mm3to4dat.bin'):
	print(f"parsing {filepath}")
	with open(filepath, "rb") as f:
		data = f.read()

		mazedat = data[0:768]
		mazeinfo = data[768:]#64 for mm3 (124 for mm4)

		# print(f"mm3 map id: {data[799]}")
		# print(f"mm3 map id: {mazeinfo[31]}")

		# print(f"mm4 map id: {data[768]}")
		# print(f"mm4 map id: {mazeinfo[0]}")
		
		is_mm3, maze_id = parse_mazeinfo(mazeinfo)

		parse_mazedat(mazedat, is_mm3)

		if is_mm3:
			print("converting 3to4:")
			convert_3to4(mazedat, outpath, maze_id)


		print("")



parse_mazefile("ext_cld_world/MAZE0028.DAT")
# parse_mazefile("scummvmxeen/mazex255-og.dat")
parse_mazefile("ext_cld_world/MAZE0023.DAT")

# parse_mazefile("scummvmxeen/mazex255.dat")

parse_mazefile("mm3_default.sav-files/MAZE01.DAT")
# parse_mazefile("mm3_default.sav-files/MAZE02.DAT")
# parse_mazefile("mm3_default.sav-files/MAZE41.DAT")

