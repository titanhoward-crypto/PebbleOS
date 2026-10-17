#!/usr/bin/env python3
"""
build_iso.py - build the PebbleOS ISO from Windows using WSL2 (Debian live-build).

    python build_iso.py                      # finds pebbleos-source.zip or ./pebbleos next to you
    python build_iso.py pebbleos-source.zip -o C:\\Users\\me\\Desktop
    python build_iso.py --stage 1            # quick minimal build for testing
    python build_iso.py --prepare-only       # just show what would be patched; don't touch WSL

What it does
  1. Checks WSL2 + a Debian distro, installs live-build & friends inside it.
  2. Loads your source (zip or folder) in memory and fixes things that break builds
     under WSL (CRLF endings, missing exec bits, bad package names, empty wallpaper).
     Your zip/folder is never modified.
  3. Ships the cleaned tree into WSL's own ext4 disk (NOT /mnt/c - live-build can't
     build on NTFS mounts), runs scripts/configure.sh + `lb build` as root.
  4. Copies pebbleos.iso (and the build log) back to the output folder.
"""
from __future__ import annotations

import argparse
import atexit
import io
import lzma
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import types
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

DEFAULT_BUILD_DIR = "/root/pebbleos-build"      # lives on WSL's ext4 disk
COMPONENTS = ("main", "contrib", "non-free", "non-free-firmware")
HOST_DEPS = (
    "live-build debootstrap xorriso squashfs-tools grub-pc-bin grub-efi-amd64-bin "
    "grub-common mtools dosfstools isolinux syslinux syslinux-common gpgv "
    "ca-certificates debian-archive-keyring"
)
PKG_DIR = "config/package-lists/"
WALLPAPER_DST = "config/includes.chroot/usr/share/backgrounds/pebbleos/default.jpg"
WALLPAPER_SRC = "assets/wallpapers/default.jpg"
# Packages that don't exist in the target release -> a real replacement (used only if it exists)
SUBSTITUTES = {"xfdesktop": "xfdesktop4", "pinta": "drawing"}
# When a substitute is used, also fix launchers that call the old program
LAUNCHER_FIXES = {
    "pinta": ("config/includes.chroot/usr/share/applications/pebble-paint.desktop",
              "Exec=pinta", "Exec=drawing"),
}
SKIP_TOP = {".git", "__MACOSX", "chroot", "binary", "cache", ".build"}


