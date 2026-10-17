# Building the PebbleOS ISO

Everything needed is in this folder. Pick ONE way:

## A) On Windows with WSL (build on your own PC)
1. Open an **admin** PowerShell and run:  `wsl --install -d Debian`
   Reboot if asked, then open "Debian" once and create a username/password.
2. Make sure Python is installed (python.org, tick "Add python.exe to PATH").
3. Unzip this folder somewhere with ~20 GB free on C:, then double-click **build_iso.bat**.
   (Options: `build_iso.bat --stage 1` for a quick minimal build.)
4. Takes ~30-60 min. Result: `pebbleos.iso` (+ `pebbleos-build.log`) in this folder.

## B) On GitHub (build in the cloud, nothing to install)
1. Create a new repo at github.com/new (public = free build minutes + storage).
2. **Add file -> Upload files**: upload everything in this folder
   (including the hidden `.github` folder, `.gitattributes` and `.gitignore`).
   If `.github` won't upload, use **Add file -> Create new file**, name it
   `.github/workflows/build-iso.yml` and paste in that file's contents.
3. **Actions** tab -> "Build PebbleOS ISO" -> **Run workflow**.
4. When done (~40-90 min), download `pebbleos-iso` from the run's Artifacts section.
   Push a tag like `v0.1` to publish it as a Release instead.

## Using the ISO
Boot it in VirtualBox / VMware / QEMU (or write it to USB with Rufus / balenaEtcher).
Login: `pebble` / `pebble`.

## What build_iso.py fixes automatically (your source files are never edited)
missing exec bits, CRLF line endings, live-build merging every stage package list,
package names that don't exist in Debian 12 (dropped or replaced: xfdesktop->xfdesktop4,
pinta->drawing), and the empty wallpaper (adds imagemagick).

## Troubleshooting
- "no Linux distro" / "running under WSL1" / "not Debian": the script prints the exact fix.
- "something is still mounted": run `wsl --shutdown` in PowerShell, then retry.
- Build fails: open `pebbleos-build.log` and look at the last ~30 lines.
