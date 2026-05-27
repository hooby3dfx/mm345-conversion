import argparse
import os
from pathlib import Path
import re

from parse_maze import parse_mazefile
from parse_event import parse_evt_file
from parse_mob import parse_mm3_mob
from mm3to4_sprite_transcoder2 import convert_sprite_3to4
from mm4_sprite_merge import merge_mm4_sprites
from mm4_sprite_merge2 import merge_mm4_multi_frame
from mm4_sprite_merge3 import merge_mm4_optimized
from hashFileName import hash_file_name_mm4
from sprite_inspect import inspect_sprite
from parse_monsters import parse_monsters

'''
OK so here we go.

this script will do the following:

1. parse/convert all MM3 map related data to MM4 format and save to output folder
	inputs: 
	- MAZEYY.DAT
	- MAZEYY.EVT
	- MAZEYY.MOB
	- textYY.maz
	outputs: 
	- MAZE00YY.DAT
	- MAZE00YY.EVT
	- MAZE00YY.MOB
	- AAZE00YY.TXT	(strings file)
	- AAZE00YY.HED	(512, empty file?)
	- XEEN00YY.TXT  (name file)

2. parse/convert all MM3 monster/object sprite graphics data to MM4 format and save to output folder
	inputs: 
	- mm3 pallete
	- *.mon (monster sprites)
	- *.pic (object sprites)
	outputs:
	-YYY.OBJ (object sprites)
	-YYY.MON (monster sprites, 8 frames)
	-YYY.ATT (monster sprites, 4 frames)
	NOTE: DARK.CC skips a bunch of numbers. nice. 

3. parse/convert all MM3 environment graphics related data to MM4 format and save to output folder
	inputs:
	- *.vga 
		walls, ground: cavwl1.vga; twnwl4.vga; 
		surface: dirt.vga
		sky: day.vga
	twnwl1.vga
		frame 00	front
		frame 01	front
		frame 02	front
		frame 03	front
		frame 04	side
		frame 05	side
		frame 06	front
		frame 07	front
		frame 08	front
		frame 09	front
		frame 10	front pillars
		frame 11	side pillars
		frame 12	side pillars

	- *.til (cave.til)
	- *.sky (cav.sky)

	outputs:
	- *.GND	ground (1 frame 'skymap' for ground)
	- *.SKY	(2 frames)
	- *.TIL	environment minimap
	- *.SRF	surface (25 frames for ground)
	- *.SWL side walls (48 frames, all in 1 file)
	- *.FWL	front walls (split into 4 files; #frames: 8, 11, 34, 17)
		

4. parse/convert all MM3 meta info
	inputs:
	- *.bin (text)
	- Mon*.dat (Monster stats)
	outputs:
	- XEEN.MON (Monster stats)
	- CLOUDS.dat (object sprites info)
	- SPELLS.XEN, MAE.XEEN

5. parse/convert all MM3 "2D" graphics
	inputs:
	- *.fac (Portrait sprite)
	- eface*.out (Animated face)
	- *.out (Town location animation ie temple, guild, bank)
	- *.icn (icons)
	outputs:
	- *.fac
		CHAR01.FAC (5 frames) 24 sprites
		FACE01.FAC (4 frames) 44 sprites
	- *.icn (icons)

6. parse/convert all MM3 media files
	inputs:
	- *.m (music)
	outputs:
	- *.m (music)

'''

def copy_file(src, dst):
	print(f"copy_file: {src} to {dst}")
	with open(src, 'rb') as source:
		content = source.read()
		with open(dst, 'wb') as dest:
			dest.write(content)

def hash_filename(name):
	return f"d_{hash_file_name_mm4(name)}.ccx"

def remap_sprites(filemaps, in_dir, out_dir, mm3_prefix="", mm4_prefix=""):
	for filemap in filemaps:
		dst_file = mm4_prefix+filemap[0]
		mapping = filemap[1]

		for i in range(len(mapping)):

			src_file = mm3_prefix+mapping[i][0]
			src_frame = mapping[i][1]
			if len(mapping[i])==2:
				convert_sprite_3to4(in_dir+"/"+src_file, out_dir+"/"+dst_file+f"{i:02}", frame_number=src_frame)
			elif len(mapping[i])==3:
				src_y_end = mapping[i][2]
				convert_sprite_3to4(in_dir+"/"+src_file, out_dir+"/"+dst_file+f"{i:02}", frame_number=src_frame, y_end=src_y_end)
			if i==0:
				#for first file, copy/rename as a merged file
				copy_file(out_dir+"/"+dst_file+f"{i:02}", out_dir+"/"+dst_file+f"m{i:02}")
			if i>0:
				#after the first file, merge previous and current
				merge_mm4_optimized(out_dir+"/"+dst_file+f"m{i-1:02}", out_dir+"/"+dst_file+f"{i:02}", out_dir+"/"+dst_file+f"m{i:02}")
			if i==len(mapping)-1:
				#if last file, we are done and can rename current/last file as the final output
				mm4_hash = hash_filename(dst_file)
				copy_file(out_dir+"/"+dst_file+f"m{i:02}", out_dir+"/"+mm4_hash)


MM3_MAZE_NAMES = [
	'Fountain Head','Baywatch','Wildabar','Swamp Town','Blistering Heights','Fountain Head Cavern','Baywatch Cavern','Wildabar Cavern',
	'Swamp Town Cavern','Blistering Heights Cavern','Cyclops Cavern','Arachnoid Cavern','Cursed Cold Cavern','Dragon Cavern','The Magic Cavern','Ancient Temple of Moo',
	'Slithercult Stronghold','Fortress of Fear','Halls of Insanity','Dark Warrior Keep','Cathedral of Carnage','Tomb of Terror','The Maze From Hell','Castle Whiteshield',
	'Castle Bloodreign','Castle Dragontooth','Castle Greywind','Castle Blackwind','Whiteshield Dungeon','Bloodreign Dungeon','Dragontooth Dungeon','Greywind Dungeon',
	'Blackwind Dungeon','Alpha Engine Sector','Main Engine Sector','Beta Engine Sector','Aft Storage Sector','Central Control Sector','Forward Storage Sector','Main Control Sector',
	'A1','A2','A3','A4','B1','B2','B3','B4',
	'C1','C2','C3','C4','D1','D2','D3','D4',
	'E1','E2','E3','E4','F1','F2','F3','F4',
	'It\'s a Secret','The Arena',]