def die(msg: str, code: int = 1):
    print(f"\nERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def info(msg: str):
    print(f"[pebble] {msg}", flush=True)


# --------------------------------------------------------------------------- #
# 1. Load + clean the source tree (all in memory)
# --------------------------------------------------------------------------- #
def _skip(rel: str) -> bool:
    parts = rel.split("/")
    return (
        parts[0] in SKIP_TOP
        or ".git" in parts
        or "__MACOSX" in parts
        or parts[-1] in (".DS_Store", "build.log")
        or rel.endswith(".iso")
        or ".." in parts
    )


def load_tree(src: Path) -> tuple[dict[str, bytes], set[str]]:
    files: dict[str, bytes] = {}
    dirs: set[str] = set()
    if src.is_file() and src.suffix.lower() == ".zip":
        with zipfile.ZipFile(src) as z:
            marker = "config/package-lists/"
            prefix = None
            for n in z.namelist():
                if marker in n:
                    prefix = n[: n.index(marker)]
                    break
            if prefix is None:
                die(f"{src.name} doesn't look like a live-build tree (no config/package-lists/).")
            for i in z.infolist():
                if not i.filename.startswith(prefix):
                    continue
                rel = i.filename[len(prefix):].rstrip("/")
                if not rel or _skip(rel):
                    continue
                if i.is_dir():
                    dirs.add(rel)
                else:
                    files[rel] = z.read(i)
    elif src.is_dir():
        root = src if (src / "config").is_dir() else next(
            (p for p in src.iterdir() if (p / "config").is_dir()), None)
        if root is None:
            die(f"{src} doesn't contain a config/ folder.")
        for p in sorted(root.rglob("*")):
            rel = p.relative_to(root).as_posix()
            if _skip(rel):
                continue
            if p.is_dir():
                dirs.add(rel)
            else:
                files[rel] = p.read_bytes()
    else:
        die(f"Source not found: {src}")
    if not any(k.startswith(PKG_DIR) for k in files):
        die("No package lists found under config/package-lists/.")
    return files, dirs


def is_text(b: bytes) -> bool:
    return b"\0" not in b[:8192]


def fix_line_endings(files: dict[str, bytes]) -> int:
    n = 0
    for k, v in files.items():
        if b"\r\n" in v and is_text(v):
            files[k] = v.replace(b"\r\n", b"\n")
            n += 1
    return n


# --------------------------------------------------------------------------- #
# 2. Package-list handling
# --------------------------------------------------------------------------- #
def select_stage(files: dict[str, bytes], stage: int) -> str:
    """live-build installs EVERY *.list.chroot, so keep exactly one active list."""
    lists = [k for k in files if k.startswith(PKG_DIR) and k.endswith(".list.chroot")]
    wanted = PKG_DIR + (f"stage{stage}.list.chroot" if stage != 4 else "pebble.list.chroot")
    if wanted not in files:
        wanted = PKG_DIR + f"stage{stage}.list.chroot"
    if wanted not in files:
        die(f"Package list for stage {stage} not found.")
    text = files[wanted].decode("utf-8")
    for k in lists:
        del files[k]
    return text


def fetch_available(mirror: str, suite: str) -> set[str] | None:
    names: set[str] = set()
    for comp in COMPONENTS:
        url = f"{mirror.rstrip('/')}/dists/{suite}/{comp}/binary-amd64/Packages.xz"
        info(f"  fetching package index: {suite}/{comp}")
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                text = lzma.decompress(r.read()).decode("utf-8", "replace")
        except (urllib.error.URLError, OSError, lzma.LZMAError) as e:
            info(f"  could not fetch {url} ({e}); skipping package validation")
            return None
        names.update(re.findall(r"^Package: (\S+)$", text, re.M))
        for prov in re.findall(r"^Provides: (.+)$", text, re.M):
            for item in prov.split(","):
                m = re.match(r"\s*([^\s(|]+)", item)
                if m:
                    names.add(m.group(1))
    return names


def filter_packages(text: str, available: set[str]):
    """Returns (new_text, removed, substituted{old: new})."""
    out, removed, subs = [], [], {}
    for line in text.splitlines():
        s_ = line.strip()
        if not s_ or s_.startswith("#"):
            out.append(line)
            continue
        keep = []
        for t in s_.split():
            if t in available:
                keep.append(t)
            elif SUBSTITUTES.get(t) in available:
                keep.append(SUBSTITUTES[t])
                subs[t] = SUBSTITUTES[t]
            else:
                removed.append(t)
        out.append(" ".join(keep) if keep else f"# (removed by build_iso.py) {s_}")
    return "\n".join(out) + "\n", removed, subs


# --------------------------------------------------------------------------- #
# 3. Pack into a tar with correct modes/owners (Windows perms are all 777/666)
# --------------------------------------------------------------------------- #
def wants_exec(rel: str, data: bytes) -> bool:
    return data.startswith(b"#!") or rel.startswith("config/hooks/")


def build_tar(files: dict[str, bytes], dirs: set[str], dest: Path):
    all_dirs = set(dirs)
    for rel in files:
        p = rel.rsplit("/", 1)[0] if "/" in rel else ""
        while p:
            all_dirs.add(p)
            p = p.rsplit("/", 1)[0] if "/" in p else ""
    now = time.time()

    def meta(ti: tarfile.TarInfo, mode: int):
        ti.mode, ti.uid, ti.gid, ti.uname, ti.gname, ti.mtime = mode, 0, 0, "root", "root", now

    with tarfile.open(dest, "w", format=tarfile.GNU_FORMAT) as tf:
        for d in sorted(all_dirs):
            ti = tarfile.TarInfo(d)
            ti.type = tarfile.DIRTYPE
            meta(ti, 0o755)
            tf.addfile(ti)
        for rel, data in sorted(files.items()):
            ti = tarfile.TarInfo(rel)
            ti.size = len(data)
            meta(ti, 0o755 if wants_exec(rel, data) else 0o644)
            tf.addfile(ti, fileobj=io.BytesIO(data))


# --------------------------------------------------------------------------- #
# 4. WSL plumbing
# --------------------------------------------------------------------------- #
def decode_out(b: bytes) -> str:
    """wsl.exe's own messages are UTF-16; output from inside Linux is UTF-8."""
    if not b:
        return ""
    if b"\x00" in b:
        return b.decode("utf-16-le", "replace").replace("\x00", "").replace("\ufeff", "").strip()
    return b.decode("utf-8", "replace").strip()


def long_path(p: Path) -> Path:
    """Expand Windows 8.3 short names (C:\\Users\\TITANH~1) to the real path."""
    try:
        import ctypes
        buf = ctypes.create_unicode_buffer(32768)
        if ctypes.windll.kernel32.GetLongPathNameW(str(p), buf, 32768):
            return Path(buf.value)
    except Exception:
        pass
    return p


class Wsl:
    def __init__(self, distro: str | None, tmp: Path):
        self.exe = shutil.which("wsl") or shutil.which("wsl.exe")
        if not self.exe:
            die("wsl.exe not found. Install WSL first, in an ADMIN PowerShell:\n"
                "    wsl --install -d Debian\nthen reboot.")
        r = subprocess.run([self.exe, "-l", "-q"], capture_output=True)
        names = [n.strip() for n in decode_out(r.stdout).splitlines() if n.strip()]
        names = [n for n in names if not n.lower().startswith("docker-desktop")]
        if r.returncode != 0 or not names:
            die("WSL is installed but has no Linux distro. In an ADMIN PowerShell run:\n"
                "    wsl --install -d Debian\nreboot if asked, open 'Debian' once to create a "
                "username/password, then run this again.\n(wsl said: " + decode_out(r.stdout + r.stderr) + ")")
        if distro:
            match = next((n for n in names if n.lower() == distro.lower()), None)
            if not match:
                die(f"No WSL distro named '{distro}'. Installed: {', '.join(names)}\n"
                    f"To add it:  wsl --install -d {distro}")
            distro = match
        else:
            distro = next((n for n in names if n.lower() == "debian"), None)  # else WSL's default
        self.distro, self.tmp, self._n = distro, tmp, 0
        info(f"WSL distros: {', '.join(names)}  ->  using {distro or 'your default distro'}")

    def _base(self) -> list[str]:
        cmd = [self.exe]
        if self.distro:
            cmd += ["-d", self.distro]
        return cmd + ["-u", "root", "--exec"]

    def path(self, p: Path) -> str:
        posix = long_path(p.resolve()).as_posix()
        r = subprocess.run(self._base() + ["wslpath", "-a", "-u", posix], capture_output=True)
        out = decode_out(r.stdout)
        if r.returncode == 0 and out:
            return out
        m = re.match(r"^([A-Za-z]):/(.*)$", posix)       # fall back to the default /mnt/<drive>/ layout
        if m:
            return f"/mnt/{m.group(1).lower()}/{m.group(2)}"
        die(f"Could not convert {p} to a WSL path: {decode_out(r.stderr) or decode_out(r.stdout)}")

    def script(self, body: str, env: dict[str, str] | None = None, capture: bool = False):
        """Run a bash script as root inside WSL. Script goes via a file => no quoting issues."""
        self._n += 1
        f = self.tmp / f"step{self._n}.sh"
        header = "set -euo pipefail\nexport PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\n"
        for k, v in (env or {}).items():
            header += f"export {k}={shlex.quote(v)}\n"
        f.write_text(header + body, encoding="utf-8", newline="\n")
        cmd = self._base() + ["bash", self.path(f)]
        if capture:
            r = subprocess.run(cmd, capture_output=True)
            return types.SimpleNamespace(returncode=r.returncode,
                                         stdout=decode_out(r.stdout), stderr=decode_out(r.stderr))
        return subprocess.run(cmd)


PROBE = r"""
echo "KERNEL=$(uname -r)"
. /etc/os-release
echo "OSID=${ID:-unknown}"
echo "OSVER=${VERSION_ID:-?}"
mkdir -p "$(dirname "$BUILD")"
echo "FREEGB=$(df -BG --output=avail "$(dirname "$BUILD")" | tail -n1 | tr -dc 0-9)"
"""

BUILD_SH = r"""
export DEBIAN_FRONTEND=noninteractive

echo "==> Installing build tools (live-build etc.)"
apt-get update -qq
apt-get install -y --no-install-recommends $HOST_DEPS

safe_rm() {
  # Never rm -rf a chroot that still has /dev, /proc... bind-mounted into it.
  if grep -qs " $1/" /proc/mounts; then
    echo "ERROR: something is still mounted under $1:" >&2
    grep " $1/" /proc/mounts >&2
    echo "Run 'wsl --shutdown' from Windows PowerShell, then try again." >&2
    exit 1
  fi
  rm -rf "$1"
}

echo "==> Staging source into $BUILD (WSL ext4 disk)"
if [ -d "$BUILD/config" ]; then (cd "$BUILD" && lb clean >/dev/null 2>&1) || true; fi
STAGE="$BUILD.stage"
safe_rm "$STAGE"
mkdir -p "$STAGE"
tar -xf "$TARFILE" -C "$STAGE"
if [ -d "$BUILD" ]; then
  if [ "$FRESH" != "1" ] && [ -d "$BUILD/cache" ]; then mv "$BUILD/cache" "$STAGE/cache"; fi
  safe_rm "$BUILD"
fi
mv "$STAGE" "$BUILD"

echo "==> Building ISO (this takes a while: ~30-60 min first time)"
cd "$BUILD"
export DISTRO ARCH=amd64
rc=0
{ bash scripts/configure.sh && lb build; } 2>&1 | tee "$BUILD/build.log" || rc=$?
mkdir -p "$OUT"
cp -f "$BUILD/build.log" "$OUT/pebbleos-build.log" || true
if [ "$rc" -ne 0 ]; then echo "BUILD FAILED (exit $rc) - see pebbleos-build.log" >&2; exit "$rc"; fi

ISO=$(ls -1 "$BUILD"/live-image-*.iso 2>/dev/null | head -n1 || true)
[ -n "$ISO" ] || { echo "ERROR: lb build finished but no ISO was produced" >&2; exit 1; }
cp -f "$ISO" "$OUT/pebbleos.iso"
echo "==> Done"
( cd "$OUT" && sha256sum pebbleos.iso )
"""


# --------------------------------------------------------------------------- #
def find_default_source() -> Path | None:
    for base in (Path.cwd(), Path(__file__).resolve().parent):
        if (base / "config" / "package-lists").is_dir():      # script sits inside the project
            return base
        for name in ("pebbleos-source.zip", "pebbleos"):
            if (base / name).exists():
                return base / name
    return None


def main():
    ap = argparse.ArgumentParser(description="Build the PebbleOS ISO via WSL2.")
    ap.add_argument("source", nargs="?", help="pebbleos-source.zip or the pebbleos folder")
    ap.add_argument("-o", "--out", default=".", help="where to put pebbleos.iso (default: current folder)")
    ap.add_argument("--stage", type=int, choices=(1, 2, 3, 4), default=4,
                    help="package set: 1=minimal desktop ... 4=everything (default)")
    ap.add_argument("--suite", default="bookworm", help="Debian release to build (default: bookworm)")
    ap.add_argument("--wsl-distro", help="WSL distro name, e.g. Debian (default: your default distro)")
    ap.add_argument("--mirror", default="http://deb.debian.org/debian")
    ap.add_argument("--build-dir", default=DEFAULT_BUILD_DIR, help="build dir inside WSL")
    ap.add_argument("--fresh", action="store_true", help="also discard live-build's download cache")
    ap.add_argument("--skip-pkg-check", action="store_true", help="don't validate package names")
    ap.add_argument("--prepare-only", action="store_true", help="patch + report only; don't run WSL")
    ap.add_argument("--force", action="store_true", help="skip the WSL2/Debian sanity checks")
    a = ap.parse_args()

    src = Path(a.source) if a.source else find_default_source()
    if not src:
        die("Couldn't find pebbleos-source.zip or a pebbleos folder. Pass the path as an argument.")
    out_dir = Path(a.out).resolve()

    tmp = Path(tempfile.mkdtemp(prefix="pebbleos-"))
    atexit.register(shutil.rmtree, tmp, True)
    w = None if a.prepare_only else Wsl(a.wsl_distro, tmp)     # fail fast if WSL isn't ready

    # ---- load & patch --------------------------------------------------------
    info(f"Loading {src}")
    files, dirs = load_tree(src)
    n = fix_line_endings(files)
    if n:
        info(f"Converted CRLF -> LF in {n} file(s)")

    pkg_text = select_stage(files, a.stage)
    info(f"Using package set: stage {a.stage} (other stage lists removed - live-build would merge them all)")

    if WALLPAPER_DST not in files:
        if WALLPAPER_SRC in files:
            files[WALLPAPER_DST] = files[WALLPAPER_SRC]
            info("Using assets/wallpapers/default.jpg as the desktop/login wallpaper")
        else:
            pkg_text += "\n# added by build_iso.py: needed by 020-branding hook to generate default.jpg\nimagemagick\n"
            info("No wallpaper supplied: adding 'imagemagick' so the branding hook can generate one")

    if not a.skip_pkg_check:
        info("Validating package names against the Debian archive...")
        avail = fetch_available(a.mirror, a.suite)
        if avail:
            pkg_text, removed, subs = filter_packages(pkg_text, avail)
            for old, new in subs.items():
                info(f"Replaced '{old}' (not in {a.suite}) with '{new}'")
                fix = LAUNCHER_FIXES.get(old)
                if fix and fix[0] in files:
                    files[fix[0]] = files[fix[0]].decode().replace(fix[1], fix[2]).encode()
                    info(f"  updated launcher {fix[0].rsplit('/', 1)[-1]}")
            if removed:
                info(f"Dropped {len(removed)} package(s) that don't exist in {a.suite}: {', '.join(removed)}")
            else:
                info("All package names are valid.")
    files[PKG_DIR + "pebble.list.chroot"] = pkg_text.encode()

    # ---- pack ---------------------------------------------------------------
    tarpath = tmp / "pebbleos-src.tar"
    build_tar(files, dirs, tarpath)
    info(f"Packed {len(files)} files")
    if a.prepare_only:
        keep = out_dir / "pebbleos-prepared.tar"
        out_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(tarpath, keep)
        info(f"--prepare-only: wrote {keep}")
        return

    # ---- WSL checks ------------------------------------------------------
    r = w.script(PROBE, env={"BUILD": a.build_dir}, capture=True)
    if r.returncode != 0:
        die("Couldn't run a command in WSL. Is the distro installed and initialised "
            "(open it once from the Start menu to create a user)?\n" + (r.stderr or r.stdout))
    probe = dict(l.split("=", 1) for l in r.stdout.splitlines() if "=" in l)
    kernel, osid = probe.get("KERNEL", ""), probe.get("OSID", "")
    free = int(probe.get("FREEGB") or 0)
    info(f"WSL kernel {kernel} | {osid} {probe.get('OSVER')} | {free} GB free")
    if not a.force:
        if "wsl2" not in kernel.lower():
            die("This distro is running under WSL1. Convert it:  wsl --set-version <name> 2")
        if osid != "debian":
            die(f"WSL distro is '{osid}', not Debian. Ubuntu's live-build is an older fork that "
                "chokes on this Debian config.\n  Fix:  wsl --install -d Debian   then re-run with  "
                "--wsl-distro Debian\n  (or pass --force to try anyway)")
        if free and free < 20:
            die(f"Only {free} GB free for the WSL disk; need ~20 GB. Free up space or use --force.")

    # ---- build -----------------------------------------------------------
    out_dir.mkdir(parents=True, exist_ok=True)
    env = {
        "BUILD": a.build_dir, "TARFILE": w.path(tarpath), "OUT": w.path(out_dir),
        "DISTRO": a.suite, "FRESH": "1" if a.fresh else "0", "HOST_DEPS": HOST_DEPS,
    }
    try:
        rc = w.script(BUILD_SH, env=env).returncode
    except KeyboardInterrupt:
        die("Interrupted. If a later build complains about mounts, run:  wsl --shutdown", 130)
    if rc != 0:
        log = out_dir / "pebbleos-build.log"
        die(f"Build failed (exit {rc}). Log: {log if log.exists() else a.build_dir + '/build.log (in WSL)'}", rc)

    iso = out_dir / "pebbleos.iso"
    size = iso.stat().st_size / 1e6 if iso.exists() else 0
    info(f"SUCCESS: {iso}  ({size:,.0f} MB)")
    info("Test it in VirtualBox/QEMU - login: pebble / pebble")


if __name__ == "__main__":
    main()
