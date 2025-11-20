# Minecraft capture starter

This helper demonstrates the first step of the agentic Minecraft assistant: capturing frames from the game window (or a chosen monitor region) at a fixed interval.

## Setup
1. Install dependencies (requires `mss`):
   ```bash
   pip install -r requirements.txt
   ```
2. Ensure Minecraft is visible on the target monitor or within the bounding box you plan to record.

## Usage
Run the capture script and save frames to `captures/`:
```bash
python minecraft_capture.py --interval 0.3 --duration 120 --monitor 1
```

Key options:
- `--interval`: Seconds between frames (e.g., `0.25` ≈ 4 FPS).
- `--duration`: Total seconds to record (`0` to run until you stop with `Ctrl+C`).
- `--monitor`: Monitor index to capture (1 = primary). Ignored when `--bbox` is provided.
- `--bbox LEFT TOP WIDTH HEIGHT`: Capture only a specific rectangle instead of a full monitor.
- `--output-dir`: Directory for saved PNGs (default `captures/`).
- `--prefix`: Filename prefix (default `minecraft`).

Example capturing a 1280×720 region starting at (100, 100):
```bash
python minecraft_capture.py --interval 0.25 --duration 60 --bbox 100 100 1280 720
```

After capture, PNG frames can be fed into your Ollama vision prompt loop for analysis and overlay rendering.
