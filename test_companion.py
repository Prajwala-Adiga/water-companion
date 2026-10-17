import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import tempfile
import unittest
from pathlib import Path
from schedule import Schedule, INTERVAL
from settings import Settings

class TimingTests(unittest.TestCase):
    def test_custom_interval(self):
        with tempfile.TemporaryDirectory() as tmp:
            s = Schedule(Path(tmp) / 'state.json', 100, interval=30 * 60)
            self.assertEqual(s.next_due, 1900)
            s.postpone(200)
            self.assertEqual(s.next_due, 2000)

    def test_settings_validation_and_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'settings.json'
            settings = Settings(path)
            settings.values['interval_minutes'] = 90
            settings.values['sound_enabled'] = True
            settings.values['character'] = 'ranga'
            settings.save()
            restored = Settings(path)
            self.assertEqual(restored.interval_minutes, 90)
            self.assertTrue(restored.sound_enabled)
            self.assertEqual(restored.character, 'ranga')

    def test_restart_and_sleep(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'state.json'
            first = Schedule(path, 1000)
            first.save()
            restored = Schedule(path, 1500)
            self.assertEqual(restored.next_due, 1000 + INTERVAL)
            self.assertFalse(restored.due(8199))
            self.assertTrue(restored.due(8200))
            self.assertTrue(restored.due(50000))

    def test_snooze_pause_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            s = Schedule(Path(tmp) / 'state.json', 0)
            s.postpone(7200, 600)
            self.assertFalse(s.due(7799))
            self.assertTrue(s.due(7800))
            s.pause(True, 7800)
            self.assertFalse(s.due(100000))
            self.assertTrue(Schedule(s.path, 100000).paused)
            s.pause(False, 100000)
            self.assertEqual(s.next_due, 107200)

    def test_invalid_state_recovers(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'state.json'
            for value in ['bad json', '{"next_due": "NaN"}', '{"next_due": null}']:
                path.write_text(value)
                self.assertEqual(Schedule(path, 50).next_due, 7250)

class InterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_preview_due_snooze_and_pause(self):
        from app import Companion
        import time
        with tempfile.TemporaryDirectory() as tmp:
            pet = Companion(Path(tmp))
            pet.check_timer.stop()
            self.assertFalse(pet.isVisible())
            pet.settings.values['character'] = 'ranga'
            pet.apply_character('ranga')
            self.assertEqual(pet.settings.character, 'ranga')
            original = pet.schedule.next_due
            pet.test_reminder()
            self.assertTrue(pet.isVisible())
            pet.motion_target_x = pet.x()
            pet.animate_motion()
            self.assertTrue(pet.board.isVisible())
            self.assertTrue(pet.done.isVisible())
            self.assertTrue(pet.title.wordWrap())
            pet.acknowledge()
            self.assertEqual(pet.reaction, 'happy')
            pet.finish_exit()
            self.assertFalse(pet.isVisible())
            self.assertEqual(pet.schedule.next_due, original)
            pet.test_reminder()
            pet.motion_target_x = pet.x()
            pet.animate_motion()
            self.assertTrue(pet.done.isVisible())
            pet.snooze_reminder(300)
            self.assertEqual(pet.schedule.next_due, original)
            self.assertEqual(pet.reaction, 'snooze')
            pet.finish_exit()
            pet.schedule.next_due = time.time() - 1
            pet.check_due()
            self.assertEqual(pet.board_kind, 'reminder')
            pet.test_reminder()
            self.assertEqual(pet.board_kind, 'reminder')
            pet.snooze_reminder(300)
            self.assertEqual(pet.reaction, 'snooze')
            self.assertIsNone(pet.board_kind)
            pet.finish_exit()
            self.assertFalse(pet.isVisible())
            self.assertAlmostEqual(pet.schedule.next_due - time.time(), 300, delta=2)
            pet.schedule.next_due = time.time() - 1
            pet.check_due()
            pet.snooze_reminder(600)
            pet.finish_exit()
            self.assertAlmostEqual(pet.schedule.next_due - time.time(), 600, delta=2)
            pet.toggle_pause(True)
            self.assertTrue(pet.schedule.paused)
            pet.toggle_pause(False)
            self.assertAlmostEqual(pet.schedule.next_due - time.time(), INTERVAL, delta=2)
            pet.show_board('reminder')
            pet.motion_target_x = pet.x()
            pet.animate_motion()
            self.app.processEvents()
            pet.grab().save(str(Path(tmp).parent / 'water-companion-preview.png'))
            pet.tray.hide()
            pet.close()
            pet.deleteLater()

if __name__ == '__main__':
    unittest.main()
