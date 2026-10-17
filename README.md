# PebbleOS

**PebbleOS** is a Windows-style desktop operating system delivered as a bootable live ISO (`pebbleos.iso`).  
It is based on Debian (stable/bookworm or later) with a heavily customized XFCE desktop environment, branded look-and-feel, and a curated set of applications presented under Pebble names.

## What is custom vs. borrowed

| Component | Source | Notes |
|-----------|--------|-------|
| Kernel, init, networking, package manager | Debian | Unmodified |
| Bootloader (GRUB) | Debian + custom splash/config | Custom theme and menu text |
| Live system infrastructure | live-boot / live-config | Standard |
| Window manager / desktop | XFCE 4.x | Heavily themed & configured for bottom taskbar, Start menu (Whisker), rounded corners via CSS/theme |
| Login manager | LightDM + greeter | Custom branding |
| File manager | Thunar (as "Pebble Files") | Custom .desktop + icons + sidebar defaults |
| Text editor | Mousepad / Leafpad (as "Pebble Notes") | Custom branding |
| Browser | Firefox ESR (as "Pebble Browser") | Custom profile defaults + bookmarks |
| Terminal | XFCE Terminal (as "Pebble Terminal") | Custom |
| Settings | XFCE Settings + custom wrappers | Wallpaper, theme, display, users, date/time, network |
| Calculator | GNOME Calculator or galculator | Mode switch |
| Paint | Pinta or simple Python/Tk app | Drawing + PNG save |
| Media | VLC / mpv | Music & video |
| Photos | Ristretto / Eye of XFCE | Slideshow |
| Task Manager | XFCE Task Manager / htop wrapper | CPU/RAM + end task |
| Calendar/Clock | Orage + custom applet | Alarms/timer/stopwatch via scripts |
| Store | Simple script listing packages or flatpak | "Extra apps" installer |
| Games | Mines (GNOME), Aisleriot (Solitaire), custom Snake | Packaged or simple scripts |
| Icons, wallpapers, sounds, logo | Custom assets | Gray/blue palette, rounded style |
| Guest Additions | VirtualBox guest additions (installable) | For screen resize, shared folders, etc. |

The project is intentionally **not** a from-scratch kernel or compositor. Building a production-quality OS from zero is a multi-year effort. This delivers a polished, bootable, branded desktop experience that matches the requested feature list as closely as practical.

## Project layout

```
pebbleos/
├── README.md                 # This file
├── Makefile                  # High-level build targets
├── auto/                     # live-build auto scripts (generated/edited)
├── config/
│   ├── package-lists/        # Packages to install
│   ├── hooks/                # Chroot and binary hooks
│   ├── includes.chroot/      # Files copied into the live filesystem
│   └── includes.binary/      # Files for the ISO (GRUB, isolinux)
├── assets/                   # Source wallpapers, icons, logo, sounds
├── scripts/                  # Helper scripts
├── docs/                     # Build & VirtualBox instructions, limitations, roadmap
└── apps/                     # Optional pure-Python/simple custom app sources
```

## Quick start (build machine)

1. Use a Debian or Ubuntu host with ≥ 4 GB RAM and ≥ 20 GB free disk.
2. Install dependencies (see `docs/BUILD.md`).
3. `cd pebbleos && make config && make build`
4. Result: `pebbleos.iso` (hybrid, BIOS + UEFI).

Detailed instructions are in `docs/`.

## Testing stages

The configuration is structured so you can build incrementally:

1. **Stage 1 – Boot + desktop**  
   Minimal package list + LightDM + XFCE. Test: ISO boots to graphical login and desktop.

2. **Stage 2 – Window manager & taskbar**  
   Panel config, Whisker menu, window decorations, Alt-Tab, lock screen. Test: drag/resize windows, Start menu, system tray, clock.

3. **Stage 3 – Core apps**  
   Files, Notes, Settings. Test: open/save, wallpaper change, theme switch.

4. **Stage 4 – Remaining apps + polish**  
   Browser, Terminal, Calculator, Paint, Media, Photos, Task Manager, Calendar, Store, Games. Test full workflow.

See `docs/STAGES.md` for the exact package/hook changes between stages.

## License & credits

- Debian packages: their respective licenses (mostly DFSG-free).
- PebbleOS branding, configs, scripts, and custom assets: provided as-is for this project (you may reuse/modify).
- Inspired by many live-build tutorials and XFCE theming communities.