def convert_maps(in_dir, out_dir):
	print("convert_maps")
	dir_path = Path(in_dir)

	print("finding mm3 maze dat files")
	files = dir_path.glob('MAZE*.DAT')
	for file in sorted(files):
		print(file.name)
		match = re.search(r'\d+', file.name)
		num = match.group()
		numi = int(num)

		if numi==29:
			#for darkside, maze29 is castleview; it seems like when starting a new game this 
			#maze gets corrupted and then saves dont work. needs further investigation.
			# continue
			print("be careful for maze29 with darksize/wox")

		print(f"for MM3 maze {num}")
		maze_dat = f"MAZE{num}.DAT"
		maze_evt = f"MAZE{num}.EVT"
		maze_mob = f"MAZE{num}.MOB"
		maze_txt = f"text{num}.maz"

		# convert/generate DAT, HED, name TXT files
		if Path(in_dir+"/"+maze_dat).is_file():
			print(f"found maze DAT file: {maze_dat}")
			maze_dat_mm4 = f"MAZE{numi:04}.DAT" if numi < 100 else f"MAZEX{numi:03}.DAT"
			print(f"target MM4 maze DAT file: {maze_dat_mm4}")
			parse_mazefile(in_dir+"/"+maze_dat, out_dir+"/"+maze_dat_mm4)

			maze_hed_mm4 = f"AAZE{numi:04}.HED" if numi < 100 else f"AAZEX{numi:03}.HED"
			hed_data = bytearray(512)
			with open(out_dir+"/"+maze_hed_mm4, 'wb') as dest:
				dest.write(hed_data)

			base_id = "DARK" #XEEN or DARK
			maze_id_mm4 = f"{base_id}{numi:04}.TXT" if numi < 100 else f"{base_id}X{numi:03}.TXT"
			if numi <= 66:
				maze_name = MM3_MAZE_NAMES[numi-1]
			else:
				maze_name = f"MM3 MAZE{num}"
			maze_name_bytes = bytearray(maze_name.encode())
			maze_name_bytes.append(0x00)
			with open(out_dir+"/"+maze_id_mm4, 'wb') as dest:
				dest.write(maze_name_bytes)

		else:
			print("no maze DAT file")

		if Path(in_dir+"/"+maze_evt).is_file():
			print(f"found maze EVT file: {maze_evt}")
			maze_evt_mm4 = f"MAZE{numi:04}.EVT" if numi < 100 else f"MAZEX{numi:03}.EVT"
			print(f"target MM4 maze EVT file: {maze_evt_mm4}")
			parse_evt_file(in_dir+"/"+maze_evt, out_dir+"/"+maze_evt_mm4)
		else:
			print("no maze EVT file")

		if Path(in_dir+"/"+maze_mob).is_file():
			print(f"found maze MOB file: {maze_mob}")
			maze_mob_mm4 = f"MAZE{numi:04}.MOB" if numi < 100 else f"MAZEX{numi:03}.MOB"
			print(f"target MM4 maze MOB file: {maze_mob_mm4}")
			parse_mm3_mob(in_dir+"/"+maze_mob, out_dir+"/"+maze_mob_mm4)
		else:
			print("no maze MOB file")

		if Path(in_dir+"/"+maze_txt).is_file():
			print(f"found maze TXT file: {maze_txt}")
			maze_txt_mm4 = f"AAZE{numi:04}.TXT" if numi < 100 else f"AAZEX{numi:03}.EVT"
			print(f"target MM4 maze TXT file: {maze_txt_mm4}")
			#straight copy
			copy_file(in_dir+"/"+maze_txt, out_dir+"/"+maze_txt_mm4)
		else:
			print("no maze TXT file")


MM3_OBJ_SPRITE_NAMES = [
	'ALTRBALL','ALTRCUP','ALTRGEM','ALTRHEAD','BLKBOX','BONES','CAULDRON','CRYSTALS',
	'DESK','DESK','FLRBEAM','FLRELEC','FLRLEVR','FLRSAFE','FLRSPER','GONG','HORSE',
	'HOURGLAS','IRONCHST','LION','LEATHSAC','MERMAID','MONSTER','ORNTBOX','PENDLM',
	'PIT','POOLR','POOLG','RIP','SEAHRS1','SHAKLE','SIGNPOST','SKULPOST',
	'STONCOFN','THRONE','TRAPDOOR','TRSRPILE','WARRIOR','WDNCHST','WHRLPOOL','WOODCFN',
	'MIRROR','CASTLE','TOWN','PYRAMID','WAGON','VILLGHUT','LATTERDN','LATTERUP',
	'DUNGNDOR','CAVEOPN','CEILAXE','FLRFIRE','SEWAGE','VAPOR','BARREL','FOUNTHED',
	'POOLB','POOLY','well','tube','town2','dcastle']

MM3_MON_SPRITE_NAMES = [
	'bat','bublman','goblin','orc','skel','head','wasp','rat',
	'shriek','zombie','candle','dwarf','ninja','mantis','hamr','bugeye',
	'repthed','spider','sprite','beetle','cobra','scorpia','flytrap','jester',
	'minidrgn','plasmoid','hand','ghoul','gatekepr','phantom','pirana','ranger',
	'thief','treeglum','witch','robo2','dthlocus','archer','ballface','barbaran',
	'cleric','firelzrd','firemon','gargoyle','ghost','lizard','sonicnja','beholder',
	'cris','paladin','pegasus','reaper','sorc','lich','shield','troll',
	'demon','dino','robo','blknight','martface','mummy','powsorc','cataplr',
	'undragon','cyclop','devil','grndrgn','wizard','worm','vampire','werewolf',
	'termnatr','hydra','roc','kudo','medusa','minotaur','octobest','draglord',
	'rat','rat','rat','rat','rat','rat','rat','rat','rat',]#last 9 reuse sprites


