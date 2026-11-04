import json
import re
import subprocess
import wave
from threading import Event

import pytest

from vex.export import export_video
from vex.jobs import Cancelled, Context
from vex.runtime import NO_WINDOW, ffmpeg_path
from vex.sample import example_project


def short_project():
    project = example_project()
    data = project.model_dump()
    data["scenes"] = data["scenes"][:2]
    for scene in data["scenes"]:
        scene["duration"] = .5
        for node in scene["nodes"]:
            node["tracks"] = []
    return type(project).model_validate(data)


def test_real_mp4_decode_frame_count_and_cache(tmp_path):
    project = short_project()
    reports = []
    ctx = Context(Event(), lambda fraction, message: reports.append(fraction))
    output = export_video(project, tmp_path, ctx, preview=True)
    assert output.stat().st_size > 1000
    metadata = json.loads(output.with_suffix(".json").read_text())
    assert metadata["duration"] == 1
    assert metadata["width"] == 640 and metadata["height"] == 360
    ffmpeg = ffmpeg_path()
    decode = subprocess.run([ffmpeg, "-v", "info", "-i", str(output), "-f", "null", "-"], capture_output=True, text=True, creationflags=NO_WINDOW, timeout=30)
    assert decode.returncode == 0
    assert "Video: h264" in decode.stderr
    assert "640x360" in decode.stderr
    assert int(re.findall(r"frame=\s*(\d+)", decode.stderr)[-1]) == 24
    cache = list((tmp_path / "cache").glob("*.mp4"))
    assert len(cache) == 2
    original = {p.name: p.stat().st_mtime_ns for p in cache}
    export_video(project, tmp_path, ctx, preview=True)
    assert {p.name: p.stat().st_mtime_ns for p in cache} == original
    # Corrupt cache cannot be silently reused.
    cache[0].write_bytes(b"broken")
    export_video(project, tmp_path, ctx, preview=True)
    assert cache[0].stat().st_size > 1000
    assert reports[-1] == 1


def test_cancel_keeps_completed_scene_and_existing_export(tmp_path):
    project = short_project()
    context = Context(Event(), lambda *args: None)
    final = export_video(project, tmp_path, context, preview=True)
    original = final.read_bytes()
    # Change second scene only. First scene remains valid and should be retained.
    project.scenes[1].background = "#334455"
    cancel = Event()
    def report(fraction, message):
        if fraction > .46:
            cancel.set()
    with pytest.raises(Cancelled):
        export_video(project, tmp_path, Context(cancel, report), preview=True)
    assert final.read_bytes() == original
    assert len(list((tmp_path / "cache").glob("*.mp4"))) >= 2
    assert not list(tmp_path.rglob("*.partial.mp4"))
    output = export_video(project, tmp_path, context, preview=True)
    assert output.stat().st_size > 1000


def test_real_audio_subtitle_mux_and_burn_in_with_unicode_paths(tmp_path):
    folder = tmp_path / "Türkçe proje ' test"
    folder.mkdir()
    audio = folder / "ses.wav"
    with wave.open(str(audio), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(24000)
        handle.writeframes(b"\0\0" * 24000)
    subtitle = folder / "altyazı.srt"
    subtitle.write_text("1\n00:00:00,000 --> 00:00:00,900\nHello VEX\n", encoding="utf-8")
    project = short_project()
    project.export.burn_subtitles = True
    result = export_video(project, folder, Context(Event(), lambda *args: None), preview=True, audio=audio, subtitles=subtitle)
    probe = subprocess.run([ffmpeg_path(), "-i", str(result)], capture_output=True, text=True, creationflags=NO_WINDOW)
    assert "Audio: aac" in probe.stderr
    assert "Subtitle: mov_text" in probe.stderr
    assert result.stat().st_size > 1000
