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
	outputs:
	- *.fac
		CHAR01.FAC (5 frames) 24 sprites
		FACE01.FAC (4 frames) 44 sprites

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

			base_id = "DARK" #XEEN
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
	'POOLB','POOLY',]

MM3_MON_SPRITE_NAMES = [
	'bat','bublman','goblin','orc','skel','head','wasp','rat',
	'shriek','zombie','candle','dwarf','ninja','mantis','hamr','bugeye',
	'repthed','spider','sprite','beetle','cobra','scorpia','flytrap','jester',
	'minidrgn','plasmoid','hand','ghoul','gatekepr','phantom','pirana','ranger',
	'thief','treeglum','witch','robo2','dthlocus','archer','ballface','barbaran',
	'cleric','firelzrd','firemon','gargoyle','ghost','lizard','sonicnja','beholder',
	'cris','paladin','pegasus','reaper','sorc','lich','shield','troll',
	# 'demon','dino','robo','blknight','martface','mummy','powsorc','cataplr',
	'undragon','cyclop','devil','grndrgn','wizard','worm','vampire','werewolf',
	'termnatr','hydra','roc','kudo','medusa','minotaur','octobest','draglord',]


def convert_sprites(in_dir, out_dir):
	print("convert_sprites")

	# MM3 palette
	hex_pal = "0000003F 3F3F3C3C 3C3A3A3A 38383835 35353333 33313131 2F2F2F2C 2C2C2A2A 2A282828 25252523 23232121 211F1F1F 1D1D1D1B 1B1B1919 19171717 15151513 13131111 110F0F0F 0D0D0D0B 0B0B0909 09070707 05050503 03030101 01000000 3F3A3A3E 35353D30 303C2C2C 3B28283A 2323391F 1F391B1B 38171737 13133610 10350C0C 34080833 05053202 02320000 2E00002A 00002600 00210000 1D000019 00001500 00110000 0D00003F 1D003719 00301600 28120021 0F00190B 00120800 3F3F363F 3F2E3E3F 263E3F1E 3E3F163D 3F0E3D3F 063B3D00 3B3B0038 37003533 00322E00 2F2A002C 26002922 00261F00 221A001E 16001A12 00160F00 120B000E 08000A05 00060300 363F1631 3B112D38 0D29340A 25310621 2D031D2A 011A2700 15240013 2100121F 00111D00 101B000E 19000D17 000C1500 0B13002F 3E2F273C 26203A1F 17381710 37100B35 0A0A3209 082F0807 2D07062A 06052704 04240403 2203021F 02021C02 011A0101 17010114 00001100 000F0000 0C000009 00000700 3C3C3F38 383F3333 3F2F2F3F 2B2C3F27 283F2323 3F1F203F 1B1C3F17 183F1314 3F0F103F 0B0C3F07 083F0304 3F00013F 00003F00 003B0000 37000033 00002F00 002B0000 27000024 00002000 001C0000 18000014 00001000 000C0000 08000005 3C363F39 2E3F3627 3F341F3F 32173F2F 103F2D08 3F2A003F 26003920 00321B00 2B150023 0F001B0A 00140600 0C020005 333F3F2D 3B3B2738 38223535 1D323219 2F2F142B 2B112828 0D242409 1F1F071B 1B041717 02131301 0F0F000B 0B000707 3A3C3E36 3A3D3137 3D2D353D 29333C25 313C2130 3C1D2E3B 192C3B15 2B3B1129 3A0D283A 0A263A06 25390224 39012136 011F3300 1D30001B 2D00192B 00172800 15250014 2200121F 00101C00 0E18000C 15000A12 00080F00 060C0005 09000306 3F3A373F 37333F35 303F332C 3F31293F 2F253F2D 223F2B1F 3F291B3F 27183C25 173A2416 38221536 21143420 14321F13 2F1D112C 1B10291A 0E26180D 23160C20 150A1D13 091A1108 170F0714 0D06110C 050E0A03 0B080309 06020604 013F3F3F"
	raw_palette = bytes.fromhex(hex_pal)
	pal_name = "MM4" # MM4, MM4E, DARK
	with open(out_dir+"/"+f"{pal_name}.PAL", "wb") as f:
		f.write(raw_palette)
	copy_file(out_dir+"/"+f"{pal_name}.PAL", out_dir+"/"+hash_filename(f"{pal_name}.PAL"))

	#object sprites
	for i in range(len(MM3_OBJ_SPRITE_NAMES)):
		mm3_obj = MM3_OBJ_SPRITE_NAMES[i]+".pic"
		mm4_obj = f"{(i):03}.OBJ"
		mm4_hash = hash_filename(mm4_obj)

		print(f"converting obj sprite {mm3_obj} to {mm4_obj} ({mm4_hash})")
		sprite_width = 250
		convert_sprite_3to4(in_dir+"/"+mm3_obj, out_dir+"/"+mm4_obj, False, out_width=sprite_width)
		# hash mm4_obj to .ccx name for packing
		copy_file(out_dir+"/"+mm4_obj, out_dir+"/"+mm4_hash)

	#TODO generate https://xeen.fandom.com/wiki/CLOUDS.DAT_File
	# sprite_dat_mm4 = f"DARK.DAT"
	# mm4_hash = hash_filename(sprite_dat_mm4)
	# sprite_dat_data = bytearray(1452)
	# with open(out_dir+"/"+sprite_dat_mm4, 'wb') as dest:
	# 	dest.write(sprite_dat_data)
	# copy_file(out_dir+"/"+sprite_dat_mm4, out_dir+"/"+mm4_hash)

	#monster sprites
	for i in range(len(MM3_MON_SPRITE_NAMES)):
		mm3_mon = MM3_MON_SPRITE_NAMES[i]+".mon"
		mm4_mon = f"{(i):03}.MON"
		mm4_att = f"{(i):03}.ATT"
		mm4_mon_hash = hash_filename(mm4_mon)
		mm4_att_hash = hash_filename(mm4_att)

		print(f"converting mon sprite {mm3_mon} to {mm4_mon} and {mm4_att}")
		sprite_width = 250
		convert_sprite_3to4(in_dir+"/"+mm3_mon, out_dir+"/"+mm4_mon+"00", False, out_width=sprite_width, frame_number=0)
		convert_sprite_3to4(in_dir+"/"+mm3_mon, out_dir+"/"+mm4_mon+"01", False, out_width=sprite_width, frame_number=1)
		convert_sprite_3to4(in_dir+"/"+mm3_mon, out_dir+"/"+mm4_mon+"02", False, out_width=sprite_width, frame_number=2)
		convert_sprite_3to4(in_dir+"/"+mm3_mon, out_dir+"/"+mm4_mon+"03", False, out_width=sprite_width, frame_number=3)
		convert_sprite_3to4(in_dir+"/"+mm3_mon, out_dir+"/"+mm4_mon+"04", False, out_width=sprite_width, frame_number=0)
		convert_sprite_3to4(in_dir+"/"+mm3_mon, out_dir+"/"+mm4_mon+"05", False, out_width=sprite_width, frame_number=1)
		convert_sprite_3to4(in_dir+"/"+mm3_mon, out_dir+"/"+mm4_mon+"06", False, out_width=sprite_width, frame_number=2)
		convert_sprite_3to4(in_dir+"/"+mm3_mon, out_dir+"/"+mm4_mon+"07", False, out_width=sprite_width, frame_number=3)

		merge_mm4_optimized(out_dir+"/"+mm4_mon+"00", out_dir+"/"+mm4_mon+"01", out_dir+"/"+mm4_mon+"a")
		merge_mm4_optimized(out_dir+"/"+mm4_mon+"a", out_dir+"/"+mm4_mon+"02", out_dir+"/"+mm4_mon+"b")
		merge_mm4_optimized(out_dir+"/"+mm4_mon+"b", out_dir+"/"+mm4_mon+"03", out_dir+"/"+mm4_mon+"c")
		merge_mm4_optimized(out_dir+"/"+mm4_mon+"c", out_dir+"/"+mm4_mon+"04", out_dir+"/"+mm4_mon+"d")
		merge_mm4_optimized(out_dir+"/"+mm4_mon+"d", out_dir+"/"+mm4_mon+"05", out_dir+"/"+mm4_mon+"e")
		merge_mm4_optimized(out_dir+"/"+mm4_mon+"e", out_dir+"/"+mm4_mon+"06", out_dir+"/"+mm4_mon+"f")
		merge_mm4_optimized(out_dir+"/"+mm4_mon+"f", out_dir+"/"+mm4_mon+"07", out_dir+"/"+mm4_mon)

		# convert_sprite_3to4(in_dir+"/"+mm3_mon, out_dir+"/"+mm4_att, False, out_width=sprite_width)
		copy_file(out_dir+"/"+mm4_mon, out_dir+"/"+mm4_mon_hash)
		# copy_file(out_dir+"/"+mm4_att, out_dir+"/"+mm4_att_hash)


