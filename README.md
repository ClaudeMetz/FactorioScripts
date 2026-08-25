# Modding scripts

Two helpers: one cuts a release, the other scaffolds a migration. Both work out their paths
relative to themselves, so it doesn't matter which directory you run them from.

```sh
uv run --project scripts scripts/build_release.py [--local | --release]
uv run --project scripts scripts/new_migration.py
```

## Required environment variables

- `FACTORIO` - the Factorio executable.
- `FACTORIO_USERDATA` - the directory that holds `mods/` and `script-output/`.
- `MOD_UPLOAD_API_KEY` - a factorio.com API key with the *Upload Mods* scope.
- `MOD_EDIT_API_KEY` - a factorio.com API key with the *Edit Mods* scope, used to replace the
  screenshots on the mod portal.

The two keys are only needed for `--release`, and the two paths only when the run takes
screenshots. `new_migration.py` needs none of them.