def convert_sprites(in_dir, out_dir):
	print("convert_sprites")

	# MM3 palette
	hex_pal = "0000003F 3F3F3C3C 3C3A3A3A 38383835 35353333 33313131 2F2F2F2C 2C2C2A2A 2A282828 25252523 23232121 211F1F1F 1D1D1D1B 1B1B1919 19171717 15151513 13131111 110F0F0F 0D0D0D0B 0B0B0909 09070707 05050503 03030101 01000000 3F3A3A3E 35353D30 303C2C2C 3B28283A 2323391F 1F391B1B 38171737 13133610 10350C0C 34080833 05053202 02320000 2E00002A 00002600 00210000 1D000019 00001500 00110000 0D00003F 1D003719 00301600 28120021 0F00190B 00120800 3F3F363F 3F2E3E3F 263E3F1E 3E3F163D 3F0E3D3F 063B3D00 3B3B0038 37003533 00322E00 2F2A002C 26002922 00261F00 221A001E 16001A12 00160F00 120B000E 08000A05 00060300 363F1631 3B112D38 0D29340A 25310621 2D031D2A 011A2700 15240013 2100121F 00111D00 101B000E 19000D17 000C1500 0B13002F 3E2F273C 26203A1F 17381710 37100B35 0A0A3209 082F0807 2D07062A 06052704 04240403 2203021F 02021C02 011A0101 17010114 00001100 000F0000 0C000009 00000700 3C3C3F38 383F3333 3F2F2F3F 2B2C3F27 283F2323 3F1F203F 1B1C3F17 183F1314 3F0F103F 0B0C3F07 083F0304 3F00013F 00003F00 003B0000 37000033 00002F00 002B0000 27000024 00002000 001C0000 18000014 00001000 000C0000 08000005 3C363F39 2E3F3627 3F341F3F 32173F2F 103F2D08 3F2A003F 26003920 00321B00 2B150023 0F001B0A 00140600 0C020005 333F3F2D 3B3B2738 38223535 1D323219 2F2F142B 2B112828 0D242409 1F1F071B 1B041717 02131301 0F0F000B 0B000707 3A3C3E36 3A3D3137 3D2D353D 29333C25 313C2130 3C1D2E3B 192C3B15 2B3B1129 3A0D283A 0A263A06 25390224 39012136 011F3300 1D30001B 2D00192B 00172800 15250014 2200121F 00101C00 0E18000C 15000A12 00080F00 060C0005 09000306 3F3A373F 37333F35 303F332C 3F31293F 2F253F2D 223F2B1F 3F291B3F 27183C25 173A2416 38221536 21143420 14321F13 2F1D112C 1B10291A 0E26180D 23160C20 150A1D13 091A1108 170F0714 0D06110C 050E0A03 0B080309 06020604 013F3F3F"
	raw_palette = bytes.fromhex(hex_pal)
	pal_name = "MM4" # MM4, MM4E, DARK, MIRROR
	with open(out_dir+"/"+f"{pal_name}.PAL", "wb") as f:
		f.write(raw_palette)
	copy_file(out_dir+"/"+f"{pal_name}.PAL", out_dir+"/"+hash_filename(f"{pal_name}.PAL"))

	#object sprites
	for i in range(len(MM3_OBJ_SPRITE_NAMES)):
		mm3_obj = MM3_OBJ_SPRITE_NAMES[i]+".pic"
		mm4_obj = f"{(i):03}.OBJ"
		mm4_hash = hash_filename(mm4_obj)

		mm3_frame_ct = inspect_sprite(in_dir+"/"+mm3_obj, True)
		mm4_frame_ct = inspect_sprite("ext_cld"+"/"+mm4_hash, True)
		if not mm4_frame_ct:
			# mm4_frame_ct = 3
			if mm3_obj == "TOWN.pic":
				mm4_frame_ct = 3

		print(f"converting obj sprite {mm3_obj} ({mm3_frame_ct} frames) to {mm4_obj} ({mm4_frame_ct} frames) [{mm4_hash}]")

		#some slots seem to be hardcoded with certain animations or properties.
		#idea: as a workaround, add dummy frames?
		#also - some of these slots dont exist (like 059.obj in xeen)

		sprite_width = 250
		convert_sprite_3to4(in_dir+"/"+mm3_obj, out_dir+"/"+mm4_obj, False, out_width=sprite_width)

		if mm4_frame_ct and mm3_frame_ct < mm4_frame_ct:
			#fill missing frames with frame 0
			num_frame_diff = mm4_frame_ct - mm3_frame_ct
			print(f"adding {num_frame_diff} extra frames")
			convert_sprite_3to4(in_dir+"/"+mm3_obj, out_dir+"/"+mm4_obj+"0", False, out_width=sprite_width, frame_number=0)
			for j in range(num_frame_diff):
				merge_mm4_optimized(out_dir+"/"+mm4_obj, out_dir+"/"+mm4_obj+"0", out_dir+"/"+mm4_obj)


		# hash mm4_obj to .ccx name for packing
		copy_file(out_dir+"/"+mm4_obj, out_dir+"/"+mm4_hash)


	# generate object sprite dat file
	# https://xeen.fandom.com/wiki/CLOUDS.DAT_File
	# TODO enter correct values
	sprite_dat_mm4 = f"DARK.DAT"
	mm4_hash = hash_filename(sprite_dat_mm4)
	sprite_dat_data = bytearray(1452)
	with open(out_dir+"/"+sprite_dat_mm4, 'wb') as dest:
		dest.write(sprite_dat_data)
	copy_file(out_dir+"/"+sprite_dat_mm4, out_dir+"/"+mm4_hash)


	#monster sprites
	for i in range(len(MM3_MON_SPRITE_NAMES)):
		mm3_mon = MM3_MON_SPRITE_NAMES[i]+".mon"
		mm4_mon = f"{(i):03}.MON"
		mm4_att = f"{(i):03}.ATT"

		print(f"converting mon sprite {mm3_mon} to {mm4_mon} and {mm4_att}")
		sprite_width = 250
		sprite_height_off = 50
		#Xeen mon sprites are 8 frames, att sprites are 4 frames
		#...can there be more?
		# convert_sprite_3to4(in_dir+"/"+mm3_mon, out_dir+"/"+mm4_mon, False, out_width=sprite_width)

		mm3_frame_ct = inspect_sprite(in_dir+"/"+mm3_mon, True)
		if (mm3_frame_ct<=3):
			#if there are less than 3 frames, duplicate them so there are 6 to work with
			merge_mm4_optimized(in_dir+"/"+mm3_mon, in_dir+"/"+mm3_mon, in_dir+"/"+mm3_mon+"x2")
			mm3_mon = mm3_mon+"x2"

		convert_sprite_3to4(in_dir+"/"+mm3_mon, out_dir+"/"+mm4_mon+"00", False, out_width=sprite_width, out_height_off=sprite_height_off, frame_number=0)
		convert_sprite_3to4(in_dir+"/"+mm3_mon, out_dir+"/"+mm4_mon+"01", False, out_width=sprite_width, out_height_off=sprite_height_off, frame_number=1)
		convert_sprite_3to4(in_dir+"/"+mm3_mon, out_dir+"/"+mm4_mon+"02", False, out_width=sprite_width, out_height_off=sprite_height_off, frame_number=2)
		convert_sprite_3to4(in_dir+"/"+mm3_mon, out_dir+"/"+mm4_mon+"03", False, out_width=sprite_width, out_height_off=sprite_height_off, frame_number=3)
		convert_sprite_3to4(in_dir+"/"+mm3_mon, out_dir+"/"+mm4_mon+"04", False, out_width=sprite_width, out_height_off=sprite_height_off, frame_number=0)
		convert_sprite_3to4(in_dir+"/"+mm3_mon, out_dir+"/"+mm4_mon+"05", False, out_width=sprite_width, out_height_off=sprite_height_off, frame_number=1)
		convert_sprite_3to4(in_dir+"/"+mm3_mon, out_dir+"/"+mm4_mon+"06", False, out_width=sprite_width, out_height_off=sprite_height_off, frame_number=2)
		convert_sprite_3to4(in_dir+"/"+mm3_mon, out_dir+"/"+mm4_mon+"07", False, out_width=sprite_width, out_height_off=sprite_height_off, frame_number=3)

		merge_mm4_optimized(out_dir+"/"+mm4_mon+"00", out_dir+"/"+mm4_mon+"01", out_dir+"/"+mm4_mon+"a")
		merge_mm4_optimized(out_dir+"/"+mm4_mon+"a", out_dir+"/"+mm4_mon+"02", out_dir+"/"+mm4_mon+"b")
		merge_mm4_optimized(out_dir+"/"+mm4_mon+"b", out_dir+"/"+mm4_mon+"03", out_dir+"/"+mm4_mon+"c")
		merge_mm4_optimized(out_dir+"/"+mm4_mon+"c", out_dir+"/"+mm4_mon+"04", out_dir+"/"+mm4_mon+"d")
		merge_mm4_optimized(out_dir+"/"+mm4_mon+"d", out_dir+"/"+mm4_mon+"05", out_dir+"/"+mm4_mon+"e")
		merge_mm4_optimized(out_dir+"/"+mm4_mon+"e", out_dir+"/"+mm4_mon+"06", out_dir+"/"+mm4_mon+"f")
		merge_mm4_optimized(out_dir+"/"+mm4_mon+"f", out_dir+"/"+mm4_mon+"07", out_dir+"/"+mm4_mon)

		#att sprite
		convert_sprite_3to4(in_dir+"/"+mm3_mon, out_dir+"/"+mm4_att, False, out_width=sprite_width, out_height_off=sprite_height_off)

		mm4_mon_hash = hash_filename(mm4_mon)
		mm4_att_hash = hash_filename(mm4_att)
		copy_file(out_dir+"/"+mm4_mon, out_dir+"/"+mm4_mon_hash)
		copy_file(out_dir+"/"+mm4_att, out_dir+"/"+mm4_att_hash)


