"""Fahadh Water Companion. Runs offline; no network or account required."""
import logging
import math
import os
from pathlib import Path
import random
import sys
import time

from PySide6.QtCore import Qt, QTimer, QRect, QPoint, QLockFile
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap, QRegion, QTransform
from PySide6.QtWidgets import QApplication, QWidget, QFrame, QLabel, QPushButton, QMenu, QSystemTrayIcon, QMessageBox, QDialog, QFormLayout, QSpinBox, QCheckBox, QComboBox, QDialogButtonBox
from schedule import Schedule
from settings import Settings, set_start_with_windows

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
DATA = Path(os.environ.get('LOCALAPPDATA', Path.home() / '.local' / 'share')) / 'FahadhWaterCompanion'

CHARACTERS = {
    'friendly': {
        'name': 'Friendly Fahadh',
        'walk': 'fahadh.png',
        'reminder': 'fahadh-reminder.png',
        'happy': 'fahadh-happy.png',
        'snooze': 'fahadh-snooze.png',
        'reminders': ['Did you drink water?'],
        'done': ['Nice work!', 'That’s better.', 'Good choice!'],
        'snoozed': ['Okay, I’ll be back.', 'Five more minutes, then!', 'Don’t forget me.'],
    },
    'ranga': {
        'name': 'Ranga mode',
        'walk': 'ranga-walk.png',
        'reminder': 'ranga-reminder.png',
        'happy': 'ranga-happy.png',
        'snooze': 'ranga-warning.png',
        'reminders': ['Eyy… drink water!', 'Water. Now.', 'I am asking nicely… for now.', 'Hydration first. Everything else later.'],
        'done': ['Good. Very good.', 'That’s my friend.', 'Excellent decision.', 'Okay… you may continue.'],
        'snoozed': ['Five minutes. Not one minute more.', 'I’ll come back. Be ready.', 'Again snooze? I am watching.', 'This is your final warning!'],
    },
}


