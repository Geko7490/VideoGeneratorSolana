"""Explicit first-run downloads; all inference remains local afterwards."""
from __future__ import annotations

import hashlib
import shutil
import urllib.request
import zipfile
from pathlib import Path

from .storage import atomic_json

CATALOG = {
    "gguf": ("https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf", "models/qwen2.5-1.5b.gguf"),
    "kokoro_model": ("https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx", "models/kokoro-v1.0.onnx"),
    "kokoro_voices": ("https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin", "models/voices-v1.0.bin"),
    "llama_archive": ("https://github.com/ggml-org/llama.cpp/releases/download/b12110/llama-b12110-bin-win-vulkan-x64.zip", "runtime/llama.zip"),
}


def download(url, path: Path, context):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".part")
    try:
        with urllib.request.urlopen(url, timeout=30) as response, temporary.open("wb") as handle:
            size = int(response.headers.get("Content-Length", 0))
            received = 0
            digest = hashlib.sha256()
            while chunk := response.read(1024 * 1024):
                context.check()
                handle.write(chunk)
                digest.update(chunk)
                received += len(chunk)
                context.report(received / size if size else 0, f"{path.name}: {received/1048576:.1f} MB" + (f" / {size/1048576:.1f} MB" if size else " (toplam bilinmiyor)"))
            if not received or (size and received != size):
                raise ValueError("İndirme tamamlanmadı")
        temporary.replace(path)
        atomic_json(path.with_name(path.name + ".download.json"), dict(url=url, bytes=received, sha256=digest.hexdigest()))
        return path
    finally:
        temporary.unlink(missing_ok=True)


def unpack(archive: Path, target: Path):
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zipped:
        if sum(item.file_size for item in zipped.infolist()) > 2_000_000_000:
            raise ValueError("Runtime arşivi boyut sınırını aşıyor")
        for item in zipped.infolist():
            destination = (target / item.filename).resolve()
            if not destination.is_relative_to(target.resolve()):
                raise ValueError("Runtime arşivinde geçersiz yol")
        zipped.extractall(target)


def prepare_asset(key, root: Path, context):
    url, relative = CATALOG[key]
    path = root / relative
    # Existing user-selected files are not overwritten by setup.
    if path.is_file() and path.stat().st_size:
        context.report(1, f"Mevcut dosya kullanılıyor: {path.name}")
    else:
        download(url, path, context)
    if key == "llama_archive":
        target = root / "runtime" / "llama"
        if not (target / "llama-server.exe").exists():
            unpack(path, target)
        return target / "llama-server.exe"
    return path


def prepare_whisper(root: Path, context):
    from huggingface_hub import hf_hub_download
    target = root / "models" / "whisper-tiny.en"
    target.mkdir(parents=True, exist_ok=True)
    names = ("config.json", "model.bin", "tokenizer.json", "vocabulary.txt")
    for index, name in enumerate(names):
        context.check()
        if not (target / name).is_file():
            # Download progress is provided by huggingface_hub; overall count is real completed files.
            source = hf_hub_download("Systran/faster-whisper-tiny.en", filename=name)
            shutil.copyfile(source, target / name)
        context.report((index + 1) / len(names), f"Whisper model dosyası hazır: {name}")
    return target
