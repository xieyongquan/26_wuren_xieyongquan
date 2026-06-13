#!/bin/bash

mkdir linux_practice
cd linux_practice
mkdir docs backup

cd ./docs/
touch readme.txt notes.log temp.tmp

rm temp.tmp
mv notes.log daily_report.txt

echo "Project Status: Active" >  daily_report.txt 
date >> daily_report.txt 

cp *.txt ../backup/

cd ../backup/
chmod 444 *

echo "Archive Complete."
for file in *
do
    echo "File [$file] is now read-only."
done