def convert_environments(in_dir, out_dir):
	print("convert_environments")

	#ground
	mm3_town_gnd = "twnwl4.vga" #frame 29
	mm4_town_gnd = "TOWN.GND"
	frame_number = 29
	convert_sprite_3to4(in_dir+"/"+mm3_town_gnd, out_dir+"/"+mm4_town_gnd, frame_number=frame_number)
	mm4_hash = hash_filename(mm4_town_gnd)
	copy_file(out_dir+"/"+mm4_town_gnd, out_dir+"/"+mm4_hash)

	#sky
	mm3_sky_sky = "day.vga"
	mm4_sky_skya = "SKY.SKYa"
	mm4_sky_skyb = "SKY.SKYb"
	mm4_sky_sky = "SKY.SKY"
	# mm4_town_skyo = "TOWN.SKYo"
	# convert_sprite_3to4(in_dir+"/"+mm3_town_sky, out_dir+"/"+mm4_town_skyo, True)
	convert_sprite_3to4(in_dir+"/"+mm3_sky_sky, out_dir+"/"+mm4_sky_skya, y_end=17)
	convert_sprite_3to4(in_dir+"/"+mm3_sky_sky, out_dir+"/"+mm4_sky_skyb, y_start=17)
	# now to put the two frames together into one file...
	merge_mm4_sprites(out_dir+"/"+mm4_sky_skya, out_dir+"/"+mm4_sky_skyb, out_dir+"/"+mm4_sky_sky)
	mm4_hash = hash_filename(mm4_sky_sky)
	copy_file(out_dir+"/"+mm4_sky_sky, out_dir+"/"+mm4_hash)

	#side walls
	mm3_town_swl_1 = "twnwl1.vga" #"twnwl1.vga","twnwl2.vga","twnwl3.vga","twnwl4.vga"
	mm4_town_swl = "STOWN.SWL" #48 frames
	#remap, then merge back together...
	


	#front walls
	mm3_town_fwl_1 = "twnwl1.vga"
	mm4_town_fwl_1 = "FTOWN1.FWL"
	#4 distance levels...
	convert_sprite_3to4(in_dir+"/"+mm3_town_fwl_1, out_dir+"/"+mm4_town_fwl_1+"00", frame_number=0)
	convert_sprite_3to4(in_dir+"/"+mm3_town_fwl_1, out_dir+"/"+mm4_town_fwl_1+"01", frame_number=1)
	convert_sprite_3to4(in_dir+"/"+mm3_town_fwl_1, out_dir+"/"+mm4_town_fwl_1+"02", frame_number=2)
	convert_sprite_3to4(in_dir+"/"+mm3_town_fwl_1, out_dir+"/"+mm4_town_fwl_1+"03", frame_number=3)
	convert_sprite_3to4(in_dir+"/"+mm3_town_fwl_1, out_dir+"/"+mm4_town_fwl_1+"04", frame_number=2)
	convert_sprite_3to4(in_dir+"/"+mm3_town_fwl_1, out_dir+"/"+mm4_town_fwl_1+"05", frame_number=3)
	convert_sprite_3to4(in_dir+"/"+mm3_town_fwl_1, out_dir+"/"+mm4_town_fwl_1+"06", frame_number=0)
	convert_sprite_3to4(in_dir+"/"+mm3_town_gnd, out_dir+"/"+mm4_town_fwl_1+"07", frame_number=29, y_end=4)

	merge_mm4_optimized(out_dir+"/"+mm4_town_fwl_1+"00", out_dir+"/"+mm4_town_fwl_1+"01", out_dir+"/"+mm4_town_fwl_1+"a")
	merge_mm4_optimized(out_dir+"/"+mm4_town_fwl_1+"a", out_dir+"/"+mm4_town_fwl_1+"02", out_dir+"/"+mm4_town_fwl_1+"b")
	merge_mm4_optimized(out_dir+"/"+mm4_town_fwl_1+"b", out_dir+"/"+mm4_town_fwl_1+"03", out_dir+"/"+mm4_town_fwl_1+"c")
	merge_mm4_optimized(out_dir+"/"+mm4_town_fwl_1+"c", out_dir+"/"+mm4_town_fwl_1+"04", out_dir+"/"+mm4_town_fwl_1+"d")
	merge_mm4_optimized(out_dir+"/"+mm4_town_fwl_1+"d", out_dir+"/"+mm4_town_fwl_1+"05", out_dir+"/"+mm4_town_fwl_1+"e")
	merge_mm4_optimized(out_dir+"/"+mm4_town_fwl_1+"e", out_dir+"/"+mm4_town_fwl_1+"06", out_dir+"/"+mm4_town_fwl_1+"f")
	merge_mm4_optimized(out_dir+"/"+mm4_town_fwl_1+"f", out_dir+"/"+mm4_town_fwl_1+"07", out_dir+"/"+mm4_town_fwl_1)

	mm4_hash = hash_filename(mm4_town_fwl_1)
	copy_file(out_dir+"/"+mm4_town_fwl_1, out_dir+"/"+mm4_hash)