MM3TO4_OUTDOOR_TERRAIN = [
	# WAL files
	# ('swmtree.vga','DEDLTREE.WAL'),
	('dtree.vga','DTREE.WAL'),
	('lavamtn.vga','LAVAMNT.WAL'),
	('ltree.vga','LTREE.WAL'),
	('mount.vga','MOUNT.WAL'),
	('palms.vga','PALM.WAL'),
	('snomtn.vga','SNOMNT.WAL'),
	('snotree.vga','SNOTREE.WAL'),
]

MM3TO4_OUTDOOR_SURFACE = [
	# SRF files
	# ('','CLOUD.SRF'),
	('desert.vga','DESERT.SRF'),
	# ('dirt.vga','DIRT.SRF'),#need to fix sprite
	('desert.vga','DIRT.SRF'),
	# ('water.vga','DWATER.SRF'),
	('grass.vga','GRASS.SRF'),
	('lava.vga','LAVA.SRF'),
	('road.vga','ROAD.SRF'),
	# ('','SCORTCH.SRF'),
	# ('','SKY.SRF'),
	('snow.vga','SNOW.SRF'),
	# ('','SPACE.SRF'),
	('swamp.vga','SWAMP.SRF'),
	# ('','TFLR.SRF'),
	# ('water.vga','WATER.SRF'),
]

# MM3TO4_OUTDOOR_TERRAIN = []
# MM3TO4_OUTDOOR_SURFACE = []


