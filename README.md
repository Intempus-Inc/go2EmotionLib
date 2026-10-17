# Go2 motion library

27 expressive Go2 authoring timelines with 243 keyframes, 38 movement intervals, and 26 action markers. A small Python package reads and inspects them offline.

## Use

Requires Python 3.10 or later. From a clone of this repository:

```sh
python -m pip install .
python -m go2_motion relief
```

```python
from go2_motion import load, timeline, action_events

motion = load("joy")
for frame in timeline(motion):
    print(frame["timestamp"], frame["layers"])
print(action_events(load("relief")))
```

`names()` lists recordings; `load_file(path)` reads the same format. `load()` returns a fresh dictionary in stored order. `timeline()` returns a chronological view without changing it; equal-time frames retain their input order. `action_events()` lists every active action marker. Neither function interpolates or sends commands.

## Format and limits

Version `2.0`, robot type `unitree_go2`. Clip duration, keyframe `timestamp`, and active `periodic.duration` are seconds. The filename identifies the recording; the original internal name is generic. The loader accepts both `suprise` and `surprise`.

| Layer | Stored fields |
| --- | --- |
| `perpetual` | Pose mode, torso and head height, roll, pitch, yaw |
| `periodic` | Gait, velocity (`vx`, `vy`, `vyaw`), phase, interval duration |
| `episodic` | Named action at the frame timestamp |

Each layer has an `active` flag. Torso angles are radians; `vx` and `vy` use m/s and `vyaw` uses rad/s. All stored blend weights are 1. Height, head, and phase fields have no verified physical mapping. These are high-level authoring settings; they require an explicit controller mapping.

Three files contain frames out of time order. `Awkwardness` has overlapping movement intervals, and the original players disagree about how to combine them. Craving and Nostalgia share layer sequences with different timing. Four saved playback-state flags were removed; they must not suppress action markers on a new run.

The original players also omit fields and use different interpolation rules. This package defines no hardware playback policy. Emotion names describe animation intent, not measured viewer responses.

## Development and license

After installation, run `python -m unittest discover -s tests`.

Code: [MIT](LICENSE). Motion JSON files: [CC BY 4.0](LICENSE-DATA), attributed to Intempus, Inc. Cite the repository and note modifications when reusing the data.