MM3_FACE_SPRITE_NAMES = [
	'human1.fac','human2.fac','human3.fac','human4.fac',
	'dwarf1.fac','dwarf2.fac','dwarf3.fac','dwarf4.fac',
	'elf1.fac','elf2.fac','elf3.fac','elf4.fac',
	'gnome1.fac','gnome2.fac','gnome3.fac','gnome4.fac',
	'horc1.fac','horc2.fac','horc3.fac','horc4.fac',
	'hire0.fac','hire1.fac','hire2.fac','hire3.fac',
	'hire4.fac','hire5.fac','hire6.fac','hire7.fac','hire8.fac','hire9.fac']

def convert_2d_graphics(in_dir, out_dir):
	print("convert_2d_graphics")
	#portraits
	#in: human1.fac (32x32)
	#out: CHAR01.FAC (32x32)
	mm3_face = "human1.fac"
	mm4_face = "CHAR01.FAC"
	mm4_hash = hash_filename(mm4_face)
	convert_sprite_3to4(in_dir+"/"+mm3_face, out_dir+"/"+mm4_face)
	copy_file(out_dir+"/"+mm4_face, out_dir+"/"+mm4_hash)

	#character portraits (24)
	for i in range(24):
		mm3_fac = MM3_FACE_SPRITE_NAMES[i]
		mm4_fac = f"CHAR{(i+1):02}.FAC"
		mm4_hash = hash_filename(mm4_fac)

		convert_sprite_3to4(in_dir+"/"+mm3_fac, out_dir+"/"+mm4_fac)
		copy_file(out_dir+"/"+mm4_fac, out_dir+"/"+mm4_hash)



def convert_all(in_dir, out_dir):
	print("here we gooo!")
	convert_maps(in_dir, out_dir)
	convert_sprites(in_dir, out_dir)
	convert_environments(in_dir, out_dir)
	convert_2d_graphics(in_dir, out_dir)



if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Convert MM3 CC file contents to MM4 formats")
	parser.add_argument("indir", help="Directory containing contents of MM3 CC file")
	parser.add_argument("outdir", help="Directory to output converted file in MM4 formats")
	args = parser.parse_args()

	convert_all(args.indir, args.outdir)
