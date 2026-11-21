"""Reproduce the matched authorization study with no model credentials."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def command(*args, data=None):
    return subprocess.check_output([sys.executable, *map(str, args)], cwd=ROOT, input=data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("demo-output"))
    directory = parser.parse_args().out.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    for profile in ("stale", "registry"):
        command("study.py", "run", "--profile", profile, "--count", "8", "--out", directory / profile)
    comparison = command("study.py", "compare", directory / "stale", directory / "registry",
                         "--html", directory / "comparison.html")
    (directory / "comparison.json").write_bytes(comparison)
    turns = command("study.py", "monitor", directory / "stale")
    predictions = directory / "predictions.json"
    predictions.write_bytes(command("dispatch_monitor.py", data=turns))
    monitor = command("study.py", "monitor", directory / "stale", "--predictions", predictions)
    (directory / "monitor.json").write_bytes(monitor)
    counts = json.loads(comparison)["slices"]["All matched"]
    if (counts["n"], counts["left_pass"], counts["right_pass"], counts["left_unsafe"]) != (64, 32, 64, 16):
        raise RuntimeError("Calibration episode counts differ from the reference")
    metrics = json.loads(monitor)
    if [metrics[k] for k in ("TP", "FP", "TN", "FN")] != [16, 0, 112, 0]:
        raise RuntimeError("Calibration monitor counts differ from the reference")
    print("128 scripted episodes. All reference counts reproduced.")
    print(directory / "comparison.html")


if __name__ == "__main__":
    main()
