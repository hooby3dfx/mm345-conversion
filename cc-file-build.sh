#!/bin/sh

#cc file "build" script

#do the file conversion:
echo doing file conversion
python3 mm3to4_convert_main.py mm3out mm3to4_out > mm3tox_convert_main_log.txt

#copy build output to repack folder
echo copying build output to repack folder
cp mm3to4_out/d_*.ccx wipmm4to3repack
cp mm3to4_out/MAZE*.DAT wipmm4to3repack
cp mm3to4_out/MAZE*.EVT wipmm4to3repack
cp mm3to4_out/MAZE*.MOB wipmm4to3repack
cp mm3to4_out/AAZE*.TXT wipmm4to3repack
cp mm3to4_out/AAZE*.HED wipmm4to3repack
#temp workaround for starting level
cp mm3to4_out/MAZE0001.DAT wipmm4to3repack/MAZE0028.DAT
cp mm3to4_out/MAZE0001.EVT wipmm4to3repack/MAZE0028.EVT
cp mm3to4_out/MAZE0001.MOB wipmm4to3repack/MAZE0028.MOB
cp mm3to4_out/AAZE0001.TXT wipmm4to3repack/AAZE0028.TXT


#run Xeen CC Packer
echo now run Xeen CC Packer
printf "%s " "Press enter to continue"
read ans

#copy CC file to game dir
echo copying CC file to game dir
cp wipmm4to3repack/XEEN.CC ~/Games/dosc/XEEN/XEEN.CC 

echo all done! have fun
