#!/bin/sh

#cc file "build" script
output_dir=mm3to4_out
repack_dir=wipmm5to3repack #or wipmm4to3repack
base_game=DARK #XEEN or DARK
first_level=29
clean_slate=1

if [ $clean_slate -gt 0 ]; then
	echo clean slating $output_dir
	rm -rf $output_dir
	mkdir $output_dir

	echo clean slating $repack_dir
	rm -rf $repack_dir
	cp -r ext_darkw $repack_dir
fi

#do the file conversion:
echo doing file conversion
python3 mm3to4_convert_main.py mm3out $output_dir > mm3tox_convert_main_log.txt

#temp workaround for maze29 -> maze129
mv $output_dir/MAZE00${first_level}.DAT $output_dir/MAZEX1${first_level}.DAT
mv $output_dir/MAZE00${first_level}.EVT $output_dir/MAZEX1${first_level}.EVT
mv $output_dir/MAZE00${first_level}.MOB $output_dir/MAZEX1${first_level}.MOB
mv $output_dir/AAZE00${first_level}.TXT $output_dir/AAZEX1${first_level}.TXT
mv $output_dir/AAZE00${first_level}.HED $output_dir/AAZEX1${first_level}.HED
mv $output_dir/${base_game}00${first_level}.TXT $output_dir/${base_game}X1${first_level}.TXT

#copy build output to repack folder
echo copying build output to repack folder
cp $output_dir/d_*.ccx $repack_dir
cp $output_dir/MAZE*.DAT $repack_dir
cp $output_dir/MAZE*.EVT $repack_dir
cp $output_dir/MAZE*.MOB $repack_dir
cp $output_dir/AAZE*.TXT $repack_dir
cp $output_dir/AAZE*.HED $repack_dir
# cp $output_dir/XEEN*.TXT $repack_dir
cp $output_dir/DARK*.TXT $repack_dir

#temp workaround for starting level
# cp $output_dir/MAZE0001.DAT $repack_dir/MAZE00${first_level}.DAT
# cp $output_dir/MAZE0001.EVT $repack_dir/MAZE00${first_level}.EVT
# cp $output_dir/MAZE0001.MOB $repack_dir/MAZE00${first_level}.MOB
# cp $output_dir/AAZE0001.TXT $repack_dir/AAZE00${first_level}.TXT
# # cp $output_dir/XEEN0001.TXT $repack_dir/XEEN0028.TXT
# cp $output_dir/${base_game}0001.TXT $repack_dir/${base_game}00${first_level}.TXT


#run Xeen CC Packer
echo now run Xeen CC Packer
printf "%s " "Press enter to continue"
read ans

#copy CC file to game dir
echo copying CC file to game dir
cp $repack_dir/${base_game}.CC ~/Games/dosc/wox/${base_game}.CC 

echo all done! have fun
