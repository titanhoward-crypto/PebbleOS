# Assets for PebbleOS

Place the following files here (they will be copied into the live system during build if you add a corresponding hook or manually copy them into config/includes.chroot):

- wallpapers/default.jpg          – main desktop & greeter background (1920×1080 recommended)
- wallpapers/*.jpg                – additional wallpapers
- logo/pebble-logo.png            – logo for GRUB / Plymouth / about dialog
- icons/                          – custom application icons (PNG/SVG)
- sounds/startup.ogg              – optional startup sound
- sounds/*.ogg                    – notification sounds

Example generation of a default wallpaper (requires ImageMagick):

  convert -size 1920x1080 gradient:'#2c3e50-#3498db' wallpapers/default.jpg

Then copy into the includes tree:

  mkdir -p ../config/includes.chroot/usr/share/backgrounds/pebbleos
  cp wallpapers/default.jpg ../config/includes.chroot/usr/share/backgrounds/pebbleos/
