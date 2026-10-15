# Windows smoke test

Run the automated checks from the project folder:

```powershell
.\.venv\Scripts\python.exe smoke_test.py
```

Then run `START.bat` and verify the native interactions that cannot be validated by the offscreen test:

- The app starts without showing the companion.
- The tray icon appears, including under the hidden-icons arrow.
- Double-clicking the tray icon shows a preview and closing it hides the companion.
- **Test reminder** works from the tray context menu.
- **Pause reminders** updates its check mark and tooltip correctly.
- **Move to next monitor** works when a second display is connected.
- The board and all three buttons remain readable at 100%, 125%, and 150% display scaling.
- A real reminder stays visible until **Done** or a snooze option is selected.
- Closing and restarting the app preserves the next reminder time.
- **Quit** removes the tray icon and ends the process.

Record any failure with the Windows version, display scaling, number of monitors, and the relevant lines from `%LOCALAPPDATA%\FahadhWaterCompanion\app.log`.
