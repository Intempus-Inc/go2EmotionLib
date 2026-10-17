"""Read and inspect Go2 authoring timelines without connecting to hardware."""

from importlib.resources import files
import json
import math
from pathlib import Path

__all__ = ["names", "load", "load_file", "timeline", "action_events"]


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _number(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number")
    try:
        valid = math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError(f"{field} must be a finite number")
    return value


def _validate(data):
    if not isinstance(data, dict) or data.get("version") != "2.0" or data.get("robotType") != "unitree_go2":
        raise ValueError("expected a version 2.0 unitree_go2 recording")
    duration = _number(data.get("duration"), "duration")
    frames = data.get("keyframes")
    if duration < 0 or not isinstance(frames, list) or not frames:
        raise ValueError("expected a nonnegative duration and nonempty keyframes")
    for frame in frames:
        if not isinstance(frame, dict):
            raise ValueError("each keyframe must be an object")
        time = _number(frame.get("timestamp"), "timestamp")
        if not 0 <= time <= duration:
            raise ValueError("keyframe timestamp must lie within the recording duration")
        if frame.get("duration") is not None and _number(frame["duration"], "keyframe duration") < 0:
            raise ValueError("keyframe duration must be nonnegative")
        layers, weights = frame.get("layers"), frame.get("blendWeights")
        if not isinstance(layers, dict) or not isinstance(weights, dict):
            raise ValueError("layers and blendWeights must be objects")
        for name in ("perpetual", "periodic", "episodic"):
            layer = layers.get(name)
            if not isinstance(layer, dict) or type(layer.get("active")) is not bool:
                raise ValueError(f"{name} must have a boolean active field")
            if not 0 <= _number(weights.get(name), f"{name} blend weight") <= 1:
                raise ValueError("blend weights must be between zero and one")
        for group, fields in (("torso", ("height", "roll", "pitch", "yaw")), ("head", ("height", "roll", "pitch", "yaw"))):
            values = layers["perpetual"].get(group)
            if not isinstance(values, dict):
                raise ValueError(f"perpetual.{group} must be an object")
            for field in fields:
                _number(values.get(field), f"{group}.{field}")
        periodic = layers["periodic"]
        if periodic["active"]:
            interval = _number(periodic.get("duration"), "periodic.duration")
            if interval <= 0 or time + interval > duration + 1e-9:
                raise ValueError("active periodic interval must be positive and fit the recording")
        velocity = periodic.get("velocity")
        if not isinstance(velocity, dict):
            raise ValueError("periodic.velocity must be an object")
        for field in ("vx", "vy", "vyaw"):
            _number(velocity.get(field), f"velocity.{field}")
        _number(periodic.get("phase"), "periodic.phase")
        for layer, field in (("perpetual", "mode"), ("periodic", "gait"), ("episodic", "action")):
            value = layers[layer].get(field)
            if value is not None and (not isinstance(value, str) or not value):
                raise ValueError(f"{layer}.{field} must be a nonempty string or null")
            if layers[layer]["active"] and not value:
                raise ValueError(f"active {layer} requires {field}")
    return data


def names():
    """List bundled recording filenames without their extension."""
    return tuple(sorted(p.name[:-5] for p in files("go2_motion").iterdir() if p.name.endswith(".json")))


def load(name):
    """Load a fresh dictionary, preserving stored frame order. Accept 'surprise' too."""
    if not isinstance(name, str):
        raise ValueError("name must be a string")
    available = {n.casefold(): n for n in names()}
    available["surprise"] = "suprise"
    if name.casefold() not in available:
        raise ValueError(f"unknown motion: {name!r}; use names() to list recordings")
    resource = files("go2_motion").joinpath(available[name.casefold()] + ".json")
    return _validate(json.loads(resource.read_text(encoding="utf-8"), object_pairs_hook=_object))


def load_file(path):
    """Load a local recording with the same structure checks as bundled data."""
    return _validate(json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=_object))


def timeline(motion):
    """Return a sorted tuple of frames, preserving input order at equal timestamps."""
    _validate(motion)
    return tuple(sorted(motion["keyframes"], key=lambda frame: frame["timestamp"]))


def action_events(motion):
    """List (seconds, action) markers chronologically, without executing them."""
    return tuple((frame["timestamp"], frame["layers"]["episodic"]["action"])
                 for frame in timeline(motion) if frame["layers"]["episodic"]["active"])
