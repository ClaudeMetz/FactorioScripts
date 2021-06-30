#!/bin/bash

# macOS script to select and run various convenience scripts
# It runs the selected Python script in the appropriate directory

origin=$(pwd)

cd ".."
modname=${PWD##*/}

# These paths are for a default macOS Factorio installation for the user 'claude'
factoriopath="/Applications/Factorio.app"
userdatapath="/Users/claude/Library/Application Support/factorio"

echo "[1] New migration"
echo "[2] Update versions"
echo "[3] Build release"
echo "[4] Take screenshots"
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
elif [ $choice -eq 4 ]
then
    script="${origin}/take_screenshots.py"
else
    exit
fi

python3 "$script" $modname "$factoriopath" "$userdatapath"
cd $origin
