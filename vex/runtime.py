from __future__ import annotations

import importlib.util
import shutil
import subprocess
from pathlib import Path

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def ffmpeg_path(configured=""):
    if configured:
        if not Path(configured).is_file():
            raise FileNotFoundError("FFmpeg yolu bulunamadı")
        return str(Path(configured).resolve())
    system = shutil.which("ffmpeg")
    if system:
        return system
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def doctor(settings=None):
    settings = settings or {}
    result = {}
    try:
        process = subprocess.run([ffmpeg_path(settings.get("ffmpeg", "")), "-version"], capture_output=True, text=True, timeout=15, creationflags=NO_WINDOW)
        result["ffmpeg"] = process.stdout.splitlines()[0] if process.returncode == 0 else process.stderr[:300]
    except Exception as exc:
        result["ffmpeg"] = str(exc)
    for key in ("llama_server", "gguf", "kokoro_model", "kokoro_voices", "whisper_model", "blender"):
        path = settings.get(key, "")
        result[key] = "Hazır: " + path if path and Path(path).exists() else "Seçilmedi / bulunamadı"
    model_path = Path(settings.get("gguf", ""))
    if model_path.is_file():
        with model_path.open("rb") as handle:
            result["gguf_header"] = "GGUF" if handle.read(4) == b"GGUF" else "Geçersiz GGUF başlığı"
        result["model_size_mib"] = round(model_path.stat().st_size / 1048576, 1)
    server = Path(settings.get("llama_server", ""))
    if server.is_file():
        try:
            probe = subprocess.run([str(server), "--list-devices"], capture_output=True, text=True, timeout=20, creationflags=NO_WINDOW)
            result["devices"] = probe.stdout.strip() + probe.stderr.strip()
        except (OSError, subprocess.TimeoutExpired) as exc:
            result["devices"] = str(exc)
    for module in ("kokoro_onnx", "faster_whisper", "soundfile"):
        result[module] = "Kurulu" if importlib.util.find_spec(module) else "Kurulu değil (audio extra)"
    return result
