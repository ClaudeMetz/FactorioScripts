#!/usr/bin/env python3

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import requests
from git import Repo
from PIL import Image  # type: ignore

ROOT = Path(__file__).resolve().parent.parent  # the script lives in ROOT/scripts
repo = Repo(ROOT)

# Script config
INFO_PATH = ROOT / "modfiles" / "info.json"
MODNAME = json.loads(INFO_PATH.read_text())["name"]
RELEASE = (len(sys.argv) == 2 and sys.argv[1] == "--release")
LOCAL = (len(sys.argv) == 2 and sys.argv[1] == "--local")

def publish_release(take_screenshots: bool) -> None:
    if RELEASE and repo.active_branch.name != "master":
        print("- not on master branch, aborting")
        return
    if RELEASE and repo.is_dirty():
        print("- repository is dirty, aborting")
        return

    needed_vars = ["FACTORIO", "FACTORIO_USERDATA"] if take_screenshots else []
    if RELEASE:
        needed_vars += ["MOD_UPLOAD_API_KEY", "MOD_DISCORD_WEBHOOK"]
        needed_vars += ["MOD_EDIT_API_KEY"] if take_screenshots else []
    missing_vars = [var for var in needed_vars if not os.getenv(var)]
    if missing_vars:
        print(f"- environment variable(s) {', '.join(missing_vars)} unset, aborting")
        return
    if take_screenshots and not Path(os.environ["FACTORIO"]).exists():
        print(f"- no Factorio at {os.environ['FACTORIO']}, aborting")
        return

    # Check CI succeeded if applicable
    ci_configured = os.path.isdir(os.path.join(ROOT, ".github", "workflows"))
    if ci_configured:
        CI_status = subprocess.run([
            "gh", "run", "list",
            "--branch", "master",
            "--limit", "1",
            "--json", "conclusion",
            "--jq", ".[0].conclusion"
        ], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        if CI_status != "success":
            print(f"Latest CI run did not succeed (status: {CI_status}), aborting")
            return

    # Determine the next mod version
    modfiles_path = ROOT / "modfiles"
    with INFO_PATH.open("r") as file:
        info_data = json.load(file)
    split_old_mod_version = info_data["version"].split(".")
    split_old_mod_version[-1] = str(int(split_old_mod_version[-1]) + 1)  # update version to the new one
    new_mod_version = ".".join(split_old_mod_version)

    # Bump info.json version
    info_data["version"] = new_mod_version
    with INFO_PATH.open("w", newline="\n") as file:
        json.dump(info_data, file, indent=4)
    print("- info.json version bumped")

    # Prepare changelog file
    tmp_path = modfiles_path / "tmp"
    old_changelog_path = modfiles_path / "changelog.txt"
    with tmp_path.open("w", newline="\n") as new_file, old_changelog_path.open("r") as old_file:
        # Find the strings corresponding to eventual empty categories (this is silly)
        empty_categories = re.findall(r"  [\w]+:\n(?!    - )", old_file.read())
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
                elif line not in empty_category_dict:
                    new_file.write(line)

    old_changelog_path.unlink()
    new_changelog_path = modfiles_path / "changelog.txt"
    tmp_path.rename(new_changelog_path)
    print("- changelog updated for release")

    # Update LICENSE year if necessary
    mod_license_path = ROOT / "LICENSE.md"
    current_year = datetime.today().year
    notice_regex = r"Copyright \(c\) [0-9]{4}"
    updated_license_text = re.sub(notice_regex, f"Copyright (c) {current_year}", mod_license_path.read_text())
    mod_license_path.write_text(updated_license_text, newline="\n")
    print("- LICENSE year updated")

    # Copy relevant files to temporary folder
    full_mod_name = Path(f"{MODNAME}_{new_mod_version}")
    tmp_release_path = ROOT / full_mod_name
    ignore_patterns = shutil.ignore_patterns('.*', 'tmp')
    shutil.copytree(modfiles_path, tmp_release_path, ignore=ignore_patterns)
    print("- relevant files copied")

    # Include LICENSE file
    shutil.copy(str(ROOT / "LICENSE.md"), str(tmp_release_path / "LICENSE.md"))
    print("- license file included")

    # Include up-to-date versions of foreign locales, if present
    foreign_locale_path = ROOT / "locale"
    release_locale_path = tmp_release_path / "locale"
    tmp_locale_license_path = release_locale_path / "LICENSE.md"

    if foreign_locale_path.exists():
        shutil.copy(str(foreign_locale_path / "LICENSE.md"), tmp_locale_license_path)

        locale_repo = repo.submodule("locale").module()
        locale_repo.git.checkout("master")
        locale_repo.git.pull()

        locale_list = []
        directory_list = [f for f in foreign_locale_path.rglob('./*') if f.is_dir()]
        for directory in directory_list:
            locale_name = directory.name
            locale_list.append(locale_name)
            locale_destination_path = release_locale_path / locale_name
            locale_destination_path.mkdir()
            shutil.copy(str(directory / "config.cfg"), str(locale_destination_path / "config.cfg"))
        print("- locale files updated")

    # ZIP up release files
    archive_path = shutil.make_archive(str(ROOT / full_mod_name), "zip", str(ROOT), str(tmp_release_path.parts[-1]))
    shutil.rmtree(tmp_release_path)
    print("- zip archive created")

    # Add a blank changelog entry for further development
    changelog_path = modfiles_path / "changelog.txt"
    new_changelog_entry = (("-" * 99) + "\nVersion: 0.00.00\nDate: 00. 00. 0000\n"
                           "  Features:\n  Changes:\n  Bugfixes:\n\n")
    updated_changelog = new_changelog_entry + changelog_path.read_text()
    changelog_path.write_text(updated_changelog, newline="\n")
    print("- blank changelog entry added")

    # Run screenshotter if requested and possible
    screenshotter_path = ROOT / "screenshots" / "automation"
    if take_screenshots and screenshotter_path.is_dir():
        # Swap in the screenshotter's mod-list, keeping the existing one to restore afterwards
        userdata_path = Path(os.environ["FACTORIO_USERDATA"]).expanduser()
        modlist_path = userdata_path / "mods" / "mod-list.json"
        saved_modlist = modlist_path.read_text() if modlist_path.exists() else None
        shutil.copy(str(screenshotter_path / "mod-list.json"), str(modlist_path))

        scenarios_path = modfiles_path / "scenarios"
        try:
            # Link the scenario folder for the game to find
            scenarios_path.mkdir(exist_ok=True)
            scenario_link = scenarios_path / "screenshotter"
            try:
                scenario_link.symlink_to(screenshotter_path / "scenario", target_is_directory=True)
            except OSError:  # Windows only permits symlinks when elevated
                shutil.copytree(screenshotter_path / "scenario", scenario_link)

            # Run the screenshotting scenario, waiting for it to signal it's done
            print("- taking screenshots...", end=" ", flush=True)
            with subprocess.Popen(
                [os.environ["FACTORIO"],
                "--load-scenario", f"{MODNAME}/screenshotter",
                "--config", str(screenshotter_path / "config.ini"),
                "--instrument-mod", MODNAME,  # use the same mod as the instrument mod for simplicity
                "--disable-migration-window"
                ], stdout=subprocess.PIPE, bufsize=1, universal_newlines=True
            ) as factorio:
                if factorio.stdout is not None:
                    for line in factorio.stdout:
                        if line.strip() == "screenshotter_done":
                            factorio.terminate()
            print("done")

            # Load metadata from generated JSON file
            script_output_path = userdata_path / "script-output"
            with (script_output_path / "metadata.json").open("r") as file:
                frame_corners = json.load(file)["frame_corners"]
            print("- metadata loaded")

            # Clear previous screenshots
            screenshots_path = ROOT / "screenshots"
            for screenshot in screenshots_path.iterdir():
                if screenshot.is_file():
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

            # Clean up only what this run produced, leaving the rest of script-output alone
            (script_output_path / "metadata.json").unlink()
            for scene in frame_corners:
                (script_output_path / f"{scene}.png").unlink()
        finally:
            shutil.rmtree(scenarios_path, ignore_errors=True)
            if saved_modlist is not None:
                modlist_path.write_text(saved_modlist, newline="\n")

    # Commit changes
    repo.git.add("-A")
    repo.git.reset("HEAD", "--", archive_path)
    repo.git.commit(m=f"Release {new_mod_version}")
    print("- changes committed")

    if RELEASE:
        # Create tag
        tag_name = f"v{new_mod_version}"
        with new_changelog_path.open("r") as file:
            section = re.split(r"^-{99}$", file.read(), flags=re.MULTILINE)[2]
        message = ""
        for line in section.strip().splitlines()[2:]:
            if line.startswith("    - "):
                message += f"{line.strip()}\n"
            else:
                message += f"### {line.strip()}\n"
        repo.create_tag(tag_name, message=message)
        print("- tag created")

        # Push commits & tags to Github
        print("- pushing to Github...", end=" ", flush=True)
        repo.git.push("origin")
        repo.git.push("--tags")
        print("done")

        # Create Github release
        print("- creating Github release...", end=" ", flush=True)
        subprocess.run([
            "gh", "release", "create", tag_name,
            "--title", f"{info_data["title"]} {new_mod_version}",
            "--notes-from-tag",
        ], cwd=ROOT, stdout=subprocess.DEVNULL)
        subprocess.run([
            "gh", "release", "upload", tag_name,
            archive_path
        ], cwd=ROOT, stdout=subprocess.DEVNULL)
        print("done")

        # Publish to mod portal
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

        print("- publishing to mod portal...", end=" ", flush=True)
        UPLOAD_API_URL = "https://mods.factorio.com/api/v2/mods/releases/init_upload"
        UPLOAD_API_KEY = os.environ["MOD_UPLOAD_API_KEY"]
        upload_data(UPLOAD_API_URL, UPLOAD_API_KEY, archive_path, "file")
        print("done")

        # Announce the release on Discord, linking issue references as Github does
        print("- posting to Discord...", end=" ", flush=True)
        source_url = repo.remotes.origin.url.removesuffix(".git")
        thumbnail_url = f"{source_url}/raw/master/modfiles/thumbnail.png"
        description = re.sub(r"#(\d+)", rf"[#\1]({source_url}/issues/\1)", message)
        try:
            response = requests.post(os.environ["MOD_DISCORD_WEBHOOK"], timeout=10, json={
                "username": info_data["title"],
                "embeds": [{
                    "title": f"Version {new_mod_version}",
                    "url": f"https://mods.factorio.com/mod/{MODNAME}",
                    "color": 0x3498DB,
                    "description": description[:4096],
                    "thumbnail": {"url": thumbnail_url}
                }]
            })
            print("done" if response.ok else f"failed: {response.text}")
        except requests.RequestException as error:  # a published release must not fail on this
            print(f"failed: {error}")

        # Update mod portal screenshots if requested
        if take_screenshots:
            IMAGE_API_URL = "https://mods.factorio.com/api/v2/mods/images"
            EDIT_API_KEY = os.environ["MOD_EDIT_API_KEY"]

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
            for screenshot_path in sorted(p for p in screenshots_path.iterdir() if p.is_file()):
                upload_data(f"{IMAGE_API_URL}/add", EDIT_API_KEY, str(screenshot_path), "image")
            print("done")

    if not LOCAL:
        Path(archive_path).unlink()

    print(f"Version {new_mod_version} released!")


if __name__ == "__main__":
    if LOCAL:
        publish_release(False)
    else:
        screenshots = input("Update screenshots? (y/n): ")
        publish_release(screenshots == "y")
