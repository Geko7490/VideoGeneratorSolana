"""Real model acceptance test for the onedir executable (requires local model settings)."""
import argparse
import json
import subprocess
import time
from pathlib import Path
from uuid import uuid4

from vex.runtime import NO_WINDOW, ffmpeg_path

parser = argparse.ArgumentParser()
parser.add_argument("--settings", type=Path, default=Path("data/settings.json"))
parser.add_argument("--package", type=Path, default=Path("dist/VEXVideo/VEXVideo.exe"))
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
data = root / "data" / "frozen-tests" / uuid4().hex
data.mkdir(parents=True)
(data / "settings.json").write_text(args.settings.read_text(encoding="utf-8"), encoding="utf-8")
story = "A small robot wakes up in an abandoned city. It walks toward a glowing tower and discovers a mysterious message."
command = [str(args.package.resolve()), "generate", "--data-dir", str(data), "--title", "Frozen acceptance", "--story", story, "--preview", "--voice"]
started = time.monotonic()
process = subprocess.Popen(command, creationflags=NO_WINDOW)
try:
    code = process.wait(timeout=150)
except subprocess.TimeoutExpired:
    # Only the process tree created by this test is terminated.
    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, creationflags=NO_WINDOW)
    raise
if code:
    raise RuntimeError(f"Frozen executable failed: {code}; logs: {data}")
outputs = list((data / "projects").glob("*/exports/preview.mp4"))
if len(outputs) != 1:
    raise RuntimeError(f"Expected one new MP4, found {len(outputs)}; logs: {data}")
output = outputs[0]
subprocess.run([ffmpeg_path(), "-v", "error", "-i", str(output), "-f", "null", "-"], check=True, capture_output=True, creationflags=NO_WINDOW, timeout=30)
alignment = json.loads((output.parents[1] / "subtitles/alignment.json").read_text())
report = dict(exit_code=code, seconds=round(time.monotonic()-started, 2), output_bytes=output.stat().st_size,
              alignment=alignment["similarity"], uses_real_llm_tts_whisper=True,
              output=str(output.relative_to(root)))
(root / "docs/frozen-acceptance.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2), flush=True)
