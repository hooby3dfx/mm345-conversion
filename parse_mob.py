import re

'''
MM3 has 90 monster types?

list1: monsters
list2: sprite objects (fountain, chest)

'''


def oid3to4(oid3):
	match oid3:
		# case 8: #desk
		# 	print(f"converting oid3 {oid3}")
		# 	return 1 #temp remapping to workaround sprite issue
		# case 45: #wagon
		# 	print(f"converting oid3 {oid3}")
		# 	return 1 #temp remapping to workaround sprite issue
		# case 49: #DUNGNDOR
		# 	print(f"converting oid3 {oid3}")
		# 	return 1 #temp remapping to workaround sprite issue
		case _:
			# return 1
			return oid3

def get_monsters_for_mazeid(maze_id):
	#from https://dungeoncrawl-classics.com/might-and-magic/mm3/mm3-guide/
	maze_monster_map = [
		[],
		[0x01,0x07,0x07],	# Fountain Head /Foes: Bubble Man, Moose Rat, Rat Overlord
		[0x00,0x01,0x02],	# Baywatch
		[0x00,0x01,0x02],	# Wildabar
		[0x00,0x01,0x02],	# Swamp Town
		[0x00,0x01,0x02],	# Blistering Heights
		[0x00,0x02,0x07],	# Fountain Head Cavern /Foes: Vampire Bat, Goblin, Moose Rat
		[0x00,0x01,0x02],	# Baywatch Cavern
		[0x00,0x01,0x02],	# Wildabar Cavern
		[0x00,0x01,0x02],	# Swamp Town Cavern
		[0x00,0x01,0x02],	# Blistering Heights Cavern
		[0x00,0x01,0x02],	# Cyclops Cavern
		[0x00,0x01,0x02],	# Arachnoid Cavern
		[0x00,0x01,0x02],	# Cursed Cold Cavern
		[0x00,0x01,0x02],	# Dragon Cavern
		[0x00,0x01,0x02],	# The Magic Cavern
		[0x00,0x01,0x02],	# Ancient Temple of Moo
		[0x00,0x01,0x02],	# Slithercult Stronghold
		[0x00,0x01,0x02],	# Fortress of Fear
		[0x00,0x01,0x02],	# Halls of Insanity
		[0x00,0x01,0x02],	# Dark Warrior Keep
		[0x00,0x01,0x02],	# Cathedral of Carnage
		[0x00,0x01,0x02],	# Tomb of Terror
		[0x00,0x01,0x02],	# The Maze From Hell
		[0x00,0x01,0x02],	# Castle Whiteshield
		[0x00,0x01,0x02],	# Castle Bloodreign
		[0x00,0x01,0x02],	# Castle Dragontooth
		[0x00,0x01,0x02],	# Castle Greywind
		[0x00,0x01,0x02],	# Castle Blackwind
		[0x00,0x01,0x02],	# Whiteshield Dungeon
		[0x00,0x01,0x02],	# Bloodreign Dungeon
		[0x00,0x01,0x02],	# Dragontooth Dungeon
		[0x00,0x01,0x02],	# Greywind Dungeon
		[0x00,0x01,0x02],	# Blackwind Dungeon
		[0x00,0x01,0x02],	# Alpha Engine Sector
		[0x00,0x01,0x02],	# Main Engine Sector
		[0x00,0x01,0x02],	# Beta Engine Sector
		[0x00,0x01,0x02],	# Aft Storage Sector
		[0x00,0x01,0x02],	# Central Control Sector
		[0x00,0x01,0x02],	# Forward Storage Sector
		[0x00,0x01,0x02],	# Main Control Sector
		[0x00,0x01,0x02],	# A1
		[0x00,0x01,0x02],	# A2
		[0x00,0x01,0x02],	# A3
		[0x00,0x01,0x02],	# A4
		[0x00,0x01,0x02],	# B1
		[0x00,0x01,0x02],	# B2
		[0x00,0x01,0x02],	# B3
		[0x00,0x01,0x02],	# B4
		[0x00,0x01,0x02],	# C1
		[0x00,0x01,0x02],	# C2
		[0x00,0x01,0x02],	# C3
		[0x00,0x01,0x02],	# C4
		[0x00,0x01,0x02],	# D1
		[0x00,0x01,0x02],	# D2
		[0x00,0x01,0x02],	# D3
		[0x00,0x01,0x02],	# D4
		[0x00,0x01,0x02],	# E1
		[0x00,0x01,0x02],	# E2
		[0x00,0x01,0x02],	# E3
		[0x00,0x01,0x02],	# E4
		[0x00,0x01,0x02],	# F1
		[0x00,0x01,0x02],	# F2
		[0x00,0x01,0x02],	# F3
		[0x00,0x01,0x02],	# F4
		[0x00,0x01,0x02],	# It's a Secret
		[0x00,0x01,0x02],	# The Arena
	]

	if maze_id < len(maze_monster_map):
		return maze_monster_map[maze_id]

	else:
		return [0x00,0x01,0x02]



