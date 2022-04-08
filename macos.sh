#!/bin/bash

# macOS script to select and run various convenience scripts
# It runs the selected Python script in the appropriate directory

factoriopath="/Applications/factorio.app/Contents/MacOS/factorio"
userdatapath="~/Library/Application Support/factorio"

origin=$(pwd)

cd ".."
modname=${PWD##*/}  # grab the mod's name via the directory name
cd $origin

echo "[1] New migration"
echo "[2] Update versions"
echo "[3] Publish release"
echo "[4] Take screenshots"
echo -e "Select script to run: \c"
read choice

if [ $choice -eq 1 ]
then
    script="new_migration.py"
elif [ $choice -eq 2 ]
then
    script="update_versions.py"
elif [ $choice -eq 3 ]
then
    script="build_release.py"
elif [ $choice -eq 4 ]
then
    script="take_screenshots.py"
else
    exit
fi

python3 "$script" $modname "$factoriopath" "$userdatapath" $1
