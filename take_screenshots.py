# This script adds a new, blank migration and integrates it properly
# It needs to be run in the root mod project folder
# Folder structure needs to be the same as Factory Planner to work

import sys
import shutil
import subprocess
from pathlib import Path

# Script config
MODNAME = sys.argv[1]
FACTORIO_PATH = sys.argv[2]
USERDATA_PATH = sys.argv[3]

cwd = Path.cwd()

def take_screenshots():
    screenshotter_path =  cwd / "scenarios" / "screenshotter"
    if not screenshotter_path.is_dir():
        print("- no screenshotter scenario found, aborting")
        return

    # Overwrite mod-list.json with the one found in the scenarios folder
    current_modlist_path = Path(USERDATA_PATH) / "mods" / "mod-list.json"
    current_modlist_path.unlink(missing_ok=True)
    shutil.copy(str(screenshotter_path / "mod-list.json"), str(current_modlist_path))
    print("- replaced mod-list.json")

    # Run the screenshotting scenario, waiting for it to finish
    print("- running scenario ...", end=" ", flush=True)
    subprocess.run([
        "/usr/bin/open", "-W", "-a", FACTORIO_PATH, "--args",
        "--load-scenario", "{}/screenshotter".format(MODNAME),
        "--config", str(screenshotter_path / "config.ini")
        ]
    )
    print("done")


if __name__ == "__main__":
    take_screenshots()
    #proceed = input(f"[{MODNAME}] Sure to take screenshots? (y/n): ")
    #if proceed == "y":
