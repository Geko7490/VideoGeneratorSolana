"""Create a source-only archive; models, user projects and runtimes stay local."""
import os
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

root = Path(__file__).resolve().parents[1]
excluded = {".git", ".venv", "data", "build", "dist", "__pycache__", ".pytest_cache", ".ruff_cache"}
output = root.parent / "VEXVideo-source.zip"
with ZipFile(output, "w", ZIP_DEFLATED) as archive:
    for current, directories, files in os.walk(root):
        directories[:] = [name for name in directories if name not in excluded and not name.endswith(".egg-info")]
        for name in files:
            path = Path(current) / name
            relative = path.relative_to(root)
            if path.suffix not in {".pyc", ".spec", ".mp4", ".wav", ".gguf", ".onnx", ".bin"}:
                archive.write(path, Path("VideoGeneratorSolana") / relative)
print(output)
