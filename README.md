# Fahadh Water Companion

A small offline Windows desktop companion that stays quietly in the system tray and appears with a cartoon Fahadh Faasil every two hours to remind you to drink water.

## Start here

1. Extract this ZIP into a permanent folder, for example `Documents\WaterCompanion`. Do not run it from inside the ZIP.
2. Install **Python 3.12 (64-bit)** from https://www.python.org/downloads/windows/ if needed. Include the Python launcher. Python 3.12.10 has a Windows installer.
3. Double-click **SETUP.bat**. It creates a private Python environment in this folder and downloads the required packages. Internet is needed for this setup only.
4. Double-click **START.bat**. The companion starts quietly in the Windows system tray.
5. Right-click the character and select **Test reminder** to see a water break immediately.

The character remains hidden until a reminder is due. When he appears, drag to reposition horizontally or move to another monitor. On release he returns to the bottom edge. Right-click for controls. A tray icon remains beside the Windows clock; check the hidden-icons arrow if needed.

## Controls and timing

- **Done** closes a real reminder, hides the companion, and schedules the next one two hours later.
- **Snooze 5 min** hides the companion and brings the reminder back five minutes later.
- **Snooze 10 min** hides the companion and brings the reminder back ten minutes later.
- **Test reminder** shows a preview without changing the real reminder time.
- **Pause reminders** stops reminders. Unpause to begin a new two-hour interval.
- **Move to next monitor** cycles through connected monitors.
- **Settings…** changes the reminder interval, both snooze durations, sound, preferred monitor, and start-with-Windows behavior.
- **Quit** fully exits. Double-click START.bat or the packaged app to return.

Double-click the tray icon to show a reminder preview without changing the real timer.

A real reminder stays visible until you choose Done or Snooze. The timer is saved in `%LOCALAPPDATA%\FahadhWaterCompanion\reminder.json`. Quitting or restarting does not reset it. After sleep or time with the app closed, an overdue reminder appears once when the app is running again. It does not wake the computer or show reminders while the computer is off. Manual changes to the system clock also change wall-clock due timing.

Only one copy runs at a time. The app does not need ChatGPT, an account, an API key, or an internet connection after installation. It does not collect data or send requests. The two-hour interval is your chosen reminder frequency.

## Make your Windows app (.exe)

After setup, double-click **BUILD_EXE.bat**. This downloads the packaging tool and builds:

`dist\FahadhWaterCompanion\FahadhWaterCompanion.exe`

Keep the **entire** `dist\FahadhWaterCompanion` folder, including `_internal`, together. You can copy that folder elsewhere and launch the `.exe` without installing Python there. Source files remain available for future customization. Re-run BUILD_EXE.bat after code or artwork changes.

The ZIP contains source and build scripts; it does **not** contain a prebuilt Windows executable. The executable must be built and tested on Windows.

For a complete release, run **BUILD_RELEASE.bat**. It runs the tests, builds the versioned application with its Windows icon, and creates `release\FahadhWaterCompanion-Portable-1.0.0.zip`. If Inno Setup 6 is installed, it also creates `release\FahadhWaterCompanion-Setup-1.0.0.exe`.

## Optional: start when you sign in

Once the app works:

1. Create a shortcut to the built `.exe` (or START.bat if using the Python version).
2. Press **Win + R**, type `shell:startup`, and press Enter.
3. Put the **shortcut** in that folder. Keep the actual app files in their permanent location.

Remove that shortcut to disable automatic startup. No startup setting is changed automatically by these scripts.

## Troubleshooting

- **Python not found:** install Python 3.12 with its launcher, then run SETUP.bat again.
- **Nothing visible:** check the tray icon, choose Hide / show character, or double-click the tray icon. Another running copy may already exist.
- **Startup failure:** see `%LOCALAPPDATA%\FahadhWaterCompanion\app.log`. To see console errors, open a terminal in the project folder and run `.venv\Scripts\python.exe app.py`.
- **Build fails:** keep the build window open and read its error. Setup/build require internet and permission to install packages in the local project environment.
- **Reminder overlaps your work:** use Pause or Hide from the right-click menu. Exclusive fullscreen apps can cover ordinary desktop overlays.
- **Reset timing:** quit the app, remove `reminder.json` from the app-data folder above, and restart.

## Customize

- `app.py`: interface, movement, board text, and controls.
- `schedule.py`: the interval is `INTERVAL = 2 * 60 * 60` seconds.
- `assets/fahadh.png`: transparent four-cell sprite sheet. The first three cells are walking poses; the fourth is the standing pose. The app slices and aligns them at runtime.
- `requirements.txt`: tested GUI dependency version.
- `test_companion.py`: scheduling and GUI behavior checks.
- `ARTWORK.md`: artwork generation details and prompt.

## Validation

Run `.venv\Scripts\python.exe smoke_test.py` for automated Windows readiness checks. Follow `SMOKE_TEST.md` for the short native tray, scaling, and multi-monitor checklist.

Four automated tests passed under Linux with Qt's offscreen renderer: saved timing across restart/sleep, snooze and pause/resume, invalid-state recovery, and interface reminder/preview behavior. The reminder board was rendered and visually inspected.

Native Windows transparency, click-through outside the character, tray interaction, multi-monitor behavior, startup shortcuts, and the packaged executable still need a Windows smoke test. After building, check Test reminder, dragging, pause/resume, hide/show, quit/reopen, and launch the executable from its complete output folder. To test a real reminder quickly, quit, temporarily set `INTERVAL = 20` in schedule.py, remove the saved reminder state, and relaunch; restore the interval and reset the state afterward.
