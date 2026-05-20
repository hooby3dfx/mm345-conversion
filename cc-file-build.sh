#!/bin/sh

#cc file "build" script
repack_dir=wipmm5to3repack #or wipmm4to3repack
base_game=DARK #XEEN or DARK
first_level=29

#do the file conversion:
echo doing file conversion
python3 mm3to4_convert_main.py mm3out mm3to4_out > mm3tox_convert_main_log.txt

#copy build output to repack folder
echo copying build output to repack folder
cp mm3to4_out/d_*.ccx $repack_dir
cp mm3to4_out/MAZE*.DAT $repack_dir
cp mm3to4_out/MAZE*.EVT $repack_dir
cp mm3to4_out/MAZE*.MOB $repack_dir
cp mm3to4_out/AAZE*.TXT $repack_dir
cp mm3to4_out/AAZE*.HED $repack_dir
# cp mm3to4_out/XEEN*.TXT $repack_dir
cp mm3to4_out/DARK*.TXT $repack_dir
#temp workaround for starting level
cp mm3to4_out/MAZE0001.DAT $repack_dir/MAZE00${first_level}.DAT
cp mm3to4_out/MAZE0001.EVT $repack_dir/MAZE00${first_level}.EVT
cp mm3to4_out/MAZE0001.MOB $repack_dir/MAZE00${first_level}.MOB
cp mm3to4_out/AAZE0001.TXT $repack_dir/AAZE00${first_level}.TXT
# cp mm3to4_out/XEEN0001.TXT $repack_dir/XEEN0028.TXT
cp mm3to4_out/${base_game}0001.TXT $repack_dir/${base_game}00${first_level}.TXT


#run Xeen CC Packer
echo now run Xeen CC Packer
printf "%s " "Press enter to continue"
read ans

#copy CC file to game dir
echo copying CC file to game dir
cp $repack_dir/${base_game}.CC ~/Games/dosc/wox/${base_game}.CC 

echo all done! have fun
