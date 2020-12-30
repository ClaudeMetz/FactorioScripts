#!/bin/bash

# macOS script to select and run various convenience scripts
# It runs the selected python script in the appropriate directory

origin=$(pwd)

cd ".."
modname=${PWD##*/}

echo "[1] New migration"
echo "[2] Update versions"
echo "[3] Build release"
echo -e "Select script to run: \c"
read choice

if [ $choice -eq 1 ]
then
    cd "modfiles/"
    script="${origin}/new_migration.py"
elif [ $choice -eq 2 ]
then
    cd "modfiles/"
    script="${origin}/update_versions.py"
elif [ $choice -eq 3 ]
then
    script="${origin}/build_release.py"
else
    exit
fi

python3 $script $modname
cd $origin