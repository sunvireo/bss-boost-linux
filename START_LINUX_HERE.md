# Bss Booster for Linux — X11 and Wayland

Bss Booster has the same Hotbar, Alarms, Profiles, saved settings, seven configurable red AUTO buttons, and independently movable alarm panel as Windows.

## Download a Linux app (no Python needed)

1. The developer uploads the **contents** of the `BssBoosterV1` folder to GitHub, including `.github/workflows/linux-release.yml`.
2. Under **Actions**, run **Build Bss Booster Linux App** and download the successful `BssBooster-Linux-x86_64` artifact.
3. Extract the artifact, then extract `BssBooster-Linux-x86_64.tar.gz`.
4. From the extracted directory, run:

```bash
chmod +x BssBooster
./BssBooster
```

Python is **not** needed to run the finished binary. This is a Linux x86-64 build, not a Flatpak or AppImage. Build and test it on each distribution you plan to support.

## Wayland: hotbar macro setup (Ubuntu / Mint / Debian)

1. Check you're on Wayland: `echo "$XDG_SESSION_TYPE"` should return `wayland`.
2. Install the required keyboard input helper:

   ```bash
   sudo apt update
   sudo apt install ydotool espeak-ng pulseaudio-utils
   ```

3. **Configure and start `ydotoold` according to your Linux distribution's instructions.** The daemon needs controlled access to `/dev/uinput`, which may require a privileged service or an appropriately configured user service. Bss Booster **does not** install the service or change system permissions for you. If the package installs a systemd `ydotoold` service, consult your distribution and use it; service names and socket locations vary. Do **not** blindly grant everyone access to `/dev/uinput` or run Bss Booster as root.
4. Verify it works in a harmless test window before using in Roblox:

   ```bash
   ydotool key 2:1 2:0
   ```

   That sends a `1` keystroke to the focused window. Make sure no risky app has focus before testing.
5. Open Bss Booster → Settings. **On Wayland, active-window title detection is unavailable.** For safety, **the macro will not type anything with “Only send keys while Roblox is active” enabled**. You can *explicitly turn that option off*, understanding that keypresses will then go to whichever app is focused. Don't switch windows while the macro is running; press Stop first.
6. Assign items and cooldowns, start the macro, and keep the game focused. The macro uses `ydotool`, not `xdotool`, on Wayland.

Wayland users on Fedora/Arch can install `ydotool` from their distribution's package manager; service setup differs. A containerised **Flatpak** would require extra permissions and is not supplied by this package.

## Wayland: global shortcuts (requires one-time desktop setup)

Wayland doesn't let apps silently intercept arbitrary keyboard shortcuts globally. Bss Booster provides an **opt-in command bridge**: the user creates a custom keyboard shortcut in **System Settings → Keyboard → Custom Shortcuts** (names vary by GNOME/KDE) and assigns one of these commands, replacing the example path with the path where Bss Booster is installed:

```bash
/home/USERNAME/Downloads/BssBooster/BssBooster --control start
/home/USERNAME/Downloads/BssBooster/BssBooster --control pause
/home/USERNAME/Downloads/BssBooster/BssBooster --control stop
/home/USERNAME/Downloads/BssBooster/BssBooster --control alarm:Glitter
```

Suggested shortcuts: F1 for Start, F2 for Pause, F3 for Stop; another unused key for the “Glitter” alarm. The desktop decides whether single-key shortcuts are permitted or reserved. The app must already be running. Commands go through a local per-user socket; Bss Booster doesn't read keyboard events or install privileged keyboard hooks for this feature. **Shortcuts entered in the app’s Alarm page do not automatically register on Wayland**; use desktop custom shortcuts as above.

Alternatively, click the **Start, Pause, Stop** buttons in Bss Booster directly. Those don't require desktop shortcuts.

## Wayland: overlays and alarms

- Sound and offline voice alerts work without X11 and still run when hidden. Voice uses `espeak-ng` or `espeak` and sound uses `paplay`, `aplay`, or `ffplay`.
- If **XWayland is available**, Bss Booster defaults to Qt's `xcb` platform for its floating windows, which can improve moving and stacking the red buttons and the alarm window. This is just a display compatibility mode: keypresses still use `ydotool`.
- Some Wayland compositors **do not allow** always-on-top windows above native Wayland games, and some don't allow arbitrary window placement. Bss Booster cannot guarantee overlays appear over every game/compositor. Test on KDE Plasma / GNOME with the intended Roblox client in borderless/windowed mode.
- If `xcb` is unavailable or fails, launch with `QT_QPA_PLATFORM=wayland ./BssBooster` to use native Wayland display support. The UI should run, but custom overlay placement may then be limited by the compositor.
- Alarm timers still count down and make noise even when overlays are hidden.

## X11 instructions

On an Xorg/X11 desktop, install `xdotool` to send keys and `espeak-ng` for speech:

```bash
sudo apt install xdotool espeak-ng pulseaudio-utils
```

The app can detect the focused X11 window title with `xdotool`, so the “Only send keys while Roblox is active” option works there. X11 global shortcuts use `pynput`. This is the older, more directly supported input route.

## Run/build from source

With Python available locally:

```bash
./run_linux.sh
./build_linux.sh
```

The Python build method is optional. The GitHub Actions artifact lets end users run Bss Booster without Python installed.

## Safety and compatibility

Only start a macro after configuring its slots. Default **focus protection stays ON** when first installed; users must knowingly disable it on Wayland to allow automated keypresses. If `ydotoold` cannot be reached, keys are not sent and the app logs the failure. No game memory scanning, Roblox modification, or anti-cheat bypass is included. Some games ignore simulated input. Results vary across Ubuntu, Mint, KDE, GNOME, Sober, and other clients. No real Wayland/game runtime test was possible in the development environment; verify on a real Wayland desktop before sharing as universally compatible.
