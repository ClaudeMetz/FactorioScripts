# Release script

`build_release.py` cuts a release via the command below.

```sh
uv run --project scripts scripts/build_release.py [--local | --release]
```

## Environment variables

- `FACTORIO` is the Factorio executable.
- `FACTORIO_USERDATA` is the directory that holds `mods/` and `script-output/`.
- `MOD_UPLOAD_API_KEY` is a factorio.com API key with the *Upload Mods* scope.
- `MOD_EDIT_API_KEY` is a factorio.com API key with the *Edit Mods* scope, used to replace the
  screenshots on the mod portal.
- `MOD_DISCORD_WEBHOOK` is the webhook that release announcements get posted to.

The two keys and the webhook are only needed for `--release`, and the two paths only when the
run takes screenshots.
