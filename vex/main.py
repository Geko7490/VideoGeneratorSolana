from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from threading import Event


def data_root():
    return Path(os.environ.get("LOCALAPPDATA", str(Path.home() / ".local" / "share"))) / "VEXVideo"


def main():
    parser = argparse.ArgumentParser(description="VEX local procedural video studio")
    parser.add_argument("command", nargs="?", default="studio", choices=["studio", "doctor", "sample", "render", "schema", "plan", "generate"])
    parser.add_argument("--data-dir", type=Path, default=data_root())
    parser.add_argument("--project", type=Path)
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--screenshot", type=Path)
    parser.add_argument("--story", default="")
    parser.add_argument("--title", default="My story")
    parser.add_argument("--voice", action="store_true", help="Use real local Kokoro and Whisper")
    args = parser.parse_args()
    args.data_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=args.data_dir / "vex.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s", encoding="utf-8")
    if args.command == "doctor":
        from .runtime import doctor
        settings_file = args.data_dir / "settings.json"
        settings = json.loads(settings_file.read_text(encoding="utf-8")) if settings_file.exists() else {}
        print(json.dumps(doctor(settings), ensure_ascii=False, indent=2))
        return 0
    if args.command == "schema":
        from .models import Project
        print(json.dumps(Project.model_json_schema(), indent=2))
        return 0
    from .storage import Store
    store = Store(args.data_dir)
    if args.command == "sample":
        from .sample import example_project
        print(store.save(example_project()))
        return 0
    if args.command in ("render", "plan", "generate") or args.smoke_test:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtGui import QFontDatabase, QGuiApplication
    app = QGuiApplication(sys.argv[:1])
    if sys.platform == "win32":
        fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
        for name in ("segoeui.ttf", "segoeuib.ttf", "consola.ttf"):
            if (fonts / name).exists():
                QFontDatabase.addApplicationFont(str(fonts / name))
    app.setApplicationName("VEXVideo")
    app.setOrganizationName("VEX")
    if args.command in ("render", "plan", "generate"):
        if args.command == "render" and not args.project:
            parser.error("render için --project project.json gerekir")
        from .export import export_video
        from .jobs import Context
        settings_file = args.data_dir / "settings.json"
        settings = json.loads(settings_file.read_text(encoding="utf-8")) if settings_file.exists() else {}
        settings["data_root"] = str(args.data_dir.resolve())
        last_report = [-1, ""]
        def report(fraction, message):
            percent = int(fraction * 100)
            if percent != last_report[0] or message != last_report[1]:
                print(f"{percent}% {message}", flush=True)
                last_report[:] = [percent, message]
        ctx = Context(Event(), report)
        if args.command in ("plan", "generate"):
            from .local_ai import LocalDirector
            if not args.story.strip():
                parser.error("plan/generate için --story gerekir")
            project = LocalDirector(settings).plan(args.story, args.title, ctx)
            manifest = store.save(project)
        else:
            manifest = args.project
            project = store.load(manifest)
        if args.command == "plan":
            print(manifest)
            return 0
        audio = subtitles = None
        if args.voice:
            from .audio import align, narrate
            project, audio = narrate(project, manifest.parent, ctx, settings)
            subtitles = align(project, audio, manifest.parent, ctx, settings)
            store.save(project, manifest.parent)
        print(export_video(project, manifest.parent, ctx, settings, args.preview, audio, subtitles))
        return 0
    from PySide6.QtCore import QTimer, QUrl
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuick import QQuickWindow

    from .bridge import Bridge
    backend = Bridge(args.data_dir)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(Path(__file__).parent / "ui" / "Main.qml")))
    if not engine.rootObjects():
        return 1
    if not isinstance(engine.rootObjects()[0], QQuickWindow):
        raise RuntimeError("QML root must be a QQuickWindow")
    app.aboutToQuit.connect(backend.scheduler.close)
    if args.smoke_test:
        backend.loadExample()
        def finish():
            if args.screenshot:
                args.screenshot.parent.mkdir(parents=True, exist_ok=True)
                if not engine.rootObjects()[0].grabWindow().save(str(args.screenshot)):
                    app.exit(2)
                    return
            app.quit()
        QTimer.singleShot(1800, finish)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
