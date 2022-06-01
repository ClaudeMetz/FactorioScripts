import json
import re
import sys
from pathlib import Path

from git import Repo

# Script config
MODNAME = sys.argv[1]
RELEASE = (len(sys.argv) == 5 and sys.argv[4] == "--release")

cwd = Path.cwd() / ".."  # back out of scripts folder
repo = Repo(cwd)

def update_versions() -> None:
    relevant_branch = repo.active_branch.name
    if RELEASE and relevant_branch == "master":
        print("- on master branch, aborting")
        return
    if RELEASE and repo.is_dirty():
        print("- repository is dirty, aborting")
        return

    # Determine the old migration version on this branch
    modfiles_path = cwd / "modfiles"
    migrations_path = modfiles_path / "data" / "migrations"
    masterlist_path = migrations_path / "masterlist.json"
    with masterlist_path.open("r") as file:
        masterlist = json.load(file)
    old_migration_version = masterlist[-1]  # grab last version in the list
    print("- old migration version determined")

    # Determine the current and next mod version on master
    repo.git.checkout("master")
    with (modfiles_path / "info.json").open("r") as file:
        current_mod_version = json.load(file)["version"]
    split_current_mod_version = current_mod_version.split(".")
    split_current_mod_version[-1] = str(int(split_current_mod_version[-1]) + 1)  # update version to the new one
    new_mod_version = ".".join(split_current_mod_version)
    repo.git.checkout(relevant_branch)
    print("- next mod version determined")

    if old_migration_version == new_mod_version:
        print("- migration up to date, aborting")
        return

    # Update info.json
    info_json_path = modfiles_path / "info.json"
    with info_json_path.open("r") as file:
        data = json.load(file)
    data["version"] = current_mod_version
    with info_json_path.open("w") as file:
        json.dump(data, file, indent=4)
    print("- info.json version updated")

    # Update the migration file filename
    old_migration_path = migrations_path / f"migration_{old_migration_version.replace('.', '_')}.lua"
    old_migration_path.rename(migrations_path / f"migration_{new_mod_version.replace('.', '_')}.lua")
    print("- migration filename updated")

    # Update the last entry in the masterlist
    masterlist[-1] = new_mod_version
    with masterlist_path.open("w") as file:
        json.dump(masterlist, file, indent=4)
    print("- masterlist updated")

    # Update migrator to include the new migration (a bit janky)
    migrator_path = modfiles_path / "data" / "handlers" / "migrator.lua"
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
    repo.git.commit(m="Update mod and migration versions")
    print("- changes committed")


if __name__ == "__main__":
    proceed = input(f"[{MODNAME}] Sure to update mod and migration versions? (y/n): ")
    if proceed == "y":
        update_versions()
