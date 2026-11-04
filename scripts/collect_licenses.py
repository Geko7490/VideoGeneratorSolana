"""Preserve installed dependency license files in a reviewable distribution folder."""
from importlib.metadata import distributions
from pathlib import Path

root = Path(__file__).resolve().parents[1]
destination = root / "third_party_licenses"
destination.mkdir(exist_ok=True)
versions = []
for distribution in distributions():
    name = distribution.metadata.get("Name", "unknown")
    if name.lower() in ("vex-video", "pip"):
        continue
    versions.append(f"{name}=={distribution.version}")
    for entry in distribution.files or []:
        if "license" in entry.name.lower() or "copying" in entry.name.lower() or entry.name.lower() == "notice":
            source = Path(distribution.locate_file(entry))
            if source.is_file() and source.stat().st_size < 5_000_000:
                package_dir = destination / name
                package_dir.mkdir(exist_ok=True)
                (package_dir / entry.name).write_bytes(source.read_bytes())
(root / "requirements-windows.lock.txt").write_text("# Tested Windows Python 3.12 environment, including audio and developer tools\n" + "\n".join(sorted(versions, key=str.lower)) + "\n", encoding="utf-8")
