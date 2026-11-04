$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$originalPath = $env:PATH
try {
    # Third-party tools on PATH can shadow Windows ICU/UCRT DLLs during analysis.
    $env:PATH = "$env:SystemRoot\System32;$env:SystemRoot;$projectRoot\.venv\Scripts"
    & '.\.venv\Scripts\python.exe' -m PyInstaller --noconfirm --clean --onedir --windowed --name VEXVideo --add-data 'vex/ui;vex/ui' --add-data 'vex/blender_runtime.py;vex' --collect-all imageio_ffmpeg --collect-all kokoro_onnx --collect-all espeakng_loader --collect-all phonemizer --collect-all faster_whisper --exclude-module tkinter launcher.py
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed' }
    $smoke = Start-Process -FilePath '.\dist\VEXVideo\VEXVideo.exe' -ArgumentList '--smoke-test --data-dir build/smoke-data --screenshot build/exe-smoke.png' -WindowStyle Hidden -PassThru
    if (-not $smoke.WaitForExit(60000)) { $smoke.Kill(); throw 'EXE smoke test timed out' }
    if ($smoke.ExitCode -ne 0) { throw "EXE smoke test failed: $($smoke.ExitCode)" }
    if (Test-Path -LiteralPath 'third_party_licenses') {
        Copy-Item -LiteralPath 'third_party_licenses' -Destination 'dist/VEXVideo/third_party_licenses' -Recurse -Force
    }
    Copy-Item -LiteralPath 'README.md' -Destination 'dist/VEXVideo/README.md' -Force
    Copy-Item -LiteralPath 'docs/WINDOWS_PACKAGE.md' -Destination 'dist/VEXVideo/START_HERE.md' -Force
} finally {
    $env:PATH = $originalPath
}