class SettingsDialog(QDialog):
    def __init__(self, settings, screens, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Water Companion settings')
        layout = QFormLayout(self)
        self.interval = QSpinBox()
        self.interval.setRange(15, 720)
        self.interval.setSuffix(' min')
        self.interval.setValue(settings.interval_minutes)
        self.short_snooze = QSpinBox()
        self.short_snooze.setRange(1, 60)
        self.short_snooze.setSuffix(' min')
        self.short_snooze.setValue(settings.snooze_short_minutes)
        self.long_snooze = QSpinBox()
        self.long_snooze.setRange(1, 60)
        self.long_snooze.setSuffix(' min')
        self.long_snooze.setValue(settings.snooze_long_minutes)
        self.sound = QCheckBox('Play a sound when the reminder appears')
        self.sound.setChecked(settings.sound_enabled)
        self.autostart = QCheckBox('Start quietly when I sign in to Windows')
        self.autostart.setChecked(settings.start_with_windows)
        self.monitor = QComboBox()
        for index, screen in enumerate(screens):
            self.monitor.addItem(f'{index + 1}: {screen.name()}')
        self.monitor.setCurrentIndex(min(settings.preferred_monitor, len(screens) - 1))
        self.character = QComboBox()
        for key, profile in CHARACTERS.items():
            self.character.addItem(profile['name'], key)
        self.character.setCurrentIndex(max(0, self.character.findData(settings.character)))
        layout.addRow('Reminder interval:', self.interval)
        layout.addRow('First snooze:', self.short_snooze)
        layout.addRow('Second snooze:', self.long_snooze)
        layout.addRow('Preferred monitor:', self.monitor)
        layout.addRow('Character:', self.character)
        layout.addRow(self.sound)
        layout.addRow(self.autostart)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

class Companion(QWidget):
    def __init__(self, data_dir=DATA):
        super().__init__()
        self.setWindowTitle('Fahadh Water Companion')
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(400, 380)
        self.data_dir = data_dir
        self.settings = Settings(data_dir / 'settings.json')
        self.schedule = Schedule(data_dir / 'reminder.json', time.time(), self.settings.interval_minutes * 60)
        self.error_shown = False
        self.persist(self.schedule.save)
        self.direction, self.phase = 1, 0
        self.drag_offset = None
        self.board_kind = None
        self.motion = None
        self.reaction = None
        self.motion_target_x = 0
        self.motion_frames_remaining = 0
        self.frames = []
        self.expression_frames = {}
        self.apply_character(self.settings.character)

        self.icon = QIcon(self.frames[3])
        self.setWindowIcon(self.icon)
        self.board = QFrame(self)
        self.board.setGeometry(8, 8, 384, 160)
        self.board.setStyleSheet('QFrame {background:#fffaf0; border:2px solid #147d76; border-radius:16px;} QLabel {border:0; background:transparent; color:#183d3a;} QPushButton {background:#147d76;color:white;border:0;border-radius:8px;padding:8px;font-weight:600;} QPushButton:hover {background:#0b605b;} QPushButton:pressed {background:#084d49;} QPushButton:focus {border:2px solid #f5b700;}')
        self.eyebrow = QLabel('A LITTLE PAUSE', self.board)
        self.eyebrow.setGeometry(16, 10, 350, 22)
        self.eyebrow.setFont(QFont('Segoe UI', 9, QFont.Weight.Bold))
        self.title = QLabel('Time for some water', self.board)
        self.title.setGeometry(16, 34, 352, 30)
        self.title.setFont(QFont('Segoe UI', 16, QFont.Weight.Bold))
        self.detail = QLabel('Take a sip. Your next break is in two hours.', self.board)
        self.detail.setGeometry(16, 66, 352, 35)
        self.detail.setWordWrap(True)
        self.detail.setFont(QFont('Segoe UI', 10))
        self.done = QPushButton('Done', self.board)
        self.done.setGeometry(16, 112, 100, 34)
        self.done.clicked.connect(self.acknowledge)
        self.snooze_five = QPushButton('Snooze 5 min', self.board)
        self.snooze_five.setGeometry(124, 112, 116, 34)
        self.snooze_five.clicked.connect(lambda: self.snooze_reminder(self.settings.snooze_short_minutes * 60))
        self.snooze_ten = QPushButton('Snooze 10 min', self.board)
        self.snooze_ten.setGeometry(248, 112, 120, 34)
        self.snooze_ten.clicked.connect(lambda: self.snooze_reminder(self.settings.snooze_long_minutes * 60))
        self.board.hide()
        self.menu = QMenu(self)
        self.menu.addAction('Test reminder', self.test_reminder)
        self.menu.addAction('Settings…', self.open_settings)
        self.pause_action = self.menu.addAction('Pause reminders')
        self.pause_action.setCheckable(True)
        self.pause_action.setChecked(self.schedule.paused)
        self.pause_action.triggered.connect(self.toggle_pause)
        self.menu.addAction('Move to next monitor', self.next_monitor)
        self.menu.addSeparator()
        self.menu.addAction('Quit', QApplication.instance().quit)
        self.tray = QSystemTrayIcon(self.icon, self)
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self.tray_clicked)
        self.tray.show()
        screens = QApplication.screens()
        self.monitor = screens[min(self.settings.preferred_monitor, len(screens) - 1)]
        QApplication.instance().screenRemoved.connect(self.screen_removed)
        for screen in QApplication.screens():
            screen.availableGeometryChanged.connect(self.fit_screen)
        self.fit_screen()
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self.check_due)
        self.check_timer.start(5000)
        self.motion_timer = QTimer(self)
        self.motion_timer.timeout.connect(self.animate_motion)
        self.motion_timer.setInterval(220)
        self.check_due()
        self.refresh_snooze_labels()

    def apply_character(self, character):
        profile = CHARACTERS.get(character, CHARACTERS['friendly'])
        sheet = QPixmap(str(ROOT / 'assets' / profile['walk']))
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
        self.expression_frames = {
            'reminder': self.load_sprite(profile['reminder']),
            'happy': self.load_sprite(profile['happy']),
            'snooze': self.load_sprite(profile['snooze']),
        }
        if hasattr(self, 'tray'):
            self.icon = QIcon(self.frames[3])
            self.setWindowIcon(self.icon)
            self.tray.setIcon(self.icon)
            self.update_shape()

    def load_sprite(self, filename):
        pix = QPixmap(str(ROOT / 'assets' / filename))
        if pix.isNull():
            raise RuntimeError(f'Character artwork is missing: {filename}')
        bounds = QRegion(pix.mask()).boundingRect()
        if bounds.isEmpty():
            raise RuntimeError(f'Character artwork is empty: {filename}')
        return pix.copy(bounds).scaledToHeight(194, Qt.TransformationMode.SmoothTransformation)

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
        if self.motion:
            frame = self.frames[[0, 1, 2, 1][self.phase % 4]]
        elif self.reaction:
            frame = self.expression_frames[self.reaction]
        elif self.board.isVisible():
            frame = self.expression_frames['reminder']
        else:
            frame = self.frames[3]
        return frame.transformed(QTransform().scale(-1, 1)) if self.direction < 0 else frame

    def sprite_rect(self, pix):
        return QRect((self.width() - pix.width()) // 2, self.height() - pix.height(), pix.width(), pix.height())

    def update_shape(self):
        pix = self.current_pixmap()
        rect = self.sprite_rect(pix)
        region = QRegion(pix.mask()).translated(rect.topLeft())
        if self.board.isVisible():
            region = region.united(QRegion(self.board.geometry()))
        self.setMask(region)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        pix = self.current_pixmap()
        painter.drawPixmap(self.sprite_rect(pix).topLeft(), pix)

    def show_board(self, kind):
        self.board_kind = kind
        self.reaction = None
        self.board.hide()
        self.direction = 1
        area = self.monitor.availableGeometry()
        walk_distance = max(160, min(280, round(self.monitor.logicalDotsPerInchX() * 5.5 / 2.54)))
        self.motion_target_x = area.left() + 12
        self.move(self.motion_target_x - walk_distance, area.bottom() - self.height() + 1)
        self.motion = 'enter'
        self.phase = 0
        self.motion_frames_remaining = 20
        self.show()
        self.motion_timer.start()
        self.update_shape()

    def present_board(self):
        kind = self.board_kind
        preview = kind == 'test'
        profile = CHARACTERS[self.settings.character]
        self.eyebrow.setText('PREVIEW • NO TIMER CHANGE' if preview else ('RANGA’S HYDRATION CHECK' if self.settings.character == 'ranga' else 'A LITTLE PAUSE'))
        self.title.setText(random.choice(profile['reminders']))
        self.detail.setText('Choose wisely.' if self.settings.character == 'ranga' else 'A few sips now will help keep you going.')
        self.done.setText('Done')
        self.done.setGeometry(16, 112, 100, 34)
        self.snooze_five.show()
        self.snooze_ten.show()
        self.board.show()
        self.update_shape()
        if kind == 'reminder' and self.settings.sound_enabled:
            QApplication.beep()

    def animate_motion(self):
        self.phase += 1
        distance_left = self.motion_target_x - self.x()
        if distance_left == 0:
            step = 0
        else:
            step = round(distance_left / max(1, self.motion_frames_remaining))
            if step == 0:
                step = 1 if distance_left > 0 else -1
        next_x = self.x() + step
        self.motion_frames_remaining -= 1
        reached = self.motion_frames_remaining <= 0 or distance_left == 0
        if step > 0:
            reached = reached or next_x >= self.motion_target_x
        elif step < 0:
            reached = reached or next_x <= self.motion_target_x
        self.move(self.motion_target_x if reached else next_x, self.y())
        self.update_shape()
        if not reached:
            return
        self.motion_timer.stop()
        if self.motion == 'enter':
            self.motion = None
            self.direction = 1
            self.present_board()
        else:
            self.finish_exit()

    def begin_exit(self):
        if self.reaction is None and self.board_kind is None and not self.isVisible():
            return
        self.board.hide()
        self.reaction = None
        self.motion = 'exit'
        self.direction = -1
        walk_distance = max(160, min(280, round(self.monitor.logicalDotsPerInchX() * 5.5 / 2.54)))
        self.motion_target_x = self.x() - walk_distance
        self.phase = 0
        self.motion_frames_remaining = 20
        self.motion_timer.start()
        self.update_shape()

    def react_then_exit(self, reaction):
        self.motion_timer.stop()
        self.motion = None
        self.board_kind = None
        self.reaction = reaction
        self.direction = 1
        profile = CHARACTERS[self.settings.character]
        responses = profile['done'] if reaction == 'happy' else profile['snoozed']
        self.eyebrow.setText('RANGA APPROVES' if self.settings.character == 'ranga' and reaction == 'happy' else ('FINAL WARNING' if self.settings.character == 'ranga' else 'SEE YOU SOON'))
        self.title.setText(random.choice(responses))
        self.detail.setText('Hydration acknowledged.' if reaction == 'happy' else 'I’ll return after the snooze.')
        self.done.hide()
        self.snooze_five.hide()
        self.snooze_ten.hide()
        self.board.show()
        self.update_shape()
        QTimer.singleShot(1600, self.begin_exit)

    def finish_exit(self):
        self.motion_timer.stop()
        self.motion = None
        self.reaction = None
        self.board_kind = None
        self.board.hide()
        self.hide()
        self.update_shape()

    def dismiss_board(self):
        self.finish_exit()

    def acknowledge(self):
        if self.board_kind == 'reminder':
            self.persist(lambda: self.schedule.postpone(time.time()))
        self.react_then_exit('happy')

    def snooze_reminder(self, seconds):
        if self.board_kind == 'reminder':
            self.persist(lambda: self.schedule.postpone(time.time(), seconds))
        self.react_then_exit('snooze')

    def refresh_snooze_labels(self):
        self.snooze_five.setText(f'Snooze {self.settings.snooze_short_minutes} min')
        self.snooze_ten.setText(f'Snooze {self.settings.snooze_long_minutes} min')

    def open_settings(self):
        dialog = SettingsDialog(self.settings, QApplication.screens(), self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        previous_autostart = self.settings.start_with_windows
        self.settings.values.update({
            'interval_minutes': dialog.interval.value(),
            'snooze_short_minutes': dialog.short_snooze.value(),
            'snooze_long_minutes': dialog.long_snooze.value(),
            'sound_enabled': dialog.sound.isChecked(),
            'preferred_monitor': dialog.monitor.currentIndex(),
            'start_with_windows': dialog.autostart.isChecked(),
            'character': dialog.character.currentData(),
        })
        self.schedule.interval = self.settings.interval_minutes * 60
        self.monitor = QApplication.screens()[self.settings.preferred_monitor]
        self.fit_screen()
        self.refresh_snooze_labels()
        self.apply_character(self.settings.character)
        self.persist(self.settings.save)
        if previous_autostart != self.settings.start_with_windows:
            self.persist(lambda: set_start_with_windows(self.settings.start_with_windows))

    def test_reminder(self):
        if self.board_kind is None and not self.motion and not self.reaction:
            self.show_board('test')

    def check_due(self):
        if self.schedule.due(time.time()) and self.board_kind != 'reminder':
            self.show_board('reminder')
        remaining = max(0, math.ceil((self.schedule.next_due - time.time()) / 60))
        text = 'Paused' if self.schedule.paused else ('Water break is due' if remaining == 0 else f'Next water break in {remaining} min')
        self.tray.setToolTip(CHARACTERS[self.settings.character]['name'] + ' — ' + text)

    def toggle_pause(self, paused):
        self.persist(lambda: self.schedule.pause(paused, time.time()))
        self.dismiss_board()
        self.check_due()

    def tray_clicked(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.test_reminder()

    def contextMenuEvent(self, event):
        self.menu.exec(event.globalPos())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.motion:
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
