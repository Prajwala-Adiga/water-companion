"""Fahadh Water Companion. Runs offline; no network or account required."""
import logging
import math
import os
from pathlib import Path
import sys
import time

from PySide6.QtCore import Qt, QTimer, QRect, QPoint, QLockFile
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap, QRegion, QTransform
from PySide6.QtWidgets import QApplication, QWidget, QFrame, QLabel, QPushButton, QMenu, QSystemTrayIcon, QMessageBox
from schedule import Schedule

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
DATA = Path(os.environ.get('LOCALAPPDATA', Path.home() / '.local' / 'share')) / 'FahadhWaterCompanion'

class Companion(QWidget):
    def __init__(self, data_dir=DATA):
        super().__init__()
        self.setWindowTitle('Fahadh Water Companion')
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(340, 380)
        self.schedule = Schedule(data_dir / 'reminder.json', time.time())
        self.error_shown = False
        self.persist(self.schedule.save)
        self.direction, self.phase, self.walking = 1, 0, True
        self.drag_offset = None
        self.board_kind = None
        self.hidden_by_user = False
        self.last_tick = time.monotonic()
        self.frame_tick = 0.0
        sheet = QPixmap(str(ROOT / 'assets' / 'fahadh.png'))
        if sheet.isNull():
            raise RuntimeError('Character artwork is missing. Extract the entire ZIP before running.')
        self.frames = []
        for i in range(4):
            cell = sheet.copy(i * sheet.width() // 4, 0, sheet.width() // 4, sheet.height())
            # Align visible bodies using alpha, while retaining the supplied artwork.
            image = cell.toImage()
            bounds = QRegion(cell.mask()).boundingRect()
            if bounds.isEmpty():
                raise RuntimeError('Character frame is empty')
            cell = cell.copy(bounds).scaledToHeight(194, Qt.TransformationMode.SmoothTransformation)
            self.frames.append(cell)
        self.icon = QIcon(self.frames[3])
        self.setWindowIcon(self.icon)
        self.board = QFrame(self)
        self.board.setGeometry(8, 8, 324, 160)
        self.board.setStyleSheet('QFrame {background:#fffaf0; border:2px solid #147d76; border-radius:16px;} QLabel {border:0; background:transparent; color:#183d3a;} QPushButton {background:#147d76;color:white;border:0;border-radius:8px;padding:8px;font-weight:600;} QPushButton:hover {background:#0b605b;}')
        self.eyebrow = QLabel('A LITTLE PAUSE', self.board)
        self.eyebrow.setGeometry(16, 10, 290, 22)
        self.eyebrow.setFont(QFont('Segoe UI', 9, QFont.Weight.Bold))
        self.title = QLabel('Time for some water', self.board)
        self.title.setGeometry(16, 34, 296, 30)
        self.title.setFont(QFont('Segoe UI', 16, QFont.Weight.Bold))
        self.detail = QLabel('Take a sip. Your next break is in two hours.', self.board)
        self.detail.setGeometry(16, 66, 295, 35)
        self.detail.setWordWrap(True)
        self.detail.setFont(QFont('Segoe UI', 10))
        self.done = QPushButton('Done', self.board)
        self.done.setGeometry(16, 112, 135, 34)
        self.done.clicked.connect(self.acknowledge)
        self.snooze = QPushButton('Snooze 10 min', self.board)
        self.snooze.setGeometry(161, 112, 147, 34)
        self.snooze.clicked.connect(self.snooze_reminder)
        self.board.hide()
        self.menu = QMenu(self)
        self.menu.addAction('Test reminder', self.test_reminder)
        self.pause_action = self.menu.addAction('Pause reminders')
        self.pause_action.setCheckable(True)
        self.pause_action.setChecked(self.schedule.paused)
        self.pause_action.triggered.connect(self.toggle_pause)
        self.walk_action = self.menu.addAction('Walk around')
        self.walk_action.setCheckable(True)
        self.walk_action.setChecked(True)
        self.walk_action.triggered.connect(self.set_walking)
        self.menu.addAction('Hide / show character', self.toggle_visible)
        self.menu.addAction('Move to next monitor', self.next_monitor)
        self.menu.addSeparator()
        self.menu.addAction('Quit', QApplication.instance().quit)
        self.tray = QSystemTrayIcon(self.icon, self)
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self.tray_clicked)
        self.tray.show()
        self.monitor = QApplication.primaryScreen()
        QApplication.instance().screenRemoved.connect(self.screen_removed)
        for screen in QApplication.screens():
            screen.availableGeometryChanged.connect(self.fit_screen)
        self.fit_screen()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(33)
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self.check_due)
        self.check_timer.start(1000)
        self.show()
        self.show_board('welcome')
        self.check_due()

    def persist(self, operation):
        try:
            operation()
        except OSError:
            logging.exception('Could not save reminder state')
            if not self.error_shown:
                self.error_shown = True
                QMessageBox.warning(self, 'Settings could not be saved', 'Reminders will work this session, but their timing may reset after you quit. Check that your local app-data folder is writable.')

    def fit_screen(self, *_):
        area = self.monitor.availableGeometry()
        self.move(max(area.left(), min(self.x(), area.right() - self.width() + 1)), area.bottom() - self.height() + 1)

    def next_monitor(self):
        screens = QApplication.screens()
        self.monitor = screens[(screens.index(self.monitor) + 1) % len(screens)]
        self.move(self.monitor.availableGeometry().left(), self.y())
        self.fit_screen()

    def screen_removed(self, removed):
        if self.monitor == removed:
            self.monitor = QApplication.primaryScreen()
            self.fit_screen()

    def current_pixmap(self):
        frame = self.frames[[0, 1, 2, 1][self.phase % 4]] if self.walking and not self.board_kind and not self.drag_offset and not self.schedule.paused else self.frames[3]
        return frame.transformed(QTransform().scale(-1, 1)) if self.direction < 0 else frame

    def sprite_rect(self, pix):
        return QRect((self.width() - pix.width()) // 2, self.height() - pix.height(), pix.width(), pix.height())

    def update_shape(self):
        pix = self.current_pixmap()
        rect = self.sprite_rect(pix)
        region = QRegion(pix.mask()).translated(rect.topLeft())
        if self.board_kind:
            region = region.united(QRegion(self.board.geometry()))
        self.setMask(region)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        pix = self.current_pixmap()
        painter.drawPixmap(self.sprite_rect(pix).topLeft(), pix)

    def tick(self):
        now = time.monotonic()
        dt, self.last_tick = min(now - self.last_tick, 0.1), now
        if self.walking and not self.board_kind and not self.drag_offset and not self.schedule.paused and self.isVisible():
            self.frame_tick += dt
            if self.frame_tick >= 0.15:
                self.phase += 1
                self.frame_tick = 0
            area = self.monitor.availableGeometry()
            x = self.x() + self.direction * max(1, round(48 * dt))
            low, high = area.left(), max(area.left(), area.right() - self.width() + 1)
            if x <= low or x >= high:
                self.direction *= -1
            self.move(max(low, min(high, x)), area.bottom() - self.height() + 1)
        self.update_shape()

    def show_board(self, kind):
        self.board_kind = kind
        welcome = kind == 'welcome'
        self.eyebrow.setText('HELLO, I’M YOUR WATER COMPANION' if welcome else ('PREVIEW • NO TIMER CHANGE' if kind == 'test' else 'A LITTLE PAUSE'))
        self.title.setText('A sip every two hours' if welcome else 'Time for some water')
        self.detail.setText('Drag me to move. Right-click for controls.' if welcome else 'Take a little water break. You’ve earned it.')
        self.done.setText('Let’s go' if welcome else ('Close preview' if kind == 'test' else 'Done'))
        self.snooze.setVisible(kind == 'reminder')
        self.board.show()
        self.show()
        self.fit_screen()
        self.update_shape()

    def dismiss_board(self):
        self.board_kind = None
        self.board.hide()
        if self.hidden_by_user:
            self.hide()
        self.update_shape()

    def acknowledge(self):
        if self.board_kind == 'reminder':
            self.persist(lambda: self.schedule.postpone(time.time()))
        self.dismiss_board()

    def snooze_reminder(self):
        self.persist(lambda: self.schedule.postpone(time.time(), 600))
        self.dismiss_board()

    def test_reminder(self):
        if self.board_kind != 'reminder':
            self.show_board('test')

    def check_due(self):
        if self.schedule.due(time.time()) and self.board_kind != 'reminder':
            self.show_board('reminder')
        remaining = max(0, math.ceil((self.schedule.next_due - time.time()) / 60))
        text = 'Paused' if self.schedule.paused else ('Water break is due' if remaining == 0 else f'Next water break in {remaining} min')
        self.tray.setToolTip('Fahadh Water Companion — ' + text)

    def toggle_pause(self, paused):
        self.persist(lambda: self.schedule.pause(paused, time.time()))
        self.dismiss_board()
        self.check_due()

    def set_walking(self, walking):
        self.walking = walking

    def toggle_visible(self):
        self.hidden_by_user = not self.hidden_by_user
        self.setVisible(not self.hidden_by_user)

    def tray_clicked(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.hidden_by_user = False
            self.show()

    def contextMenuEvent(self, event):
        self.menu.exec(event.globalPos())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_offset = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        if self.drag_offset is not None:
            self.move(event.globalPosition().toPoint() - self.drag_offset)

    def mouseReleaseEvent(self, event):
        self.drag_offset = None
        self.monitor = QApplication.screenAt(event.globalPosition().toPoint()) or self.monitor
        self.fit_screen()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('Fahadh Water Companion')
    app.setQuitOnLastWindowClosed(False)
    DATA.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=str(DATA / 'app.log'), level=logging.WARNING)
    lock = QLockFile(str(DATA / 'app.lock'))
    if not lock.tryLock(100):
        QMessageBox.information(None, 'Already running', 'Your companion is already running. Look beside the Windows clock, including hidden tray icons.')
        return 0
    try:
        pet = Companion()
    except Exception as exc:
        logging.exception('Startup failed')
        QMessageBox.critical(None, 'Could not start', str(exc))
        return 1
    return app.exec()

if __name__ == '__main__':
    sys.exit(main())
