# PebbleOS Makefile
# Requires: live-build, debootstrap, xorriso, squashfs-tools, etc. (see docs/BUILD.md)

ISO_NAME = pebbleos
DISTRO   = bookworm
ARCH     = amd64
LB       = lb

.PHONY: all config clean build iso help stage1 stage2 stage3 stage4

all: build

help:
	@echo "PebbleOS build targets:"
	@echo "  make config   - Run lb config with PebbleOS settings"
	@echo "  make build    - Build the full ISO (calls lb build)"
	@echo "  make clean    - Clean build artifacts"
	@echo "  make stage1   - Minimal boot + desktop (for early testing)"
	@echo "  make stage2   - + window manager / taskbar polish"
	@echo "  make stage3   - + Files, Notes, Settings"
	@echo "  make stage4   - Full package set + apps"
	@echo "  make iso      - Alias for build; renames output to pebbleos.iso"

config:
	./scripts/configure.sh

build: config
	sudo $(LB) build 2>&1 | tee build.log
	@if [ -f live-image-$(ARCH).hybrid.iso ]; then \
		mv -f live-image-$(ARCH).hybrid.iso $(ISO_NAME).iso; \
		echo "Created $(ISO_NAME).iso"; \
		ls -lh $(ISO_NAME).iso; \
	elif [ -f live-image-$(ARCH).iso ]; then \
		mv -f live-image-$(ARCH).iso $(ISO_NAME).iso; \
		echo "Created $(ISO_NAME).iso"; \
	else \
		echo "ISO not found – check build.log"; \
		exit 1; \
	fi

iso: build

clean:
	sudo $(LB) clean --purge || true
	rm -f build.log $(ISO_NAME).iso *.iso
	rm -rf .build cache chroot binary || true

# Convenience stage targets simply copy different package lists then rebuild.
# Edit config/package-lists/ before calling these if you want finer control.
stage1:
	cp config/package-lists/stage1.list.chroot config/package-lists/pebble.list.chroot
	$(MAKE) build

stage2:
	cp config/package-lists/stage2.list.chroot config/package-lists/pebble.list.chroot
	$(MAKE) build

stage3:
	cp config/package-lists/stage3.list.chroot config/package-lists/pebble.list.chroot
	$(MAKE) build

stage4:
	cp config/package-lists/stage4.list.chroot config/package-lists/pebble.list.chroot
	$(MAKE) build
