"""Create a multi-size Windows icon from the standing sprite frame."""
from pathlib import Path
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter, QPixmap


ROOT = Path(__file__).resolve().parent


def main():
    app = QGuiApplication.instance() or QGuiApplication(sys.argv)
    sheet = QPixmap(str(ROOT / 'assets' / 'fahadh.png'))
    if sheet.isNull():
        raise RuntimeError('Could not load assets/fahadh.png')
    frame = sheet.copy(3 * sheet.width() // 4, 0, sheet.width() // 4, sheet.height())
    canvas = QImage(256, 256, QImage.Format.Format_ARGB32)
    canvas.fill(Qt.GlobalColor.transparent)
    sprite = frame.scaled(236, 236, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    painter = QPainter(canvas)
    painter.drawPixmap((256 - sprite.width()) // 2, 256 - sprite.height(), sprite)
    painter.end()
    output = ROOT / 'assets' / 'fahadh.ico'
    if not canvas.save(str(output), 'ICO'):
        raise RuntimeError('Could not save the Windows icon')
    print(output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
