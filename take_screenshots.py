import json
import os
import shutil
import subprocess
import sys
from pathlib import Path, PosixPath

import requests
from git import Repo
from PIL import Image  # type: ignore

# Script config
MODNAME = sys.argv[1]
FACTORIO_PATH = sys.argv[2]
USERDATA_PATH = PosixPath(sys.argv[3]).expanduser()
RELEASE = (len(sys.argv) == 5 and sys.argv[4] == "--release")

cwd = Path.cwd() / ".."  # back out of scripts folder
repo = Repo(cwd)

def take_screenshots() -> None:
    if RELEASE and repo.active_branch.name != "master":
        print("- not on master branch, aborting")
        return
    if RELEASE and repo.is_dirty():
        print("- repository is dirty, aborting")
        return

    screenshotter_path =  cwd / "scenarios" / "screenshotter"
    if not screenshotter_path.is_dir():
        print("- no screenshotter scenario found, aborting")
        return

    # Overwrite mod-list.json with the one found in the scenarios folder
    current_modlist_path = USERDATA_PATH / "mods" / "mod-list.json"
    current_modlist_path.unlink(missing_ok=True)
    shutil.copy(str(screenshotter_path / "mod-list.json"), str(current_modlist_path))
    print("- mod-list.json replaced")

    # Run the screenshotting scenario, waiting for it to finish
    print("- running scenario...", end=" ", flush=True)
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
        metadata = json.load(file)
        frame_corners = metadata["frame_corners"]
        protected_names = [f"{name}.png" for name in metadata["protected_names"]]
    print("- metadata loaded")

    # Clear previous screenshots
    screenshots_path = cwd / "screenshots"
    for screenshot in screenshots_path.iterdir():
        if screenshot.name not in protected_names:
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

    # Commit new screenshots
    repo.git.add("-A")
    repo.git.commit(m="Update screenshots")
    print("- changes committed")

    if RELEASE:
        IMAGE_API_URL = "https://mods.factorio.com/api/experimental/mods/images"
        apikey = os.getenv("MOD_EDIT_API_KEY")

        # Remove old mod portal images
        print("- removing old mod portal images...", end=" ", flush=True)
        response = requests.post(
            f"{IMAGE_API_URL}/edit",
            data = {"mod": MODNAME, "images": []},
            headers = {"Authorization": f"Bearer {apikey}"}
        )
        if not response.ok:
            raise RuntimeError(f"edit failed: {response.text}")
        print("done")

        # Upload new mod portal images
        print("- uploading to mod portal...", end=" ", flush=True)
        for screenshot_path in sorted(screenshots_path.iterdir()):
            response = requests.post(
                f"{IMAGE_API_URL}/add",
                data = {"mod": MODNAME},
                headers = {"Authorization": f"Bearer {apikey}"}
            )
            if not response.ok:
                raise RuntimeError(f"init_upload failed: {response.text}")

            upload_url = response.json()["upload_url"]
            with open(screenshot_path, "rb") as file:
                response = requests.post(upload_url, files={"image": file})
                if not response.ok:
                    raise RuntimeError(f"upload failed: {response.text}")
        print("done")


if __name__ == "__main__":
    proceed = input(f"[{MODNAME}] Sure to take screenshots? (y/n): ")
    if proceed == "y":
        take_screenshots()
