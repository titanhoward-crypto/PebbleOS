# Incremental Build Stages

Use the Makefile targets `make stage1` … `make stage4` (or manually swap the package list) to build and test progressively.

## Stage 1 – Boot the ISO and show a desktop

**Goal:** GRUB → kernel → graphical login → basic XFCE desktop.

**Packages:** live-boot, live-config, Xorg, LightDM, minimal XFCE (panel, terminal, Thunar, Mousepad), NetworkManager, basic firmware.

**Test:**
1. Boot the ISO in VirtualBox.
2. See the GRUB menu with “PebbleOS”.
3. Reach the LightDM login screen.
4. Log in as `pebble` / `pebble`.
5. Confirm a desktop appears (even if unpolished).

## Stage 2 – Window manager and taskbar

**Goal:** Bottom taskbar, Start-style menu (Whisker), system tray, clock, window controls, lock screen, Guest Additions packages, theming.

**Added packages:** xfce4-whiskermenu-plugin, xfce4-goodies, pulseaudio plugin, datetime plugin, light-locker, Arc theme, Papirus icons, virtualbox-guest-*, etc.

**Test:**
1. Bottom panel present with menu, task list, tray, clock.
2. Whisker menu opens and shows applications.
3. Windows can be moved, resized, min/max/close.
4. Alt+Tab works.
5. Lock screen activates (Super+L or from the menu).
6. Theme looks coherent (gray/blue via Arc).

## Stage 3 – Files, Notes, Settings

**Goal:** Fully usable file manager, text editor, and settings center.

**Added packages:** Thunar plugins, archive support, gvfs, policykit, full XFCE settings modules.

**Test:**
1. Open Pebble Files – browse folders, copy/paste/rename/delete, use sidebar and Trash.
2. Open Pebble Notes – create, edit, save a text file.
3. Open Pebble Settings – change wallpaper, switch light/dark theme, adjust display, check user account info, set date/time, manage network.

## Stage 4 – Remaining applications

**Goal:** Complete application set matching the project brief.

**Added packages:** Firefox ESR, GNOME Calculator / galculator, Pinta, VLC/mpv, Ristretto, Orage, gnome-mines, aisleriot, Python3 + Tk for Snake, Flatpak helpers, etc.

**Test:**
1. Launch every Pebble-branded application from the menu or desktop.
2. Browser opens with tabs; bookmarks can be added.
3. Calculator switches between basic and scientific modes.
4. Paint can draw and export PNG.
5. Media plays audio/video.
6. Photos shows images and can start a slideshow.
7. Task Manager lists processes and can end a task.
8. Calendar shows dates; basic alarm/timer functionality via Orage or scripts.
9. Pebble Store shows the demo message / package list.
10. Games (Minesweeper, Solitaire, Snake) are playable.

After Stage 4 the ISO is considered feature-complete for the initial release.
