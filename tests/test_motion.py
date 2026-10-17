import copy
import json
from pathlib import Path
import tempfile
import unittest

import go2_motion as library


class MotionTests(unittest.TestCase):
    def test_all_recordings(self):
        self.assertEqual(len(library.names()), 27)
        frames = events = intervals = 0
        for name in library.names():
            motion = library.load(name)
            frames += len(motion["keyframes"])
            events += len(library.action_events(motion))
            intervals += sum(f["layers"]["periodic"]["active"] for f in motion["keyframes"])
            times = [f["timestamp"] for f in library.timeline(motion)]
            self.assertEqual(times, sorted(times))
        self.assertEqual((frames, events, intervals), (243, 26, 38))

    def test_timeline_preserves_original_order(self):
        for name in ("aestheticappreciation", "fear", "suprise"):
            motion = library.load(name)
            original = copy.deepcopy(motion)
            self.assertNotEqual(list(library.timeline(motion)), motion["keyframes"])
            self.assertEqual(motion, original)

    def test_action_events_include_previously_executed_markers(self):
        self.assertEqual(library.action_events(library.load("relief")), (
            (1.0298869397654726, "stand_down"), (6.6, "stand_up"), (6.8, "balance_stand")))
        motion = library.load("relief")
        for frame in motion["keyframes"]:
            frame["_episodicExecuted"] = True
        self.assertEqual(library.action_events(motion), library.action_events(library.load("relief")))

    def test_equal_time_events_are_not_dropped(self):
        motion = library.load("craving")
        for frame in motion["keyframes"]:
            frame["timestamp"] = 1
        self.assertEqual(library.action_events(motion), ((1, "sit"), (1, "rise_sit"), (1, "balance_stand")))

    def test_names_and_independent_loads(self):
        self.assertEqual(library.load("Surprise"), library.load("suprise"))
        motion = library.load("JOY")
        motion["keyframes"].clear()
        self.assertEqual(len(library.load("joy")["keyframes"]), 20)
        for name in ("../joy", None, "joy.json", "unknown"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                library.load(name)

    def test_invalid_files(self):
        base = library.load("joy")
        cases = [[], {}, dict(base, version="1.0"), dict(base, keyframes=[]), dict(base, duration=True)]
        for time in (-1, True, float("nan"), float("inf"), 10**1000, base["duration"] + 1):
            candidate = copy.deepcopy(base)
            candidate["keyframes"][0]["timestamp"] = time
            cases.append(candidate)
        candidate = copy.deepcopy(base)
        candidate["keyframes"][0]["layers"]["periodic"].update(active=True, duration=-1)
        cases.append(candidate)
        candidate = copy.deepcopy(base)
        candidate["keyframes"][0]["layers"]["episodic"].update(active=True, action=None)
        cases.append(candidate)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "motion.json"
            path.write_text(json.dumps(base))
            self.assertEqual(library.load_file(path), base)
            for data in cases:
                path.write_text(json.dumps(data))
                with self.subTest(data=data), self.assertRaises(ValueError):
                    library.load_file(path)
            path.write_text('{"version":"2.0", "version":"1.0"}')
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                library.load_file(path)


if __name__ == "__main__":
    unittest.main()
