import argparse
import json
from . import action_events, load, names


def main():
    parser = argparse.ArgumentParser(description="Inspect a Go2 authoring timeline.")
    parser.add_argument("name", nargs="?", help="recording name; omit to list")
    args = parser.parse_args()
    if args.name is None:
        print("\n".join(names()))
        return
    try:
        motion = load(args.name)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps({"recording": args.name, "duration": motion["duration"],
                      "keyframes": len(motion["keyframes"]), "actions": action_events(motion)}, indent=2))


if __name__ == "__main__":
    main()
