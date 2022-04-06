import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import git
import requests

# Script config
MODNAME = sys.argv[1]

cwd = Path.cwd()
repo = git.Repo(cwd)

# pylint: disable=too-many-locals, too-many-statements, too-many-branches
def build_release():
    if repo.active_branch.name != "master":
        print("- not on master branch, aborting")
        return
    if repo.is_dirty():
        print("- repository is dirty, aborting")
        return

    # Determine the next mod version
    modfiles_path = cwd / "modfiles"
    info_json_path = modfiles_path / "info.json"
    with info_json_path.open("r") as file:
        data = json.load(file)
    split_old_mod_version = data["version"].split(".")
    split_old_mod_version[-1] = str(int(split_old_mod_version[-1]) + 1)  # update version to the new one
    new_mod_version = ".".join(split_old_mod_version)

    # Detect whether Phobos should be used or not
    if (modfiles_path / "control.lua").is_file():
        control_path = modfiles_path / "control.lua"
        ignore_pattern = ""
    elif (modfiles_path / "control.pho").is_file():
        control_path = modfiles_path / "control.pho"
        ignore_pattern = "*.pho"

    # Bump info.json version
    data["version"] = new_mod_version
    with info_json_path.open("w") as file:
        json.dump(data, file, indent=4)
    print("- info.json version bumped")

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
                    new_file.write(f"Version: {new_mod_version}\n")
                elif "Date: 00. 00. 0000" in line:
                    new_file.write(f"Date: {datetime.today().strftime('%d. %m. %Y')}\n")
                elif not re.match(r"    -( )?\n", line) and not line in empty_categories:
                    new_file.write(line)

    old_changelog_path.unlink()
    new_changelog_path = modfiles_path / "changelog.txt"
    tmp_path.rename(new_changelog_path)
    print("- changelog updated for release")

    # Update README year if necessary
    mod_license_path = cwd / "LICENSE.md"
    current_year = datetime.today().year
    notice_regex = r"Copyright \(c\) [0-9]{4}"
    updated_license_text = re.sub(notice_regex, f"Copyright (c) {current_year}", mod_license_path.read_text())
    mod_license_path.write_text(updated_license_text)
    print("- updated LICENSE year")

    # Disable devmode for release
    tmp_control_path = modfiles_path / "tmp"
    shutil.copyfile(control_path, tmp_control_path)  # copy to restore after Phobos compilation
    release_control_code = re.sub("DEVMODE = true", "DEVMODE = false", control_path.read_text())
    control_path.write_text(release_control_code)

    # Copy relevant files to temporary folder
    full_mod_name = Path(MODNAME + "_" + new_mod_version)
    tmp_release_path = cwd / full_mod_name
    ignore_patterns = shutil.ignore_patterns('.*', 'scenarios', 'tmp', ignore_pattern)
    shutil.copytree(modfiles_path, tmp_release_path, ignore=ignore_patterns)
    print("- relevant files copied")

    # Build with Phobos if necessary
    if ignore_pattern == "*.pho":
        phobos_path = cwd / "scripts" / "phobos_osx"
        print("- building with phobos...", end=" ", flush=True)
        subprocess.run([
                "./lua", "--", "main.lua",
                "--source", modfiles_path,
                "--output", tmp_release_path,
                "--profile", "release",
                "--use-load"
            ], cwd=phobos_path, check=True
        )

    # Restore control.lua from backup
    tmp_control_path.rename(control_path)

    # Include LICENSE file
    shutil.copy(str(cwd / "LICENSE.md"), str(tmp_release_path / "LICENSE.md"))
    print("- license file included")

    # Include up-to-date versions of foreign locales, if present
    foreign_locale_path = cwd / "locale"
    release_locale_path = tmp_release_path / "locale"
    tmp_locale_license_path = release_locale_path / "LICENSE.md"

    if foreign_locale_path.exists():
        shutil.copy(str(foreign_locale_path / "LICENSE.md"), tmp_locale_license_path)

        locale_repo = repo.submodule("locale")
        locale_repo.module().git.pull()

        locale_list = []
        directory_list = [f for f in foreign_locale_path.rglob('./*') if f.is_dir()]
        for directory in directory_list:
            locale_name = directory.name
            locale_list.append(locale_name)
            locale_destination_path = release_locale_path / locale_name
            locale_destination_path.mkdir()
            shutil.copy(str(directory / "config.cfg"), str(locale_destination_path / "config.cfg"))
        print("- foreign locale files updated")

    # ZIP up release
    releases_path = cwd / "releases"
    releases_path.mkdir(exist_ok=True)
    zipfile_path = releases_path / full_mod_name
    archive_path = shutil.make_archive(str(zipfile_path), "zip", str(cwd), str(tmp_release_path.parts[-1]))
    shutil.rmtree(tmp_release_path)
    print("- zip archive created")

    # Add a blank changelog entry for further development
    changelog_path = modfiles_path / "changelog.txt"
    new_changelog_entry = ("-----------------------------------------------------------------------------------------"
                           "----------\nVersion: 0.00.00\nDate: 00. 00. 0000\n  Features:\n    - \n  Changes:\n    - "
                           "\n  Bugfixes:\n    - \n\n")
    updated_changelog = new_changelog_entry + changelog_path.read_text()
    changelog_path.write_text(updated_changelog)
    print("- blank changelog entry added")

    # Commit and push release changes
    repo.git.add("-A")
    repo.git.commit(m=f"Release {new_mod_version}")
    print("- pushing changes...", end=" ", flush=True)
    repo.git.push("origin")
    print("done")

    # Publish to mod portal
    print("- publishing to mod portal...", end=" ", flush=True)
    apikey = os.getenv("MOD_UPLOAD_API_KEY")
    response = requests.post(
        "https://mods.factorio.com/api/v2/mods/releases/init_upload",
        data = {"mod": MODNAME},
        headers = {"Authorization": f"Bearer {apikey}"}
    )
    if not response.ok:
        raise RuntimeError(f"init_upload failed: {response.text}")

    upload_url = response.json()["upload_url"]
    with open(archive_path, "rb") as file:
        response = requests.post(upload_url, files={"file": file})
        if not response.ok:
            raise RuntimeError(f"upload failed: {response.text}")
    print("done")


if __name__ == "__main__":
    proceed = input(f"[{MODNAME}] Sure to publish a release? (y/n): ")
    if proceed == "y":
        build_release()
