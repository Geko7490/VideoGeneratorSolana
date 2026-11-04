import math
import wave
from array import array
from threading import Event, Timer

from vex.audio import mix_audio, timestamp
from vex.jobs import Context


def test_real_local_music_ducking_mix_is_bounded(tmp_path):
    for name, hz in (("voice", 440), ("music", 220)):
        with wave.open(str(tmp_path / f"{name}.wav"), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(24000)
            samples = array("h", [int(4000 * math.sin(2*math.pi*hz*i/24000)) for i in range(24000)])
            handle.writeframes(samples.tobytes())
    cancel = Event()
    watchdog = Timer(15, cancel.set)
    watchdog.start()
    try:
        output = mix_audio(tmp_path / "voice.wav", tmp_path / "music.wav", tmp_path / "mixed.wav", Context(cancel, lambda *args: None), {})
    finally:
        watchdog.cancel()
    with wave.open(str(output), "rb") as handle:
        assert .9 <= handle.getnframes() / handle.getframerate() <= 1.1
        assert any(handle.readframes(1000))


def test_subtitle_timestamps():
    assert timestamp(3661.234) == "01:01:01,234"
    assert timestamp(3661.23, True) == "1:01:01.23"
