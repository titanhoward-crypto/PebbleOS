# Building PebbleOS

## Host requirements

- Debian 12 (bookworm) or Ubuntu 22.04/24.04 (or any recent Debian derivative)
- At least **4 GB RAM** (8 GB recommended)
- At least **20 GB free disk space** (the build tree grows significantly)
- Internet connection (packages are downloaded during the build)
- Root/sudo privileges

## 1. Install build tools

On Debian / Ubuntu:

```bash
sudo apt update
sudo apt install -y live-build debootstrap xorriso squashfs-tools \
  grub-pc-bin grub-efi-amd64-bin mtools dosfstools \
  isolinux syslinux-common \
  git curl ca-certificates
```

Optional but useful:

```bash
sudo apt install -y qemu-system-x86 qemu-utils   # for local testing
```

## 2. Obtain the PebbleOS source

Copy or clone the `pebbleos/` directory to your build machine.

```bash
cd /path/to/pebbleos
```

## 3. (Optional) Add assets

Place custom wallpapers, icons, logo, and sounds into:

- `assets/wallpapers/` → will be copied to `/usr/share/backgrounds/pebbleos/`
- `assets/icons/`
- `assets/logo/`
- `assets/sounds/`

A simple solid-color or gradient wallpaper named `default.jpg` is expected by the greeter and desktop configs. You can generate one with ImageMagick:

```bash
# Example 1920x1080 blue-gray gradient
convert -size 1920x1080 gradient:'#2c3e50-#3498db' assets/wallpapers/default.jpg
# Then copy into the includes tree before building
mkdir -p config/includes.chroot/usr/share/backgrounds/pebbleos
cp assets/wallpapers/default.jpg config/includes.chroot/usr/share/backgrounds/pebbleos/
```

A simple PNG logo can be placed similarly.

## 4. Configure

```bash
make config
# or: ./scripts/configure.sh
```

This runs `lb config` with the PebbleOS options (Debian bookworm, amd64, hybrid ISO, live user `pebble`, etc.).

## 5. Build

```bash
make build
# or: sudo lb build 2>&1 | tee build.log
```

The process typically takes 15–45 minutes depending on network and CPU.  
When finished you should have `pebbleos.iso` in the project root.

## 6. Clean

```bash
make clean
```

## Stage-by-stage builds

To test incrementally:

```bash
make stage1   # minimal boot + desktop
# test the resulting ISO
make stage2   # + panel / Whisker / themes / guest additions
make stage3   # + Files / Notes / Settings polish
make stage4   # full application set
```

Each stage overwrites `config/package-lists/pebble.list.chroot` and rebuilds.

## Notes

- The first build downloads a large amount of packages; subsequent builds are faster if the cache is kept.
- If the build fails with mirror or key errors, try again later or change the mirror in `scripts/configure.sh`.
- For UEFI-only or BIOS-only testing you can adjust the bootloader options in the config script.
- VirtualBox Guest Additions packages are included so that once the guest is running you can install the full Guest Additions ISO from the VirtualBox menu for optimal video/clipboard/shared-folder support.
