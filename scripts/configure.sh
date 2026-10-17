#!/bin/bash
# PebbleOS live-build configuration script
set -e

DISTRO=${DISTRO:-bookworm}
ARCH=${ARCH:-amd64}

# Clean previous config if present (safe for re-runs)
if [ -d config ]; then
  echo "Using existing config/ tree (hooks & includes already present)"
else
  echo "Initializing live-build config..."
fi

lb config \
  --mode debian \
  --distribution "$DISTRO" \
  --architectures "$ARCH" \
  --binary-images iso-hybrid \
  --debian-installer none \
  --archive-areas "main contrib non-free non-free-firmware" \
  --bootappend-live "boot=live components quiet splash hostname=pebbleos username=pebble user-fullname=Pebble User locales=en_US.UTF-8 keyboard-layouts=us timezone=UTC" \
  --bootappend-live-failsafe "boot=live components memtest noapic noapm nodma nomce nolapic nomodeset nosmp nosplash vga=normal" \
  --iso-application "PebbleOS" \
  --iso-publisher "PebbleOS Project" \
  --iso-volume "PebbleOS" \
  --memtest none \
  --firmware-binary true \
  --firmware-chroot true \
  --linux-flavours "amd64" \
  --linux-packages "linux-image" \
  --apt-indices false \
  --apt-recommends true \
  --security true \
  --updates true \
  --backports false \
  --mirror-bootstrap "http://deb.debian.org/debian/" \
  --mirror-chroot "http://deb.debian.org/debian/" \
  --mirror-binary "http://deb.debian.org/debian/" \
  --parent-mirror-bootstrap "http://deb.debian.org/debian/" \
  --parent-mirror-chroot "http://deb.debian.org/debian/" \
  --parent-mirror-binary "http://deb.debian.org/debian/" \
  --debootstrap-options "--variant=minbase --include=apt-utils" \
  --uefi-secure-boot disable \
  "${@}"

# Ensure our package list is the active one
if [ ! -f config/package-lists/pebble.list.chroot ]; then
  if [ -f config/package-lists/stage4.list.chroot ]; then
    cp config/package-lists/stage4.list.chroot config/package-lists/pebble.list.chroot
  fi
fi

echo "Configuration complete. Run 'make build' (or sudo lb build) next."
