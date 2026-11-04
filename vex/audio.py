"""Real optional local English Kokoro and Whisper inference. No synthetic substitutes."""
from __future__ import annotations

import difflib
import re
import wave
from pathlib import Path

from .export import fingerprint, run_process
from .jobs import Context
from .models import Project
from .runtime import ffmpeg_path
from .storage import atomic_json


def require_file(settings, name):
    path = Path(settings.get(name, ""))
    if not path.is_file():
        raise FileNotFoundError(f"Ayarlar'da {name} dosyasını seçin")
    return path


def narrate(project: Project, folder: Path, context: Context, settings):
    import soundfile as sf
    from kokoro_onnx import Kokoro

    model = require_file(settings, "kokoro_model")
    voices = require_file(settings, "kokoro_voices")
    voice = settings.get("voice", "af_heart")
    if not voice.startswith(("af_", "am_", "bf_", "bm_")):
        raise ValueError("Yalnızca İngilizce Kokoro sesleri destekleniyor")
    engine = Kokoro(str(model), str(voices))
    if voice not in engine.get_voices():
        raise ValueError(f"Ses profili bulunamadı: {voice}")
    folder.joinpath("audio").mkdir(parents=True, exist_ok=True)
    paths = []
    updated = Project.model_validate(project.model_dump())
    model_version = (str(model.resolve()), model.stat().st_size, model.stat().st_mtime_ns,
                     str(voices.resolve()), voices.stat().st_size, voices.stat().st_mtime_ns)
    for index, scene in enumerate(updated.scenes):
        context.check()
        if not scene.narration.strip():
            raise ValueError(f"İngilizce narration boş: {scene.title}")
        key = fingerprint(dict(text=scene.narration, voice=voice, speed=1, model=model_version))
        path = folder / "audio" / f"{key}.wav"
        if not path.exists():
            audio, sample_rate = engine.create(scene.narration, voice=voice, speed=1.0, lang="en-us")
            context.check()
            partial = path.with_suffix(".partial.wav")
            sf.write(partial, audio, sample_rate, subtype="PCM_16")
            partial.replace(path)
        info = sf.info(path)
        if info.duration <= 0:
            raise ValueError("Kokoro boş WAV üretti")
        # Keep last animation pose when narration extends the original scene.
        scene.duration = max(scene.duration, info.duration + .25)
        paths.append(path)
        context.report((index + 1) / len(updated.scenes), f"İngilizce ses: {scene.title}")
    # Build a mono PCM timeline with real audio and silence between scenes, bounded memory.
    output = folder / "audio" / "narration.wav"
    partial = output.with_suffix(".partial.wav")
    try:
        with wave.open(str(partial), "wb") as destination:
            destination.setnchannels(1)
            destination.setsampwidth(2)
            rate = sf.info(paths[0]).samplerate
            destination.setframerate(rate)
            for scene, path in zip(updated.scenes, paths):
                context.check()
                with wave.open(str(path), "rb") as source:
                    if source.getnchannels() != 1 or source.getsampwidth() != 2 or source.getframerate() != rate:
                        raise ValueError("Kokoro WAV formatı beklenen mono PCM16 değil")
                    size = source.getnframes()
                    while block := source.readframes(8192):
                        context.check()
                        destination.writeframesraw(block)
                import math
                duration = math.ceil(scene.duration * project.export.fps) / project.export.fps
                silence = max(0, round(duration * rate) - size)
                while silence:
                    count = min(8192, silence)
                    destination.writeframesraw(b"\0\0" * count)
                    silence -= count
        partial.replace(output)
    finally:
        partial.unlink(missing_ok=True)
    return updated, output


def timestamp(seconds, ass=False):
    units = 100 if ass else 1000
    value = max(0, round(seconds * units))
    sec, fraction = divmod(value, units)
    minute, sec = divmod(sec, 60)
    hour, minute = divmod(minute, 60)
    return f"{hour}:{minute:02}:{sec:02}.{fraction:02}" if ass else f"{hour:02}:{minute:02}:{sec:02},{fraction:03}"


def align(project, audio, folder, context, settings):
    from faster_whisper import WhisperModel

    local_model = Path(settings.get("whisper_model", ""))
    if not local_model.is_dir() or not (local_model / "model.bin").is_file():
        raise ValueError("Yerel faster-whisper model klasörünü seçin; otomatik indirme yapılmaz")
    engine = WhisperModel(str(local_model), device="cpu", compute_type="int8", local_files_only=True)
    reference = " ".join(s.narration for s in project.scenes)
    segments, _ = engine.transcribe(str(audio), language="en", word_timestamps=True, initial_prompt=reference, beam_size=5)
    words = []
    with wave.open(str(audio), "rb") as handle:
        duration = handle.getnframes() / handle.getframerate()
    for segment in segments:
        context.check()
        for word in segment.words or []:
            if word.end > word.start:
                words.append(dict(start=word.start, end=word.end, text=word.word.strip()))
        context.report(min(.99, segment.end / duration), "Whisper İngilizce kelimeleri hizalıyor")
    if not words:
        raise ValueError("Whisper kelime zamanlaması üretmedi")
    def normalize(text):
        return re.findall(r"[a-z0-9']+", text.lower())
    score = difflib.SequenceMatcher(None, normalize(reference), normalize(" ".join(w["text"] for w in words))).ratio()
    directory = folder / "subtitles"
    directory.mkdir(parents=True, exist_ok=True)
    atomic_json(directory / "alignment.json", dict(similarity=score, words=words, reference=reference, source="faster-whisper"))
    if score < .8:
        raise ValueError(f"Whisper metin uyumu düşük ({score:.0%}); alignment.json dosyasını inceleyin. Uydurma zamanlama uygulanmadı.")
    srt = directory / "narration.srt"
    srt.write_text("\n\n".join(f"{i}\n{timestamp(w['start'])} --> {timestamp(w['end'])}\n{w['text']}" for i, w in enumerate(words, 1)) + "\n", encoding="utf-8")
    ass = "[Script Info]\nScriptType: v4.00+\nPlayResX: 1280\nPlayResY: 720\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Segoe UI,42,&H00FFFFFF,&H0000FFFF,&H00111111,&H80000000,0,0,0,0,100,100,0,0,1,2,1,2,40,40,40,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    for w in words:
        text = w["text"].replace("\\", "").replace("{", "").replace("}", "").replace("\n", " ")
        ass += f"Dialogue: 0,{timestamp(w['start'], True)},{timestamp(w['end'], True)},Default,,0,0,0,,{text}\n"
    (directory / "narration.ass").write_text(ass, encoding="utf-8")
    context.report(1, f"İngilizce altyazı hazır; metin uyumu {score:.0%}")
    return srt


def mix_audio(narration, music, output, context, settings, volume=.2):
    if not 0 <= volume <= 1:
        raise ValueError("Müzik sesi 0..1 aralığında olmalı")
    ffmpeg = ffmpeg_path(settings.get("ffmpeg", ""))
    graph = f"[1:a]volume={volume}[m];[0:a]asplit=2[voice][control];[m][control]sidechaincompress=threshold=0.03:ratio=8[duck];[voice][duck]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[out]"
    run_process([ffmpeg, "-y", "-v", "error", "-i", str(narration), "-stream_loop", "-1", "-i", str(music), "-filter_complex", graph, "-map", "[out]", "-c:a", "pcm_s16le", str(output)], context)
    return output
