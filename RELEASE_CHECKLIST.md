# Windows release checklist

## Prepare

1. Update `VERSION` using `major.minor.patch` format.
2. Confirm the working tree contains the intended changes.
3. Quit every running copy of Fahadh Water Companion.
4. Install Inno Setup 6 if an installer is required.

## Build

1. Double-click `BUILD_RELEASE.bat`.
2. Confirm all automated tests pass.
3. Confirm the portable ZIP and setup executable appear in `release`.

## Test the packaged application

1. Extract the portable ZIP into a new folder and launch the executable.
2. Check Friendly Fahadh and Ranga mode.
3. Check Done, both Snooze buttons, Settings, Pause, and Test reminder.
4. Quit and reopen the application; confirm settings and timing persist.

## Test the installer

1. Install using the setup executable.
2. Check Start Menu and optional desktop shortcuts.
3. Check the optional start-at-sign-in task.
4. Install the same version again to test repair/upgrade behavior.
5. Uninstall from Windows Settings and confirm the program folder is removed.
6. Reinstall once more and perform a final reminder test.

## Publish

1. Commit and push the release source changes.
2. Create a GitHub release tagged `v` followed by the value in `VERSION`.
3. Upload the setup executable and portable ZIP from `release`.
4. Include the SmartScreen note for this unsigned personal build.
