#!/usr/bin/env python3

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path, PosixPath

import requests
from git import Repo
from PIL import Image  # type: ignore

cwd = Path.cwd() / ".."  # back out of scripts folder
repo = Repo(cwd)

# Script config
MODNAME = cwd.resolve().name
FACTORIO_PATH = "/Applications/factorio.app/Contents/MacOS/factorio"
USERDATA_PATH = PosixPath("~/Library/Application Support/factorio").expanduser()
RELEASE = (len(sys.argv) == 2 and sys.argv[1] == "--release")
LOCAL = (len(sys.argv) == 2 and sys.argv[1] == "--local")

def publish_release(take_screenshots: bool) -> None:
    if RELEASE and repo.active_branch.name != "master":
        print("- not on master branch, aborting")
        return
    if RELEASE and repo.is_dirty():
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
        empty_category_dict = dict.fromkeys(empty_categories, 1)
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
                elif not re.match(r"    -( )?\n", line) and line not in empty_category_dict:
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
    control_path, tmp_control_path = modfiles_path / "control.lua", modfiles_path / "tmp"
    shutil.copyfile(control_path, tmp_control_path)  # copy to restore afterwards
    release_control_code = re.sub("DEV_ACTIVE = true", "DEV_ACTIVE = false", control_path.read_text())
    control_path.write_text(release_control_code)

    # Copy relevant files to temporary folder
    full_mod_name = Path(f"{MODNAME}_{new_mod_version}")
    tmp_release_path = cwd / full_mod_name
    ignore_patterns = shutil.ignore_patterns('.*', 'scenarios', 'tmp', '')
    shutil.copytree(modfiles_path, tmp_release_path, ignore=ignore_patterns)
    print("- relevant files copied")

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

    # Run screenshotter if requested and possible
    screenshotter_path =  cwd / "scenarios" / "screenshotter"
    if take_screenshots and screenshotter_path.is_dir():
        # Overwrite mod-list.json with the one found in the scenarios folder
        current_modlist_path = USERDATA_PATH / "mods" / "mod-list.json"
        current_modlist_path.unlink(missing_ok=True)
        shutil.copy(str(screenshotter_path / "mod-list.json"), str(current_modlist_path))
        print("- mod-list.json replaced")

        # Run the screenshotting scenario, waiting for it to signal it's done
        print("- taking screenshots...", end=" ", flush=True)
        with subprocess.Popen(
            [FACTORIO_PATH,
            "--load-scenario", f"{MODNAME}/screenshotter",
            "--config", str(screenshotter_path / "config.ini"),
            "--instrument-mod", MODNAME  # use the same mod as the instrument mod for simplicity
            ], stdout=subprocess.PIPE, bufsize=1, universal_newlines=True
        ) as factorio:
            if factorio.stdout is not None:
                for line in factorio.stdout:
                    if line.strip() == "screenshotter_done":
                        factorio.terminate()
        print("done")

        # Load metadata from generated JSON file
        script_output_path = Path(USERDATA_PATH, "script-output")
        with (script_output_path / "metadata.json").open("r") as file:
            frame_corners = json.load(file)["frame_corners"]
        print("- metadata loaded")

        # Clear previous screenshots
        screenshots_path = cwd / "screenshots"
        for screenshot in screenshots_path.iterdir():
            screenshot.unlink()
        print("- previous screenshots cleared")

        # Crop screenshots according to the given dimensions
        for scene, corners in frame_corners.items():
            screenshot_path = script_output_path / f"{scene}.png"
            image = Image.open(screenshot_path)

            cropped_img = image.crop((
                corners["top_left"]["x"] - 15,
                corners["top_left"]["y"] - 15,
                corners["bottom_right"]["x"] + 15,
                corners["bottom_right"]["y"] + 15
            ))
            cropped_img.save(screenshots_path / f"{scene}.png")
        print("- screenshots cropped and saved")

        # Clean up script output
        shutil.rmtree(script_output_path)
        print("- script-output removed")

    # Commit changes
    repo.git.add("-A")
    repo.git.commit(m=f"Release {new_mod_version}")
    print("- changes commited")

    if LOCAL:
        shutil.copy(archive_path, cwd / f"{full_mod_name}.zip")
        repo.head.reset("HEAD~1", index=True, working_tree=True)

    if RELEASE:
        # Push to Github
        print("- pushing to Github...", end=" ", flush=True)
        repo.git.push("origin")
        print("done")

        def upload_data(upload_url: str, api_key: str, file_path: str, dataset_name: str) -> None:
            response = requests.post(
                upload_url,
                data = {"mod": MODNAME},
                headers = {"Authorization": f"Bearer {api_key}"}
            )
            if not response.ok:
                raise RuntimeError(f"init_upload failed: {response.text}")

            upload_url = response.json()["upload_url"]
            with open(file_path, "rb") as file:
                response = requests.post(upload_url, files={dataset_name: file})
                if not response.ok:
                    raise RuntimeError(f"upload failed: {response.text}")

        # Publish to mod portal
        print("- publishing to mod portal...", end=" ", flush=True)
        UPLOAD_API_URL = "https://mods.factorio.com/api/v2/mods/releases/init_upload"
        UPLOAD_API_KEY = os.getenv("MOD_UPLOAD_API_KEY") or ""
        upload_data(UPLOAD_API_URL, UPLOAD_API_KEY, archive_path, "file")
        print("done")

        # Update mod portal screenshots if requested
        if take_screenshots:
            IMAGE_API_URL = "https://mods.factorio.com/api/v2/mods/images"
            EDIT_API_KEY = os.getenv("MOD_EDIT_API_KEY") or ""

            # Remove old mod portal images
            print("- removing old mod portal images...", end=" ", flush=True)
            response = requests.post(
                f"{IMAGE_API_URL}/edit",
                data = {"mod": MODNAME, "images": []},
                headers = {"Authorization": f"Bearer {EDIT_API_KEY}"}
            )
            if not response.ok:
                raise RuntimeError(f"edit failed: {response.text}")
            print("done")

            # Upload new mod portal images
            print("- uploading to mod portal...", end=" ", flush=True)
            for screenshot_path in sorted(screenshots_path.iterdir()):
                upload_data(f"{IMAGE_API_URL}/add", EDIT_API_KEY, str(screenshot_path), "image")
            print("done")

    print(f"Version {new_mod_version} released!")


if __name__ == "__main__":
    if LOCAL:
        publish_release(False)
    else:
        proceed = input("Sure to publish a release? (y/n): ")
        if proceed == "y":
            screenshots = input("Retake screenshots as well? (y/n): ")
            publish_release(screenshots == "y")
