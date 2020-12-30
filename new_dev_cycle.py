# This script adds a new, blank changelog entry and enables devmode
# It needs to be run in the root of the folder that contains the mod files
# Folder structure needs to be the same as Factory Planner to work

import re
import sys
from pathlib import Path

# Script config
MODNAME = sys.argv[1]

cwd = Path.cwd()
modfiles_path = cwd / "modfiles"

def new_dev_cycle():
    # Add a blank changelog entry for further development
    changelog_path = modfiles_path / "changelog.txt"
    new_changelog_entry = ("-----------------------------------------------------------------------------------------"
                           "----------\nVersion: 0.00.00\nDate: 00. 00. 0000\n  Features:\n    - \n  Changes:\n    - "
                           "\n Bugfixes:\n    - \n\n")
    with (changelog_path.open("r")) as changelog:
        old_changelog = changelog.readlines()
    old_changelog.insert(0, new_changelog_entry)
    with (changelog_path.open("w")) as changelog:
        changelog.writelines(old_changelog)
    print("- changelog entry added")

    # Disable devmode
    tmp_path = modfiles_path / "tmp"
    control_file_path = modfiles_path / "control.lua"
    with tmp_path.open("w") as new_file, control_file_path.open("r") as old_file:
        for line in old_file:
            line = re.sub("DEVMODE = false", "DEVMODE = true", line)
            new_file.write(line)
    control_file_path.unlink()
    tmp_path.rename(control_file_path)
    print("- devmode enabled")

    # Create symlink to scenarios-folder
    scenarios_path = cwd / "scenarios"
    if scenarios_path.is_dir():
        tmp_scenarios_path = modfiles_path / "scenarios"
        tmp_scenarios_path.symlink_to(scenarios_path)
        print("- scenarios symlink created")


if __name__ == "__main__":
    proceed = input(f"[{MODNAME}] Sure to start a new dev cycle? (y/n): ")
    if proceed == "y":
        new_dev_cycle()
