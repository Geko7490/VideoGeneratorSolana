"""Blender runs only a fixed application script with a validated JSON scene."""
import math
import subprocess
import tempfile
from pathlib import Path

from .runtime import NO_WINDOW
from .storage import atomic_json


def encode_3d(scene, width, height, fps, output, context, ffmpeg, settings, report):
    blender = Path(settings.get("blender", ""))
    if not blender.is_file():
        raise FileNotFoundError("3D render için Ayarlar'da Blender executable seçin")
    for node in scene.nodes:
        if node.kind in ("path", "particles") or node.gradient or node.clip or node.text_effect != "none":
            raise ValueError(f"3D motorunda desteklenmeyen 2D/motion özelliği: {node.id}")
        if node.opacity not in (0, 1) or any(k.value not in (0, 1) for t in node.tracks if t.property == "opacity" for k in t.keys):
            raise ValueError("İlk 3D motorunda yalnızca görünür/gizli opacity desteklenir")
    script = Path(__file__).with_name("blender_runtime.py")
    frames = math.ceil(scene.duration * fps)
    from .export import run_process
    with tempfile.TemporaryDirectory(prefix="vex-3d-", dir=output.parent) as temporary:
        root = Path(temporary)
        manifest = root / "scene.json"
        frame_dir = root / "frames"
        atomic_json(manifest, dict(scene=scene.model_dump(), width=width, height=height, fps=fps))
        with (root / "blender.log").open("w+b") as log:
            process = subprocess.Popen([str(blender), "--background", "--factory-startup", "--python", str(script), "--", str(manifest), str(frame_dir)], stdout=log, stderr=log, creationflags=NO_WINDOW)
            try:
                while process.poll() is None:
                    context.check()
                    count = len(list(frame_dir.glob("*.png"))) if frame_dir.exists() else 0
                    report(.95 * count / frames)
                    context.cancel.wait(.2)
                if process.returncode:
                    log.seek(0)
                    raise RuntimeError(log.read().decode(errors="replace")[-5000:])
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
        partial = output.with_suffix(".partial.mp4")
        try:
            run_process([ffmpeg, "-y", "-v", "error", "-framerate", str(fps), "-i", str(frame_dir / "%06d.png"), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", str(partial)], context)
            partial.replace(output)
            report(1)
        finally:
            partial.unlink(missing_ok=True)