def convert_environments(in_dir, out_dir):
	print("convert_environments")

	for pairmap in MM3TO4_OUTDOOR_TERRAIN:
		mm3_terrain = pairmap[0]
		mm4_terrain = pairmap[1]
		convert_sprite_3to4(in_dir+"/"+mm3_terrain, out_dir+"/"+mm4_terrain)
		mm4_hash = hash_filename(mm4_terrain)
		copy_file(out_dir+"/"+mm4_terrain, out_dir+"/"+mm4_hash)


	#sky (day)
	# so this damn sprite is giving me trouble in wox/darkside... it seems due to the filesize?
	# larger than ~7k causes other sprites such as base ground (water) not to load. 
	# the image itself is clouds and relatively noisy, so its not well compressed.
	# there are a lot of color "pairs" though...

	mm3_sky_sky = "day.vga"
	mm4_sky_sky = "SKY.SKY"
	convert_sprite_3to4(in_dir+"/"+mm3_sky_sky, out_dir+"/"+mm4_sky_sky+"a", y_end=17)
	convert_sprite_3to4(in_dir+"/"+mm3_sky_sky, out_dir+"/"+mm4_sky_sky+"b", y_start=17, scanline=True)
	# now to put the two frames together into one file...
	merge_mm4_sprites(out_dir+"/"+mm4_sky_sky+"a", out_dir+"/"+mm4_sky_sky+"b", out_dir+"/"+mm4_sky_sky)
	mm4_hash = hash_filename(mm4_sky_sky)
	copy_file(out_dir+"/"+mm4_sky_sky, out_dir+"/"+mm4_hash)

	
	#sky (night)
	mm3_night_sky = "night.vga"
	mm4_night_sky = "NIGHT.SKY"
	convert_sprite_3to4(in_dir+"/"+mm3_night_sky, out_dir+"/"+mm4_night_sky+"a", y_end=17)
	convert_sprite_3to4(in_dir+"/"+mm3_night_sky, out_dir+"/"+mm4_night_sky+"b", y_start=17)
	# now to put the two frames together into one file...
	merge_mm4_sprites(out_dir+"/"+mm4_night_sky+"a", out_dir+"/"+mm4_night_sky+"b", out_dir+"/"+mm4_night_sky)
	mm4_hash = hash_filename(mm4_night_sky)
	copy_file(out_dir+"/"+mm4_night_sky, out_dir+"/"+mm4_hash)
	

	mm3_cave_sky = "cav.sky"
	mm4_cave_sky = "CAVE.SKY"
	# mm3_castle_sky = "cas.sky"
	# mm4_castle_sky = "CSTL.SKY"
	mm3_dung_sky = "dun.sky"
	mm4_dung_sky = "DUNG.SKY"
	mm3_scifi_sky = "sci.sky"
	mm4_scifi_sky = "SCFI.SKY"

	convert_sprite_3to4(in_dir+"/"+mm3_cave_sky, out_dir+"/"+mm4_cave_sky+"a", y_end=17)
	convert_sprite_3to4(in_dir+"/"+mm3_cave_sky, out_dir+"/"+mm4_cave_sky+"b", y_start=17)
	merge_mm4_sprites(out_dir+"/"+mm4_cave_sky+"a", out_dir+"/"+mm4_cave_sky+"b", out_dir+"/"+mm4_cave_sky)
	mm4_hash = hash_filename(mm4_cave_sky)
	copy_file(out_dir+"/"+mm4_cave_sky, out_dir+"/"+mm4_hash)

	convert_sprite_3to4(in_dir+"/"+mm3_dung_sky, out_dir+"/"+mm4_dung_sky+"a", y_end=17)
	convert_sprite_3to4(in_dir+"/"+mm3_dung_sky, out_dir+"/"+mm4_dung_sky+"b", y_start=17)
	merge_mm4_sprites(out_dir+"/"+mm4_dung_sky+"a", out_dir+"/"+mm4_dung_sky+"b", out_dir+"/"+mm4_dung_sky)
	mm4_hash = hash_filename(mm4_dung_sky)
	copy_file(out_dir+"/"+mm4_dung_sky, out_dir+"/"+mm4_hash)

	convert_sprite_3to4(in_dir+"/"+mm3_scifi_sky, out_dir+"/"+mm4_scifi_sky+"a", y_end=17)
	convert_sprite_3to4(in_dir+"/"+mm3_scifi_sky, out_dir+"/"+mm4_scifi_sky+"b", y_start=17)
	merge_mm4_sprites(out_dir+"/"+mm4_scifi_sky+"a", out_dir+"/"+mm4_scifi_sky+"b", out_dir+"/"+mm4_scifi_sky)
	mm4_hash = hash_filename(mm4_scifi_sky)
	copy_file(out_dir+"/"+mm4_scifi_sky, out_dir+"/"+mm4_hash)


	#water
	mm3_water = "water.vga"
	mm4_water_out = "WATER.OUT"
	convert_sprite_3to4(in_dir+"/"+mm3_water, out_dir+"/"+mm4_water_out)
	mm4_hash = hash_filename(mm4_water_out)
	copy_file(out_dir+"/"+mm4_water_out, out_dir+"/"+mm4_hash)



	#GROUND/WALLS!

	#"twnwl1.vga","twnwl2.vga","twnwl3.vga","twnwl4.vga"

	#env sets:
	#twnwl, cavwl, dunwl, caswl, sciwl, 

	#mm4:
	# Cave (CAVE)
	# Castle (CSTL)
	# Dungeon (DUNG)
	# Sci-Fi, used for example in the crashed escape pods (SCFI)
	# Town (TOWN)
	# Tower (TOWR)

	#side walls
	# mm4_town_swl = "STOWN.SWL" #48 frames
	# mm4_cave_swl = "SCAVE.SWL"

	#remap, then merge back together...

	mm3_wall_1 = "1.vga" 
	mm3_wall_2 = "2.vga"
	mm3_wall_3 = "3.vga"
	mm3_wall_4 = "4.vga"


	mm4_gnd_map = [
		(mm3_wall_4, 29),
	]

	mm4_gnd_files = [
		(".GND", mm4_gnd_map),
	]

	remap_sprites(mm4_gnd_files, in_dir, out_dir, mm3_prefix="twnwl", mm4_prefix="TOWN")
	remap_sprites(mm4_gnd_files, in_dir, out_dir, mm3_prefix="cavwl", mm4_prefix="CAVE")
	remap_sprites(mm4_gnd_files, in_dir, out_dir, mm3_prefix="dunwl", mm4_prefix="DUNG")
	remap_sprites(mm4_gnd_files, in_dir, out_dir, mm3_prefix="caswl", mm4_prefix="CSTL")
	remap_sprites(mm4_gnd_files, in_dir, out_dir, mm3_prefix="sciwl", mm4_prefix="SCFI")


	# SCAVE.SWL

	mm4_swl_map = [
		#src_file; src_frame; y_end
		(mm3_wall_1, 4),#0
		(mm3_wall_1, 5),#1
		(mm3_wall_2, 4),#2
		(mm3_wall_2, 5),#3
		(mm3_wall_3, 4),#4
		(mm3_wall_3, 5),#5
		(mm3_wall_3, 6),#6
		(mm3_wall_3, 6),#7
		(mm3_wall_4, 4),#8
		(mm3_wall_4, 5),#9
		(mm3_wall_4, 8),#10
		(mm3_wall_4, 8),#11
		(mm3_wall_4, 10),#12
		(mm3_wall_4, 10),#13
		(mm3_wall_4, 12),#14
		(mm3_wall_4, 12),#15
		(mm3_wall_4, 6),#16
		(mm3_wall_4, 7),#17
		(mm3_wall_4, 9),#18
		(mm3_wall_4, 9),#19
		(mm3_wall_4, 11),#20
		(mm3_wall_4, 11),#21
		(mm3_wall_4, 13),#22
		(mm3_wall_4, 13),#23
		(mm3_wall_1, 11),#24
		(mm3_wall_1, 12),#25
		(mm3_wall_2, 11),#26
		(mm3_wall_2, 12),#27
		(mm3_wall_3, 12),#28
		(mm3_wall_3, 13),#29
		(mm3_wall_3, 6),#30
		(mm3_wall_3, 6),#31
		(mm3_wall_4, 19),#32
		(mm3_wall_4, 20),#33
		(mm3_wall_4, 23),#34
		(mm3_wall_4, 23),#35
		(mm3_wall_4, 10),#36
		(mm3_wall_4, 10),#37
		(mm3_wall_4, 12),#38
		(mm3_wall_4, 12),#39
		(mm3_wall_4, 21),#40	
		(mm3_wall_4, 22),#41
		(mm3_wall_4, 24),#42
		(mm3_wall_4, 24),#43
		(mm3_wall_4, 26),#44
		(mm3_wall_4, 26),#45
		(mm3_wall_4, 28),#46
		(mm3_wall_4, 28),#47
	]

	mm4_swl_files = [
		(".SWL", mm4_swl_map),
	]

	remap_sprites(mm4_swl_files, in_dir, out_dir, mm3_prefix="twnwl", mm4_prefix="STOWN")
	remap_sprites(mm4_swl_files, in_dir, out_dir, mm3_prefix="cavwl", mm4_prefix="SCAVE")
	remap_sprites(mm4_swl_files, in_dir, out_dir, mm3_prefix="dunwl", mm4_prefix="DUNG")
	remap_sprites(mm4_swl_files, in_dir, out_dir, mm3_prefix="caswl", mm4_prefix="CSTL")
	remap_sprites(mm4_swl_files, in_dir, out_dir, mm3_prefix="sciwl", mm4_prefix="SCFI")

	#front walls
	#4 distance levels...
	# mm4_town_fwl_1 = "FTOWN1.FWL"#8 frames
	# mm4_town_fwl_2 = "FTOWN2.FWL"#11 frames
	# mm4_town_fwl_3 = "FTOWN3.FWL"#34 frames
	# mm4_town_fwl_4 = "FTOWN4.FWL"#17 frames

	mm4_fwl_1_map = [
		#src_file; src_frame; y_end
		(mm3_wall_1, 0),#0
		(mm3_wall_1, 1),#1
		(mm3_wall_1, 2),#2
		(mm3_wall_1, 3),#3
		(mm3_wall_1, 2),#4
		(mm3_wall_1, 3),#5
		(mm3_wall_1, 0),#6
		(mm3_wall_4, 29, 4),#7
	]

	mm4_fwl_2_map = [
		#src_file; src_frame; y_end
		(mm3_wall_1, 6),#0
		(mm3_wall_1, 7),#1
		(mm3_wall_1, 8),#2
		(mm3_wall_1, 9),#3
		(mm3_wall_1, 0),#4
		(mm3_wall_1, 0),#5
		(mm3_wall_1, 0),#6
		(mm3_wall_1, 7),#7
		(mm3_wall_1, 8),#8
		(mm3_wall_1, 10),#9
		(mm3_wall_1, 7),#10
	]

	mm4_fwl_3_map = [
		#src_file; src_frame; y_end
		(mm3_wall_2, 0),#0
		(mm3_wall_2, 0),#1
		(mm3_wall_2, 1),#2
		(mm3_wall_2, 2),#3
		(mm3_wall_2, 3),#4
		(mm3_wall_2, 2),#5
		(mm3_wall_2, 0),#6
		(mm3_wall_2, 6),#7
		(mm3_wall_2, 7),#8
		(mm3_wall_2, 8),#9
		(mm3_wall_2, 9),#10
		(mm3_wall_2, 0),#11
		(mm3_wall_2, 0),#12
		(mm3_wall_2, 0),#13
		(mm3_wall_2, 7),#14
		(mm3_wall_2, 8),#15
		(mm3_wall_2, 10),#16
		(mm3_wall_3, 0),#17
		(mm3_wall_3, 0),#18
		(mm3_wall_3, 1),#19
		(mm3_wall_3, 2),#20
		(mm3_wall_3, 3),#21
		(mm3_wall_3, 2),#22
		(mm3_wall_3, 0),#23
		(mm3_wall_3, 7),#24
		(mm3_wall_3, 8),#25
		(mm3_wall_3, 9),#26
		(mm3_wall_3, 10),#27
		(mm3_wall_3, 0),#28
		(mm3_wall_3, 0),#29
		(mm3_wall_3, 0),#30
		(mm3_wall_3, 8),#31
		(mm3_wall_3, 9),#32
		(mm3_wall_3, 11),#33
	]

	mm4_fwl_4_map = [
		#src_file; src_frame; y_end
		(mm3_wall_4, 0),#0
		(mm3_wall_4, 0),#1
		(mm3_wall_4, 1),#2
		(mm3_wall_4, 2),#3
		(mm3_wall_4, 3),#4
		(mm3_wall_4, 2),#5
		(mm3_wall_4, 0),#6
		(mm3_wall_4, 14),#7
		(mm3_wall_4, 15),#8
		(mm3_wall_4, 16),#9
		(mm3_wall_4, 17),#10
		(mm3_wall_4, 0),#11
		(mm3_wall_4, 0),#12
		(mm3_wall_4, 0),#13
		(mm3_wall_4, 15),#14
		(mm3_wall_4, 16),#15
		(mm3_wall_4, 18),#16
	]

	mm4_fwl_files = [
		("1.FWL", mm4_fwl_1_map),
		("2.FWL", mm4_fwl_2_map),
		("3.FWL", mm4_fwl_3_map),
		("4.FWL", mm4_fwl_4_map),
	]


	remap_sprites(mm4_fwl_files, in_dir, out_dir, mm3_prefix="twnwl", mm4_prefix="FTOWN")
	remap_sprites(mm4_fwl_files, in_dir, out_dir, mm3_prefix="cavwl", mm4_prefix="FCAVE")
	remap_sprites(mm4_fwl_files, in_dir, out_dir, mm3_prefix="dunwl", mm4_prefix="DUNG")
	remap_sprites(mm4_fwl_files, in_dir, out_dir, mm3_prefix="caswl", mm4_prefix="CSTL")
	remap_sprites(mm4_fwl_files, in_dir, out_dir, mm3_prefix="sciwl", mm4_prefix="SCFI")
	



	for pairmap in MM3TO4_OUTDOOR_SURFACE:
		mm3_surface = pairmap[0]
		mm4_surface = pairmap[1]

		convert_sprite_3to4(in_dir+"/"+mm3_surface, out_dir+"/"+mm4_surface+"00", frame_number=1)
		convert_sprite_3to4(in_dir+"/"+mm3_surface, out_dir+"/"+mm4_surface+"01", frame_number=0)
		convert_sprite_3to4(in_dir+"/"+mm3_surface, out_dir+"/"+mm4_surface+"02", frame_number=2)

		convert_sprite_3to4(in_dir+"/"+mm3_surface, out_dir+"/"+mm4_surface+"03", frame_number=4)
		convert_sprite_3to4(in_dir+"/"+mm3_surface, out_dir+"/"+mm4_surface+"04", frame_number=3)
		convert_sprite_3to4(in_dir+"/"+mm3_surface, out_dir+"/"+mm4_surface+"05", frame_number=5)

		convert_sprite_3to4(in_dir+"/"+mm3_surface, out_dir+"/"+mm4_surface+"06", frame_number=8)
		convert_sprite_3to4(in_dir+"/"+mm3_surface, out_dir+"/"+mm4_surface+"07", frame_number=7)
		convert_sprite_3to4(in_dir+"/"+mm3_surface, out_dir+"/"+mm4_surface+"08", frame_number=6)
		convert_sprite_3to4(in_dir+"/"+mm3_surface, out_dir+"/"+mm4_surface+"09", frame_number=9)
		convert_sprite_3to4(in_dir+"/"+mm3_surface, out_dir+"/"+mm4_surface+"10", frame_number=10)

		convert_sprite_3to4(in_dir+"/"+mm3_surface, out_dir+"/"+mm4_surface+"11", frame_number=21)
		convert_sprite_3to4(in_dir+"/"+mm3_surface, out_dir+"/"+mm4_surface+"12", frame_number=13)
		convert_sprite_3to4(in_dir+"/"+mm3_surface, out_dir+"/"+mm4_surface+"13", frame_number=12)
		convert_sprite_3to4(in_dir+"/"+mm3_surface, out_dir+"/"+mm4_surface+"14", frame_number=11)
		convert_sprite_3to4(in_dir+"/"+mm3_surface, out_dir+"/"+mm4_surface+"15", frame_number=14)
		convert_sprite_3to4(in_dir+"/"+mm3_surface, out_dir+"/"+mm4_surface+"16", frame_number=15)
		convert_sprite_3to4(in_dir+"/"+mm3_surface, out_dir+"/"+mm4_surface+"17", frame_number=24)

		convert_sprite_3to4(in_dir+"/"+mm3_surface, out_dir+"/"+mm4_surface+"18", frame_number=20)
		convert_sprite_3to4(in_dir+"/"+mm3_surface, out_dir+"/"+mm4_surface+"19", frame_number=18)
		convert_sprite_3to4(in_dir+"/"+mm3_surface, out_dir+"/"+mm4_surface+"20", frame_number=17)
		convert_sprite_3to4(in_dir+"/"+mm3_surface, out_dir+"/"+mm4_surface+"21", frame_number=16)
		convert_sprite_3to4(in_dir+"/"+mm3_surface, out_dir+"/"+mm4_surface+"22", frame_number=19)
		convert_sprite_3to4(in_dir+"/"+mm3_surface, out_dir+"/"+mm4_surface+"23", frame_number=22)
		convert_sprite_3to4(in_dir+"/"+mm3_surface, out_dir+"/"+mm4_surface+"24", frame_number=23)

		merge_mm4_optimized(out_dir+"/"+mm4_surface+"00", out_dir+"/"+mm4_surface+"01", out_dir+"/"+mm4_surface+"a")
		merge_mm4_optimized(out_dir+"/"+mm4_surface+"a", out_dir+"/"+mm4_surface+"02", out_dir+"/"+mm4_surface+"b")
		merge_mm4_optimized(out_dir+"/"+mm4_surface+"b", out_dir+"/"+mm4_surface+"03", out_dir+"/"+mm4_surface+"c")
		merge_mm4_optimized(out_dir+"/"+mm4_surface+"c", out_dir+"/"+mm4_surface+"04", out_dir+"/"+mm4_surface+"d")
		merge_mm4_optimized(out_dir+"/"+mm4_surface+"d", out_dir+"/"+mm4_surface+"05", out_dir+"/"+mm4_surface+"e")
		merge_mm4_optimized(out_dir+"/"+mm4_surface+"e", out_dir+"/"+mm4_surface+"06", out_dir+"/"+mm4_surface+"f")
		merge_mm4_optimized(out_dir+"/"+mm4_surface+"f", out_dir+"/"+mm4_surface+"07", out_dir+"/"+mm4_surface+"g")
		merge_mm4_optimized(out_dir+"/"+mm4_surface+"g", out_dir+"/"+mm4_surface+"08", out_dir+"/"+mm4_surface+"h")
		merge_mm4_optimized(out_dir+"/"+mm4_surface+"h", out_dir+"/"+mm4_surface+"09", out_dir+"/"+mm4_surface+"i")
		merge_mm4_optimized(out_dir+"/"+mm4_surface+"i", out_dir+"/"+mm4_surface+"10", out_dir+"/"+mm4_surface+"j")
		merge_mm4_optimized(out_dir+"/"+mm4_surface+"j", out_dir+"/"+mm4_surface+"11", out_dir+"/"+mm4_surface+"k")
		merge_mm4_optimized(out_dir+"/"+mm4_surface+"k", out_dir+"/"+mm4_surface+"12", out_dir+"/"+mm4_surface+"l")
		merge_mm4_optimized(out_dir+"/"+mm4_surface+"l", out_dir+"/"+mm4_surface+"13", out_dir+"/"+mm4_surface+"m")
		merge_mm4_optimized(out_dir+"/"+mm4_surface+"m", out_dir+"/"+mm4_surface+"14", out_dir+"/"+mm4_surface+"n")
		merge_mm4_optimized(out_dir+"/"+mm4_surface+"n", out_dir+"/"+mm4_surface+"15", out_dir+"/"+mm4_surface+"o")
		merge_mm4_optimized(out_dir+"/"+mm4_surface+"o", out_dir+"/"+mm4_surface+"16", out_dir+"/"+mm4_surface+"p")
		merge_mm4_optimized(out_dir+"/"+mm4_surface+"p", out_dir+"/"+mm4_surface+"17", out_dir+"/"+mm4_surface+"q")
		merge_mm4_optimized(out_dir+"/"+mm4_surface+"q", out_dir+"/"+mm4_surface+"18", out_dir+"/"+mm4_surface+"r")
		merge_mm4_optimized(out_dir+"/"+mm4_surface+"r", out_dir+"/"+mm4_surface+"19", out_dir+"/"+mm4_surface+"s")
		merge_mm4_optimized(out_dir+"/"+mm4_surface+"s", out_dir+"/"+mm4_surface+"20", out_dir+"/"+mm4_surface+"t")
		merge_mm4_optimized(out_dir+"/"+mm4_surface+"t", out_dir+"/"+mm4_surface+"21", out_dir+"/"+mm4_surface+"u")
		merge_mm4_optimized(out_dir+"/"+mm4_surface+"u", out_dir+"/"+mm4_surface+"22", out_dir+"/"+mm4_surface+"v")
		merge_mm4_optimized(out_dir+"/"+mm4_surface+"v", out_dir+"/"+mm4_surface+"23", out_dir+"/"+mm4_surface+"w")
		merge_mm4_optimized(out_dir+"/"+mm4_surface+"w", out_dir+"/"+mm4_surface+"24", out_dir+"/"+mm4_surface)

		mm4_hash = hash_filename(mm4_surface)
		copy_file(out_dir+"/"+mm4_surface, out_dir+"/"+mm4_hash)



