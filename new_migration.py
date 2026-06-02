#!/usr/bin/env python3

import json
import re
import shutil
from pathlib import Path

cwd = Path.cwd() / ".."  # back out of scripts folder

def new_migration() -> None:
    # Determine the next mod version
    modfiles_path = cwd / "modfiles"
    with (modfiles_path / "info.json").open("r") as file:
        split_old_mod_version = json.load(file)["version"].split(".")
    split_old_mod_version[-1] = str(int(split_old_mod_version[-1]) + 1)  # update version to the new one
    new_mod_version = ".".join(split_old_mod_version)
    print("- next version determined")

    # Add a new migration file, targeted at the next version, using the blank 0_0_0 template
    migrations_path = modfiles_path / "backend" / "migrations"
    blank_migration_path = (migrations_path / "migration_0_0_0.lua")
    new_migration_path = migrations_path / f"migration_{new_mod_version.replace('.', '_')}.lua"
    shutil.copy(blank_migration_path, new_migration_path)
    print("- migration file created")

    # Update migrator to include the new migration
    migrator_path = migrations_path / "migrator.lua"
    with migrator_path.open("r") as migrator:
        migrator_lines = migrator.readlines()

    # Extract existing versions from migrator in order, then append the new one
    version_line_regex = r"^\s+\[\d+\] = {version=\"([^\"]+)\".+},?\n$"
    masterlist = [m.group(1) for line in migrator_lines if (m := re.fullmatch(version_line_regex, line))]
    masterlist.append(new_mod_version)

    # Remove every existing version line and reinsert them all in order
    migrator_lines[:] = [line for line in migrator_lines if not re.fullmatch(version_line_regex, line)]
    for line_index, line in enumerate(migrator_lines):
        if "local migration_masterlist = {" in line:
            for version_index, version in enumerate(masterlist, start=1):
                internal_version = version.replace(".", "_")
                new_version_line = (f"    [{version_index}] = {{version=\"{version}\", "
                                    f"migration=require(\"backend.migrations.migration_{internal_version}\")}},\n")
                migrator_lines.insert(line_index+version_index, new_version_line)
            break

    with migrator_path.open("w") as migrator:
        migrator.writelines(migrator_lines)
    print("- migrator file updated")


if __name__ == "__main__":
    new_migration()
