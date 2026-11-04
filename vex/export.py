"""Bounded-memory frame streaming, scene cache, safe subprocess cancellation."""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

from .drawing import RENDERER_VERSION, render
from .jobs import Context
from .models import Project
from .runtime import NO_WINDOW, ffmpeg_path
from .storage import atomic_json


def fingerprint(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def run_process(args, context: Context, cwd=None):
    with tempfile.TemporaryFile() as log:
        process = subprocess.Popen(args, cwd=cwd, stdout=subprocess.DEVNULL, stderr=log, creationflags=NO_WINDOW)
        try:
            while True:
                context.check()
                try:
                    code = process.wait(timeout=.1)
                    break
                except subprocess.TimeoutExpired:
                    continue
            if code:
                log.seek(0)
                raise RuntimeError(log.read().decode(errors="replace")[-6000:])
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


def encode_scene(scene, width, height, fps, output: Path, context: Context, ffmpeg, report):
    frames = math.ceil(scene.duration * fps)
    partial = output.with_suffix(".partial.mp4")
    with tempfile.TemporaryFile() as log:
        process = subprocess.Popen([
            ffmpeg, "-y", "-v", "error", "-f", "rawvideo", "-pixel_format", "rgba",
            "-video_size", f"{width}x{height}", "-framerate", str(fps), "-i", "pipe:0",
            "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", str(partial),
        ], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=log, creationflags=NO_WINDOW)
        try:
            for index in range(frames):
                context.check()
                image = render(scene, index / fps, width, height)
                # QImage RGBA rows are contiguous because width*4 is aligned.
                process.stdin.write(image.constBits())
                report((index + 1) / frames)
            process.stdin.close()
            while process.poll() is None:
                context.check()
                try:
                    process.wait(timeout=.1)
                except subprocess.TimeoutExpired:
                    pass
            if process.returncode:
                log.seek(0)
                raise RuntimeError(log.read().decode(errors="replace")[-6000:])
            partial.replace(output)
        except BrokenPipeError as exc:
            log.seek(0)
            raise RuntimeError(log.read().decode(errors="replace")[-6000:]) from exc
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            if process.stdin and not process.stdin.closed:
                process.stdin.close()
            partial.unlink(missing_ok=True)


def export_video(project: Project, folder: Path, context: Context, settings=None, preview=False, audio=None, subtitles=None):
    if not project.scenes:
        raise ValueError("Önce sahne oluşturun veya örnek projeyi açın")
    project = Project.model_validate(project.model_dump())
    settings = settings or {}
    ffmpeg = ffmpeg_path(settings.get("ffmpeg", ""))
    width, height = project.export.dimensions(preview)
    fps = project.export.fps
    cache = folder / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    exports = folder / "exports"
    exports.mkdir(parents=True, exist_ok=True)
    total_frames = sum(math.ceil(s.duration * fps) for s in project.scenes)
    processed = 0
    clips = []
    for scene in project.scenes:
        context.check()
        runtime_signature = None
        if scene.engine == "3d":
            blender = Path(settings.get("blender", ""))
            if blender.is_file():
                runtime_signature = [str(blender.resolve()), blender.stat().st_size, blender.stat().st_mtime_ns]
            else:
                raise FileNotFoundError("3D render için Blender runtime seçin")
        key = fingerprint(dict(scene=scene.model_dump(), width=width, height=height, fps=fps, renderer=RENDERER_VERSION, runtime=runtime_signature))
        clip = cache / f"{key}.mp4"
        checksum = clip.with_suffix(".json")
        valid = False
        if clip.exists() and checksum.exists():
            try:
                with clip.open("rb") as handle:
                    valid = json.loads(checksum.read_text())["sha256"] == hashlib.file_digest(handle, "sha256").hexdigest()
            except (ValueError, KeyError, OSError):
                valid = False
        frames = math.ceil(scene.duration * fps)
        if not valid:
            def report_scene(fraction):
                context.report(.9 * (processed + fraction * frames) / total_frames, f"Çiziliyor: {scene.title}")
            if scene.engine == "3d":
                from .engine3d import encode_3d
                encode_3d(scene, width, height, fps, clip, context, ffmpeg, settings, report_scene)
            else:
                encode_scene(scene, width, height, fps, clip, context, ffmpeg, report_scene)
            with clip.open("rb") as handle:
                digest = hashlib.file_digest(handle, "sha256").hexdigest()
            atomic_json(checksum, {"sha256": digest})
        processed += frames
        clips.append(clip)
        context.report(.9 * processed / total_frames, f"Sahne hazır: {scene.title}")
    # All concat entries are internally generated hexadecimal names, never user strings.
    concat = cache / "concat.txt"
    concat.write_text("".join(f"file '{clip.name}'\n" for clip in clips), encoding="utf-8")
    suffix = "preview" if preview else "final"
    final = exports / f"{suffix}.mp4"
    partial = exports / f"{suffix}.partial.mp4"
    args = [ffmpeg, "-y", "-v", "error", "-f", "concat", "-safe", "1", "-i", str(concat.resolve())]
    if audio:
        args += ["-i", str(Path(audio).resolve())]
    if subtitles:
        args += ["-i", str(Path(subtitles).resolve())]
    args += ["-map", "0:v:0"]
    if subtitles and project.export.burn_subtitles:
        shutil.copyfile(subtitles, exports / "vex-subtitles.srt")
        args += ["-vf", "subtitles=filename=vex-subtitles.srt", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20"]
    else:
        args += ["-c:v", "copy"]
    if audio:
        args += ["-map", "1:a:0", "-c:a", "aac", "-af", "apad", "-t", str(sum(math.ceil(s.duration * fps) / fps for s in project.scenes))]
    if subtitles:
        args += ["-map", f"{2 if audio else 1}:s:0", "-c:s", "mov_text", "-metadata:s:s:0", "language=eng"]
    args += ["-movflags", "+faststart", str(partial.resolve())]
    try:
        context.report(.92, "MP4 birleştiriliyor")
        run_process(args, context, cwd=exports)
        context.report(.97, "Video decode edilerek doğrulanıyor")
        run_process([ffmpeg, "-v", "error", "-i", str(partial), "-f", "null", "-"], context)
        context.check()
        partial.replace(final)
    finally:
        partial.unlink(missing_ok=True)
    atomic_json(exports / f"{suffix}.json", dict(width=width, height=height, fps=fps, duration=sum(math.ceil(s.duration * fps) / fps for s in project.scenes), scenes=len(clips), narration=bool(audio), subtitles=bool(subtitles), renderer=RENDERER_VERSION))
    context.report(1, str(final))
    return final
