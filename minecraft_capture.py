"""
Minimal screen-capture loop for Minecraft frames.

This script implements the first step of the agentic assistant pipeline:
capturing frames from the game window (or a chosen monitor region) at a
configurable interval. Frames are saved to disk so they can be fed into a
vision model or further processing loop.
"""

import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import Dict

import mss
import mss.tools


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture Minecraft frames at a fixed interval and save to disk."
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.5,
        help="Seconds between captures (e.g., 0.25 for 4 FPS).",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=30,
        help="Total seconds to run capture. Use 0 for unlimited until interrupted.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("captures"),
        help="Directory to store captured frames.",
    )
    parser.add_argument(
        "--monitor",
        type=int,
        default=1,
        help="Monitor index for capture (1 = primary). Ignored when --bbox is set.",
    )
    parser.add_argument(
        "--bbox",
        type=int,
        nargs=4,
        metavar=("LEFT", "TOP", "WIDTH", "HEIGHT"),
        help="Bounding box to capture (pixels). Overrides monitor selection.",
    )
    parser.add_argument(
        "--prefix",
        default="minecraft",
        help="Filename prefix for saved frames.",
    )
    return parser.parse_args()


def build_region(args: argparse.Namespace, sct: mss.mss) -> Dict[str, int]:
    """Return a monitor region dict for mss based on CLI args."""
    if args.bbox:
        left, top, width, height = args.bbox
        return {"left": left, "top": top, "width": width, "height": height}

    monitors = sct.monitors
    if args.monitor < 1 or args.monitor >= len(monitors):
        raise ValueError(
            f"Monitor index {args.monitor} out of range. Available: 1..{len(monitors)-1}"
        )
    return monitors[args.monitor]


def capture_frames(args: argparse.Namespace) -> None:
    args.output_dir.mkdir(parents=True, exist_ok=True)
    saved = 0
    with mss.mss() as sct:
        region = build_region(args, sct)
        start_time = time.perf_counter()
        end_time = start_time + args.duration if args.duration > 0 else float("inf")

        print(f"Capturing region {region} every {args.interval:.2f}s...")
        while True:
            now = time.perf_counter()
            if now >= end_time:
                break

            frame = sct.grab(region)
            timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S_%f")
            filename = args.output_dir / f"{args.prefix}_{timestamp}.png"
            mss.tools.to_png(frame.rgb, frame.size, output=str(filename))
            saved += 1
            time.sleep(args.interval)

    print(f"Saved {saved} frames to {args.output_dir.resolve()}")


def main() -> None:
    args = parse_args()
    try:
        capture_frames(args)
    except KeyboardInterrupt:
        print("\nCapture stopped by user.")
    except Exception as exc:  # noqa: BLE001 (simple CLI entrypoint)
        print(f"Error: {exc}")
        raise


if __name__ == "__main__":
    main()