def convert_meta_data(in_dir, out_dir):
	print("convert_meta_data")
	#MM3:
	# award.bin
	# copy.bin
	# corak.bin
	# jester.bin
	# quest.bin
	# spldesc.bin
	# tavern.bin
	#MM4:
	# AWARD.BIN
	# NOTES.BIN
	# QNOTES.BIN
	# QUEST.BIN
	# SPECIAL.BIN
	# SPLDESC.BIN
	# TAVERN.BIN
	# VIEWTEXT.BIN


	mm3_bin = "award.bin"
	mm4_bin = "AWARD.BIN"
	mm4_hash = hash_filename(mm4_bin)
	copy_file(in_dir+"/"+mm3_bin, out_dir+"/"+mm4_bin)
	copy_file(out_dir+"/"+mm4_bin, out_dir+"/"+mm4_hash)

	mm3_bin = "tavern.bin"
	mm4_bin = "TAVERN.BIN"
	mm4_hash = hash_filename(mm4_bin)
	copy_file(in_dir+"/"+mm3_bin, out_dir+"/"+mm4_bin)
	copy_file(out_dir+"/"+mm4_bin, out_dir+"/"+mm4_hash)

	mm3_bin = "quest.bin"
	mm4_bin = "QUEST.BIN"
	mm4_hash = hash_filename(mm4_bin)
	copy_file(in_dir+"/"+mm3_bin, out_dir+"/"+mm4_bin)
	copy_file(out_dir+"/"+mm4_bin, out_dir+"/"+mm4_hash)




	mm4_mon = "DARK.MON"
	mm4_hash = hash_filename(mm4_mon)
	parse_monsters(in_dir, out_dir+"/"+mm4_hash)

	#mirror text
	#XEENMIRR.TXT / DARKMIRR.TXT
	#https://xeen.fandom.com/wiki/Mirror_File_Format
	mirror_text = "DARKMIRR.TXT"
	mm4_hash = hash_filename(mirror_text)
	mirror_text_data = bytearray()
	#32 bytes per entry
		#28 bytes - name
		#4 bytes - 
			#index (i+25); x; y; facing dir
	for i, name in enumerate(MM3_MAZE_NAMES):
		mirror_name_bytes = bytearray(28)
		mirror_name_enc = name.encode('utf-8')
		end_idx = len(mirror_name_enc)
		mirror_name_bytes[0:end_idx] = mirror_name_enc
		mirror_name_bytes.append(i+1)#mapid
		mirror_name_bytes.append(5)#x
		mirror_name_bytes.append(6)#y
		mirror_name_bytes.append(0)#dir
		mirror_text_data.extend(mirror_name_bytes)

	with open(out_dir+"/"+mirror_text, 'wb') as dest:
		dest.write(mirror_text_data)
	copy_file(out_dir+"/"+mirror_text, out_dir+"/"+mm4_hash)

	#TODO stuff in exe/dat files:
	#items
	#stats
	#MAE.XEN, SPELLS.XEN




