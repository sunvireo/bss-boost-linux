# Bss Booster for Linux — quick start

This is the **Bss Booster desktop app**, ported from the latest Windows design. It preserves the seven hotbar slots, clickable red AUTO pills, adjustable intervals, profile saves, bell-icon Alarms tab, individual button visibility, and independently movable alarm overlay.

## Easiest method — no Python installation

1. Create/open a GitHub repository with the **contents of this `BssBoosterV1` folder** at the repository root, including `.github/workflows/linux-release.yml`.
2. Open **Actions → Build Bss Booster Linux App → Run workflow**.
3. Wait for a successful run, open it, and download the artifact **BssBooster-Linux-x86_64**.
4. Unzip the artifact, then extract the contained `BssBooster-Linux-x86_64.tar.gz`.
5. Open a terminal in the extracted folder and run `chmod +x BssBooster && ./BssBooster`.

**This executable does not require Python installed.** It is an unsigned Linux x86_64 binary, built by GitHub on Ubuntu 22.04. It has not been tested on all Linux distributions.

## Before using the macro on Linux

On Ubuntu or Debian, install optional system helpers once:

```bash
sudo apt update
sudo apt install xdotool espeak-ng pulseaudio-utils
```

The **macro and global reset/start/stop shortcuts require an X11/Xorg desktop session**, not native Wayland. On Ubuntu, sign out, select the gear on the login screen, and choose **Ubuntu on Xorg** (if offered). Windows key injection is not used on Linux. The Linux app sends simulated keys only to whichever window is already focused and, by default, only if its title matches the **Target window** in Settings. Linux Roblox clients may be titled **Sober**, not **Roblox** — set the correct target title in Settings.

Alarms run when hidden. The offline Linux voice uses `espeak-ng` (or `espeak`); sound uses `paplay`, `aplay` or `ffplay` if installed. If voice isn't installed the app attempts the sound alarm instead. No cloud speech service is needed.

The overlay may behave differently between X11 window managers. Certain games or anti-cheat systems may ignore simulated keypresses. Native Wayland forbids general cross-application key injection and global shortcuts without compositor-specific privileges; this version intentionally disables both there instead of pretending they work.

## Run from source (Python required only for this method)

On Ubuntu/Debian with Python 3 available:

```bash
sudo apt install python3 python3-venv xdotool espeak-ng pulseaudio-utils
./run_linux.sh
```

The script creates `.venv`, installs PySide6 and `pynput`, then launches the GUI. Internet is needed for the initial Python dependency installation, but alarm speech works offline afterwards.

## Build the Linux executable on your own Linux PC

```bash
./build_linux.sh
./dist/BssBooster
```

To optionally install the locally built executable into your user application menu, run `./install_linux_binary.sh`.

## Notes

- An existing Windows executable cannot run natively as a Linux binary. The Linux workflow builds Linux ELF executable bytes on Linux.
- Linux and Windows settings are stored separately. Linux normally uses `~/.bss_booster/booster_settings.json`.
- The app doesn't automate logging in or read Roblox memory. It only sends configurable number-key presses when you start a macro.
- Be cautious about game rules governing macros, and test with nonessential items first.
