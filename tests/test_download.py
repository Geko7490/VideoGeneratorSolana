import zipfile
from threading import Event

import pytest

from vex.jobs import Cancelled, Context
from vex.model_manager import download, unpack


def test_download_counts_bytes_and_cleans_cancelled_partial(tmp_path):
    original = tmp_path / "source.bin"
    original.write_bytes(b"test" * 500000)
    destination = tmp_path / "destination.bin"
    reports = []
    download(original.as_uri(), destination, Context(Event(), lambda f, m: reports.append(f)))
    assert destination.read_bytes() == original.read_bytes()
    assert reports[-1] == 1
    assert destination.with_name("destination.bin.download.json").exists()
    event = Event()
    event.set()
    with pytest.raises(Cancelled):
        download(original.as_uri(), destination, Context(event, lambda *args: None))
    assert destination.read_bytes() == original.read_bytes()
    assert not destination.with_name("destination.bin.part").exists()


def test_runtime_unpack_rejects_path_traversal(tmp_path):
    archive = tmp_path / "runtime.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr("../escape.txt", "bad")
    with pytest.raises(ValueError):
        unpack(archive, tmp_path / "runtime")
    assert not (tmp_path / "escape.txt").exists()