MM3_FACE_SPRITE_NAMES = [
	'human1.fac','human2.fac','human3.fac','human4.fac',
	'dwarf1.fac','dwarf2.fac','dwarf3.fac','dwarf4.fac',
	'elf1.fac','elf2.fac','elf3.fac','elf4.fac',
	'gnome1.fac','gnome2.fac','gnome3.fac','gnome4.fac',
	'horc1.fac','horc2.fac','horc3.fac','horc4.fac',
	'hire0.fac','hire1.fac','hire2.fac','hire3.fac',
	'hire4.fac','hire5.fac','hire6.fac','hire7.fac','hire8.fac','hire9.fac']

MM3_ICONS = [
	'bank.icn','bank2.icn','buy.icn','cast.icn','charpow.icn','combat.icn','confirm.icn',
	'confirm2.icn','cpanel.icn','create.icn','detctmon.icn','detect.icn','duplicat.icn',
	'element.icn','equip.icn','esc.icn','global.icn','hpbars.icn','inn.icn','items.icn',
	'lloyds.icn','main.icn','mouse.icn','pow0.icn','pow10.icn','pow11.icn','pow12.icn',
	'pow13.icn','pow14.icn','pow2.icn','pow3.icn','pow4.icn','pow5.icn','pow7.icn',
	'pow8.icn','pow9.icn','protect.icn','restore.icn','scroll.icn','sell.icn','start.icn',
	'train.icn','view.icn'
]

