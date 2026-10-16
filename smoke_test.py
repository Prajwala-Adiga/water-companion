"""Quick Windows readiness checks that do not modify the user's real reminder state."""
import platform
import tempfile
from pathlib import Path

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QSystemTrayIcon

from app import Companion, ROOT


def check(condition, message):
    if not condition:
        raise RuntimeError(message)
    print(f'PASS: {message}')


def manual_check(condition, message):
    status = 'PASS' if condition else 'MANUAL CHECK REQUIRED'
    print(f'{status}: {message}')


def main():
    app = QApplication.instance() or QApplication([])
    check(platform.system() == 'Windows', 'running on Windows')
    manual_check(QSystemTrayIcon.isSystemTrayAvailable(), 'Windows system tray is available')
    check(bool(QApplication.screens()), 'at least one display is available')

    artwork = QPixmap(str(ROOT / 'assets' / 'fahadh.png'))
    check(not artwork.isNull(), 'character artwork loads')
    check(artwork.width() % 4 == 0, 'sprite sheet contains four equal-width cells')

    with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
        pet = Companion(Path(tmp))
        pet.check_timer.stop()
        check(not pet.isVisible(), 'companion starts hidden')
        pet.test_reminder()
        app.processEvents()
        check(pet.isVisible(), 'preview can be shown')
        check(pet.board_kind == 'test', 'preview does not become a real reminder')
        pet.motion_target_x = pet.x()
        pet.animate_motion()
        pet.acknowledge()
        pet.finish_exit()
        check(not pet.isVisible(), 'companion hides after preview closes')
        pet.tray.hide()
        pet.close()
        pet.deleteLater()

    print('Automated Windows smoke test passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
