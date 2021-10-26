import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

import git  # type: ignore

# Script config
MODNAME = sys.argv[1]

cwd = Path.cwd()
repo = git.Repo(cwd)

def build_release():
    if repo.active_branch.name != "master":
        print("- not on master branch, aborting")
        return
    if repo.is_dirty():
        print("- repository is dirty, aborting")
        return

    # Build mod
    print("Building mod ...")

    # Determine the next mod version
    modfiles_path = cwd / "modfiles"
    info_json_path = modfiles_path / "info.json"
    with info_json_path.open("r") as file:
        data = json.load(file)
    split_old_mod_version = data["version"].split(".")
    split_old_mod_version[-1] = str(int(split_old_mod_version[-1]) + 1)  # update version to the new one
    new_mod_version = ".".join(split_old_mod_version)

    # Bump info.json version
    data["version"] = new_mod_version
    with info_json_path.open("w") as file:
        json.dump(data, file, indent=4)
    print("- info.json version bumped")

    # Disable devmode if it is active
    tmp_path = modfiles_path / "tmp"
    control_file_path = modfiles_path / "control.lua"
    with tmp_path.open("w") as new_file, control_file_path.open("r") as old_file:
        for line in old_file:
            line = re.sub("DEVMODE = true", "DEVMODE = false", line)
            new_file.write(line)
    control_file_path.unlink()
    tmp_path.rename(control_file_path)
    print("- devmode disabled")

    # Update changelog file for release
    tmp_path = modfiles_path / "tmp"
    old_changelog_path = modfiles_path / "changelog.txt"
    with tmp_path.open("w") as new_file, old_changelog_path.open("r") as old_file:
        # Find the strings corresponding to eventual empty categories (this is silly)
        empty_categories = re.findall(r"  [\w]+:\n    - ?\n", old_file.read())
        empty_categories = [(line.split("\n")[0] + "\n") for line in empty_categories]
        empty_categories = dict.fromkeys(empty_categories, 1)
        old_file.seek(0)  # reset seekhead after file.read()

        # Rewrite the file, incorporating the necessary changes
        separation_line_count = 0  # Only change the topmost changelog entry
        for line in old_file:
            if re.match(r"-{99}", line):
                separation_line_count += 1

            if separation_line_count > 1:
                new_file.write(line)
            else:
                if "Version: 0.00.00" in line:
                    new_file.write("Version: {}\n".format(new_mod_version))
                elif "Date: 00. 00. 0000" in line:
                    new_file.write("Date: {}\n".format(datetime.today().strftime("%d. %m. %Y")))
                elif not re.match(r"    -( )?\n", line) and not line in empty_categories:
                    new_file.write(line)

    old_changelog_path.unlink()
    new_changelog_path = modfiles_path / "changelog.txt"
    tmp_path.rename(new_changelog_path)
    print("- changelog updated for release")

    # Remove symlink to scenarios-folder
    scenarios_symlink = modfiles_path / "scenarios"
    scenarios_symlink.unlink(missing_ok=True)
    print("- scenarios symlink removed")

    # Stealthily include the LICENSE
    tmp_license_path = modfiles_path / "LICENSE.md"
    shutil.copy(str(cwd / "LICENSE.md"), str(tmp_license_path))
    print("- license file included")

    # Include up-to-date versions of foreign locales, if present
    foreign_locale_path = cwd / "locale"
    modfiles_locale_path = modfiles_path / "locale"
    tmp_locale_license_path = modfiles_locale_path / "LICENSE.md"
    locale_list = []

    if foreign_locale_path.exists():
        locale_repo = repo.submodule("locale")

        # Pull locale module
        locale_repo.module().git.pull()

        # Stealthily include files into the zip
        shutil.copy(str(foreign_locale_path / "LICENSE.md"), tmp_locale_license_path)

        directory_list = [f for f in foreign_locale_path.rglob('./*') if f.is_dir()]
        for directory in directory_list:
            locale_name = directory.name
            locale_list.append(locale_name)
            locale_destination_path = modfiles_locale_path / locale_name
            locale_destination_path.mkdir()
            shutil.copy(str(directory / "config.cfg"), str(locale_destination_path / "config.cfg"))
        print("- foreign locale files updated")

    # Remove silly .DS_Store files before creating the zip.file
    for dirpath, _, _ in os.walk(modfiles_path):
        DS_store_path = Path(dirpath, ".DS_Store")
        DS_store_path.unlink(missing_ok=True)

    # Rename modfiles folder temporarily so the zip generates correctly
    full_mod_name = Path(MODNAME + "_" + new_mod_version)
    tmp_modfiles_path = cwd / full_mod_name
    modfiles_path.rename(tmp_modfiles_path)
    releases_path = cwd / "releases"
    releases_path.mkdir(exist_ok=True)
    zipfile_path = releases_path / full_mod_name
    shutil.make_archive(str(zipfile_path), "zip", str(cwd), str(tmp_modfiles_path.parts[-1]))
    tmp_modfiles_path.rename(modfiles_path)
    print("- zip archive created")

    # Remove stealthily included files
    tmp_license_path.unlink()
    tmp_locale_license_path.unlink(missing_ok=True)
    for locale in locale_list:
        shutil.rmtree(str(modfiles_locale_path / locale))

    # Commit release changes
    repo.git.add("-A")
    repo.git.commit(m="Release {}".format(new_mod_version))
    print("Build complete\n")

    # Start new dev cycle immediately
    print("Preparing new development cycle ...")

    # Add a blank changelog entry for further development
    changelog_path = modfiles_path / "changelog.txt"
    new_changelog_entry = ("-----------------------------------------------------------------------------------------"
                           "----------\nVersion: 0.00.00\nDate: 00. 00. 0000\n  Features:\n    - \n  Changes:\n    - "
                           "\n  Bugfixes:\n    - \n\n")
    with (changelog_path.open("r")) as changelog:
        old_changelog = changelog.readlines()
    old_changelog.insert(0, new_changelog_entry)
    with (changelog_path.open("w")) as changelog:
        changelog.writelines(old_changelog)
    print("- blank changelog entry added")

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

    # Commit new dev cycle changes
    repo.git.add("-A")
    repo.git.commit(m="Start new development cycle")
    print("Development cycle started\n")

    # Push to Github
    print("Pushing changes ...", end=" ", flush=True)
    repo.git.push("origin")
    print("done")


if __name__ == "__main__":
    proceed = input(f"[{MODNAME}] Sure to build a release? (y/n): ")
    if proceed == "y":
        build_release()
