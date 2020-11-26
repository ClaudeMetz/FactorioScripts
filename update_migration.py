# This script updates the most recent migration to apply to the next release
# It deduces the next release from the master branch
# This becomes necessary when an older feature branch becomes out of date
# It needs to be run in the root of the folder that contains the mod files
# Folder structure needs to be the same as Factory Planner to work

import json
import shutil
import re
from pathlib import Path

import git  # gitpython module

cwd = Path.cwd()
repo = git.Repo(cwd / "..")

def update_migration():
    relevant_branch = repo.active_branch.name
    if relevant_branch == "master":
        print("- on master branch, aborting")
        return

    # Determine the old migration version on this branch
    migrations_path = cwd / "data" / "migrations"
    masterlist_path = migrations_path / "masterlist.json"
    with masterlist_path.open("r") as file:
        masterlist = json.load(file)
    old_migration_version = masterlist[-1]  # grab last version in the list
    print("- old migration version determined")

    # Determine the next mod version on master
    repo.git.checkout("master")
    with (cwd / "info.json").open("r") as file:
        split_old_mod_version = json.load(file)["version"].split(".")
    split_old_mod_version[-1] = str(int(split_old_mod_version[-1]) + 1)  # update version to the new one
    new_mod_version = ".".join(split_old_mod_version)
    repo.git.checkout(relevant_branch)
    print("- next mod version determined")

    if old_migration_version == new_mod_version:
        print("- migration up to date, aborting")
        return

    # Update the migration file filename
    old_migration_path = (migrations_path / "migration_{}.lua".format(old_migration_version.replace(".", "_")))
    old_migration_path.rename(migrations_path / "migration_{}.lua".format(new_mod_version.replace(".", "_")))
    print("- migration filename updated")

    # Update the last entry in the masterlist
    masterlist[-1] = new_mod_version
    with masterlist_path.open("w") as file:
        json.dump(masterlist, file, indent=4)
    print("- masterlist updated")

    # Update migrator to include the new migration (a bit janky)
    migrator_path = cwd / "data" / "handlers" / "migrator.lua"
    with (migrator_path.open("r")) as migrator:
        migrator_lines = migrator.readlines()

    # Update migrator file (shamelessly copied from new_migration.py because that's easier)
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

    # Commit changes
    repo.git.add("-A")
    repo.git.commit(m="Update migration version")
    print("- changes committed")


if __name__ == "__main__":
    proceed = input("Sure to update the last migration? (y/n): ")
    if proceed == "y":
        update_migration()
