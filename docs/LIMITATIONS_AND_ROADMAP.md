# Known Limitations & Roadmap

## Known Limitations (current design)

1. **Not a from-scratch OS**  
   PebbleOS is a branded Debian live system with a customized XFCE desktop. It does not contain a custom kernel, custom compositor, or custom system libraries written for this project.

2. **Window decorations & rounded corners**  
   Rounded corners and some visual polish depend on the GTK/XFCE theme (Arc is used). True Windows-11-style acrylic/mica effects or client-side decorations would require a different compositor (e.g. KWin or a Wayland compositor) and more custom CSS/theme work.

3. **App rebranding is surface-level**  
   Most “Pebble …” applications are existing Debian packages with custom `.desktop` files and icons. Deep UI changes (e.g. completely rewriting the file manager chrome) are not present.

4. **Pebble Store**  
   Currently a simple informational dialog / script. A full graphical store would need integration with `gnome-software`, Discover, or a custom Python/Qt frontend plus Flatpak/AppImage support.

5. **Games**  
   Minesweeper and Solitaire come from GNOME/Aisleriot. Snake is a small pure-Python Tkinter game included in the tree. No advanced graphics or sound effects.

6. **Login / lock screen**  
   LightDM + light-locker provide basic login and lock. A fully custom animated lock screen or biometric support is not implemented.

7. **Installer**  
   The ISO is live-only by default (`--debian-installer none`). Adding Calamares or the Debian installer is straightforward but not enabled out of the box.

8. **Multi-language / accessibility**  
   Defaults to US English. Additional locales and accessibility tools can be added via the package list and live-config parameters.

9. **Security model**  
   Live user has passwordless sudo (typical for live media). For a production install you would tighten this.

10. **Resource usage**  
    XFCE is lightweight, but a full package set still needs ~1–1.5 GB RAM at idle. Very low-end machines may prefer a further-stripped stage1/stage2 build.

## Roadmap (future improvements)

### Short term
- [ ] Proper splash / Plymouth theme with Pebble logo
- [ ] High-quality wallpapers and a complete icon set matching the gray/blue palette
- [ ] Startup sound and system notification sounds
- [ ] Better Whisker menu configuration (favorites, categories named after Pebble apps)
- [ ] Calamares installer with Pebble branding for optional hard-disk install
- [ ] Persistence documentation and a helper script

### Medium term
- [ ] Custom GTK/XFCE theme (or CSS overrides) for more pronounced rounded corners and Windows-like title bars
- [ ] Simple Python-based “Pebble Settings” front-end that groups wallpaper, theme, display, users, datetime, network
- [ ] Improved Pebble Store (list packages, one-click apt/flatpak install)
- [ ] More polished Snake / additional small games
- [ ] Default Firefox profile with Pebble bookmarks and start page
- [ ] Automatic Guest Additions detection / helper

### Longer term
- [ ] Optional Wayland session (labwc or Wayfire) for modern effects
- [ ] Flatpak-first application model with a curated set of sandboxed apps
- [ ] Immutable / A/B update mechanism (e.g. based on ostree or a simple snapshot scheme)
- [ ] Official website + download mirrors
- [ ] Community themes and “Pebble Store” repository of extra packages

## Testing checklist (after each stage)

- [ ] ISO boots in VirtualBox (BIOS and, if enabled, UEFI)
- [ ] GRUB shows “PebbleOS”
- [ ] Login screen appears; credentials `pebble` / `pebble` work
- [ ] Desktop loads with wallpaper and bottom panel
- [ ] Start menu (Whisker) opens and launches applications
- [ ] Windows can be dragged, resized, minimized, maximized, closed
- [ ] Alt+Tab switches applications
- [ ] Lock screen works (light-locker or xscreensaver)
- [ ] Clock / date visible in the tray
- [ ] NetworkManager can obtain an IP (NAT)
- [ ] Guest Additions install and enable screen resize
- [ ] Each Pebble-named application launches and performs its basic function
- [ ] Recycle Bin / Trash works from the file manager
- [ ] Theme can be switched between light and dark variants of Arc
