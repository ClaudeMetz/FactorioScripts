import json
import re
import shutil
import sys
from pathlib import Path

# Script config
MODNAME = sys.argv[1]

cwd = Path.cwd() / ".."  # back out of scripts folder

# pylint: disable=too-many-locals
def new_migration():
    # Determine the next mod version
    modfiles_path = cwd / "modfiles"
    with (modfiles_path / "info.json").open("r") as file:
        split_old_mod_version = json.load(file)["version"].split(".")
    split_old_mod_version[-1] = str(int(split_old_mod_version[-1]) + 1)  # update version to the new one
    new_mod_version = ".".join(split_old_mod_version)
    print("- next version determined")

    # Add a new migration file, targeted at the next version, using the blank 0_0_0 template
    migrations_path = modfiles_path / "data" / "migrations"
    blank_migration_path = (migrations_path / "migration_0_0_0.lua")
    new_migration_path = migrations_path / f"migration_{new_mod_version.replace('.', '_')}.lua"
    shutil.copy(blank_migration_path, new_migration_path)
    print("- migration file created")

    # Load and update the masterlist
    masterlist_path = migrations_path / "masterlist.json"
    with masterlist_path.open("r") as file:
        masterlist = json.load(file)
    masterlist.append(new_mod_version)
    with masterlist_path.open("w") as file:
        json.dump(masterlist, file, indent=4)
    print("- masterlist updated")

    # Update migrator to include the new migration (a bit janky)
    migrator_path = modfiles_path / "data" / "handlers" / "migrator.lua"
    with (migrator_path.open("r")) as migrator:
        migrator_lines = migrator.readlines()

    # Remove every line of the migration masterlist and replace them according to the masterlist
    version_line_regex = r"^\s+\[\d+\] = {version=.+},?\n$"
    migrator_lines[:] = [line for line in migrator_lines if not re.fullmatch(version_line_regex, line)]
    for line_index, line in enumerate(migrator_lines):
        if "local migration_masterlist = {" in line:
            version_index = 1
            for masterlist_version in masterlist:
                internal_version = masterlist_version.replace(".", "_")
                new_version_line = (f"    [{version_index}] = {{version=\"{masterlist_version}\", "
                                    f"migration=require(\"data.migrations.migration_{internal_version}\")}},\n")
                migrator_lines.insert(line_index+version_index, new_version_line)
                version_index += 1
            break

    with (migrator_path.open("w")) as migrator:
        migrator.writelines(migrator_lines)
    print("- migrator file updated")


if __name__ == "__main__":
    proceed = input(f"[{MODNAME}] Sure to add a new migration? (y/n): ")
    if proceed == "y":
        new_migration()
