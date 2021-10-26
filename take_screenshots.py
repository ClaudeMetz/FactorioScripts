import json
import shutil
import subprocess
import sys
from pathlib import Path

import git  # type: ignore
from PIL import Image  # type: ignore

# Script config
MODNAME = sys.argv[1]
FACTORIO_PATH = sys.argv[2]
USERDATA_PATH = sys.argv[3]

cwd = Path.cwd()
repo = git.Repo(cwd)

def take_screenshots():
    screenshotter_path =  cwd / "scenarios" / "screenshotter"
    if not screenshotter_path.is_dir():
        print("- no screenshotter scenario found, aborting")
        return

    # Overwrite mod-list.json with the one found in the scenarios folder
    current_modlist_path = Path(USERDATA_PATH) / "mods" / "mod-list.json"
    current_modlist_path.unlink(missing_ok=True)
    shutil.copy(str(screenshotter_path / "mod-list.json"), str(current_modlist_path))
    print("- mod-list.json replaced")

    # Run the screenshotting scenario, waiting for it to finish
    print("- running scenario ...", end=" ", flush=True)
    subprocess.run([
        "/usr/bin/open", "-W", "-a", FACTORIO_PATH, "--args",
        "--load-scenario", "{}/screenshotter".format(MODNAME),
        "--config", str(screenshotter_path / "config.ini"),
        "--instrument-mod", MODNAME  # use the same mod as the instrument mod for simplicity
        ]
    )
    print("done")

    # Crop screenshots according to the given dimensions
    script_output_path = Path(USERDATA_PATH, "script-output")
    with (script_output_path / "dimensions.json").open("r") as file:
        dimensions = json.load(file)

    for scene, corners in dimensions.items():
        screenshot_path = script_output_path / "{}.png".format(scene)
        image = Image.open(screenshot_path)

        cropped_img = image.crop((
            corners["top_left"]["x"] - 15,
            corners["top_left"]["y"] - 15,
            corners["bottom_right"]["x"] + 15,
            corners["bottom_right"]["y"] + 15
        ))
        cropped_img.save(cwd / "screenshots" / "{}.png".format(scene))
    print("- screenshots updated")

    # Clean up script output
    shutil.rmtree(script_output_path)
    print("- script-output removed")

    # Commit new screenshots
    repo.git.add("-A")
    repo.git.commit(m="Update screenshots")
    print("- changes committed")


if __name__ == "__main__":
    proceed = input(f"[{MODNAME}] Sure to take screenshots? (y/n): ")
    if proceed == "y":
      take_screenshots()