def parse_mm3_mob(filepath, outpath="mm3to4mob.bin"):
	print(f"parsing {filepath}")
	with open(filepath, "rb") as f:
		data = f.read()
		fsize = len(data)

		mm4_mids = bytearray()
		mm4_monsters = bytearray()
		mm4_oids = bytearray()
		mm4_objects = bytearray()

		#parse last number from the filename for the mazeid...
		mazeid = int(re.findall(r'\d+', f.name)[-1])
		print(f"mazeid: {mazeid}")

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
				oid0 = oid3to4(data[i+1])
				oid1 = oid3to4(data[i+2])
				oid2 = oid3to4(data[i+3])
				oid3 = oid3to4(data[i+4])
				oid4 = oid3to4(data[i+5])

				print(f"object list ids: \n0: {oid0:2d}\n1: {oid1:2d}\n2: {oid2:2d}\n3: {oid3:2d}{'' if oid4==255 else f'\n4: {oid4:2d}'}")
				
				# if oid0==9 or oid1==9 or oid2==9 or oid3==9 or oid4==9:
				# 	print("oid was 9!!!")
				# 	assert False

				mm4_oids.extend([oid0, oid1, oid2, oid3, oid4])
				# mm4_oids.extend([0x00, 0x01, 0x02, 0x03, 0x04])
				# mm4_oids.extend([0x24, 0x10, 0x28, 0x0B, 0x08])
				mm4_oids.extend(bytearray([0xFF]) * 11)

				#TODO actually determine the monster IDs from MM3. if they are hardcoded in exe just make a table
				# mid0 = 0x00
				# mid1 = 0x01
				# mid2 = 0x02
				# mid3 = 0xFF
				# mid4 = 0xFF
				# mm4_mids.extend([mid0, mid1, mid2, mid3, mid4])
				# mm4_mids.extend(bytearray([0xFF]) * 11)

				mm4_mids.extend(get_monsters_for_mazeid(mazeid))
				mm4_mids.extend(bytearray([0xFF]) * 13)

				skip1 = True
			elif oy==255:
				print("early termination; skipping")
				skip1 = True
			else:
				print(f"({ox:2d}, {oy:2d}) id: {oid}")
				if mm4_oids:
					if ox<16 and oy<16 and oid<16:
						#					x	y	id	facing direction
						mm4_objects.extend([ox, oy, oid, 0x01])
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

		with open(outpath, "wb") as f:
			f.write(mm4_mob)



# parse_mm3_mob("mm3_default.sav-files/MAZE01.MOB")
# parse_mm3_mob("mm3_default.sav-files/MAZE02.MOB")
# parse_mm3_mob("mm3_default.sav-files/MAZE03.MOB")
# parse_mm3_mob("mm3_default.sav-files/MAZE04.MOB")
# parse_mm3_mob("mm3_default.sav-files/MAZE05.MOB")
# parse_mm3_mob("mm3_default.sav-files/MAZE06.MOB")
# parse_mm3_mob("mm3_default.sav-files/MAZE07.MOB")
# parse_mm3_mob("mm3_default.sav-files/MAZE08.MOB")
# parse_mm3_mob("mm3_default.sav-files/MAZE09.MOB")

# parse_mm3_mob("mm3_default.sav-files/MAZE54.MOB")
# parse_mm3_mob("mm3_default.sav-files/MAZE40.MOB")
# parse_mm3_mob("mm3_default.sav-files/MAZE41.MOB")
# parse_mm3_mob("mm3_default.sav-files/MAZE42.MOB")
# parse_mm3_mob("mm3_default.sav-files/MAZE54.MOB")

parse_mm3_mob("mm3_default.sav-files/MAZE16.MOB")

