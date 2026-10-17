# Running PebbleOS in VirtualBox

## Recommended VM settings

| Setting              | Value                          | Notes |
|----------------------|--------------------------------|-------|
| Type                 | Linux                          | |
| Version              | Debian (64-bit)                | or "Other Linux (64-bit)" |
| Memory (RAM)         | 2048 MB (minimum 1024)         | 4096 MB recommended for comfort |
| CPUs                 | 2                              | 1 is acceptable |
| Video Memory         | 128 MB                         | Enable 3D Acceleration if available |
| Graphics Controller  | VBoxSVGA or VMSVGA             | VMSVGA works well with Guest Additions |
| Storage              | Optical drive → select `pebbleos.iso` | Controller: IDE or SATA |
| Network              | NAT (default)                  | Bridged if you need LAN access |
| Audio                | Intel HD Audio                 | Optional |
| USB                  | USB 2.0 or 3.0 controller      | Optional |

## Step-by-step

1. Open VirtualBox → **New**.
2. Name: `PebbleOS`, Type: Linux, Version: Debian (64-bit).
3. Allocate RAM (2048+ MB) and create a virtual hard disk if you plan to install later (or use a small one for live testing).
4. After creation, go to **Settings → System**:
   - Motherboard: enable EFI if you want UEFI boot (optional; the ISO is hybrid).
   - Processor: 2 CPUs, enable PAE/NX if shown.
5. **Settings → Display**:
   - Video Memory: 128 MB.
   - Graphics Controller: VBoxSVGA or VMSVGA.
   - Optional: Enable 3D Acceleration.
6. **Settings → Storage**:
   - Under the optical drive, click the disk icon → **Choose a disk file…** → select `pebbleos.iso`.
7. Start the VM.

## First boot

- GRUB menu appears with “PebbleOS”.
- After a short splash the LightDM login screen appears.
- Default credentials:
  - **Username:** `pebble`
  - **Password:** `pebble`
- Root password is also `pebble` (for emergency use).

## After login

- You should see a desktop with bottom taskbar, Whisker (Start) menu, desktop icons, and system tray/clock.
- Open **Pebble Settings** to change wallpaper or switch light/dark theme (Arc theme is pre-installed).
- For best experience install VirtualBox Guest Additions:
  1. In the running VM menu: Devices → Insert Guest Additions CD image…
  2. Open a terminal and run:
     ```bash
     sudo mount /dev/cdrom /mnt
     cd /mnt
     sudo ./VBoxLinuxAdditions.run
     ```
  3. Reboot the guest. Screen resize, shared clipboard, and shared folders will then work.

## Persistence (optional)

To keep files across reboots, create a second virtual disk, format it with a filesystem labeled `persistence`, and create a `/persistence.conf` file containing `/ union`. Then boot the “Persistence enabled” GRUB entry. See the Debian live-manual for full details.

## Troubleshooting

- Black screen / no GUI: try the Failsafe GRUB entry or lower the video memory / disable 3D.
- Slow graphics: install Guest Additions as above.
- Network not working: ensure NetworkManager is running (`sudo systemctl status NetworkManager`).
- Keyboard layout wrong: change it in Settings → Keyboard or add `keyboard-layouts=xx` to the boot parameters.