def convert_2d_graphics(in_dir, out_dir):
	print("convert_2d_graphics")
	#character portraits (24)
	#in: human1.fac (32x32)
	#out: CHAR01.FAC (32x32)
	for i in range(24):
		mm3_fac = MM3_FACE_SPRITE_NAMES[i]
		mm4_fac = f"CHAR{(i+1):02}.FAC"
		mm4_hash = hash_filename(mm4_fac)
		convert_sprite_3to4(in_dir+"/"+mm3_fac, out_dir+"/"+mm4_fac)
		copy_file(out_dir+"/"+mm4_fac, out_dir+"/"+mm4_hash)

	#npc faces (44)
	for i in range(30):
		mm3_fac = f"eface{(i+1):02}.out"
		mm4_fac = f"FACE{(i+1):02}.FAC"
		mm4_hash = hash_filename(mm4_fac)
		convert_sprite_3to4(in_dir+"/"+mm3_fac, out_dir+"/"+mm4_fac)
		copy_file(out_dir+"/"+mm4_fac, out_dir+"/"+mm4_hash)

	#icons, mostly 1:1
	for i in range(len(MM3_ICONS)):
		mm3_icn = MM3_ICONS[i]
		mm4_icon = mm3_icn.upper()
		mm4_hash = hash_filename(mm4_icon)

		mm3_frame_ct = inspect_sprite(in_dir+"/"+mm3_icn, True)
		mm4_frame_ct = inspect_sprite("ext_cld"+"/"+mm4_hash, True)

		if mm3_frame_ct == mm4_frame_ct or not mm4_frame_ct:
			convert_sprite_3to4(in_dir+"/"+mm3_icn, out_dir+"/"+mm4_icon)
			copy_file(out_dir+"/"+mm4_icon, out_dir+"/"+mm4_hash)
		else:
			print(f"skipping icon {mm4_icon} ({mm4_frame_ct} frames)")





def convert_media(in_dir, out_dir):
	print("convert_media")
	#main screen background/logo image
	mm3_logo = "logy5.raw" #CGA colors???
	mm4_logo = "INTRO.RAW"
	mm4_hash = hash_filename(mm4_logo)
	copy_file(in_dir+"/"+mm3_logo, out_dir+"/"+mm4_logo)
	copy_file(out_dir+"/"+mm4_logo, out_dir+"/"+mm4_hash)




def convert_all(in_dir, out_dir):
	print("here we gooo!")
	convert_maps(in_dir, out_dir)
	convert_sprites(in_dir, out_dir)
	convert_environments(in_dir, out_dir)
	convert_meta_data(in_dir, out_dir)
	convert_2d_graphics(in_dir, out_dir)
	convert_media(in_dir, out_dir)



if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Convert MM3 CC file contents to MM4 formats")
	parser.add_argument("indir", help="Directory containing contents of MM3 CC file")
	parser.add_argument("outdir", help="Directory to output converted file in MM4 formats")
	args = parser.parse_args()

	convert_all(args.indir, args.outdir)
