from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

from .assets import AssetRegistry
from .audio import align, narrate
from .drawing import render
from .export import export_video
from .jobs import Scheduler, Task
from .local_ai import LocalDirector
from .models import Project
from .runtime import doctor
from .sample import example_project
from .storage import Store, atomic_json

log = logging.getLogger(__name__)


class Bridge(QObject):
    changed = Signal()
    jobEvent = Signal(str, float, str)
    resultReady = Signal(str)

    def __init__(self, root):
        super().__init__()
        self.root = Path(root)
        self.store = Store(self.root)
        self.registry = AssetRegistry(self.root / "assets")
        self.scheduler = Scheduler(self.store)
        self.project = Project()
        self.folder = None
        self._busy = False
        self._message = "Yeni proje oluşturun veya prosedürel örneği açın."
        self._progress = 0.0
        self._preview = ""
        self._last_output = ""
        self.settings_path = self.root / "settings.json"
        self.settings = dict(llama_server="", gguf="", gpu_layers=0, kokoro_model="", kokoro_voices="", whisper_model="", voice="af_heart", ffmpeg="", blender="")
        if self.settings_path.exists():
            try:
                self.settings.update(json.loads(self.settings_path.read_text(encoding="utf-8")))
            except (OSError, ValueError):
                log.exception("Ayar dosyası okunamadı")
        self.settings["data_root"] = str(self.root)
        self.jobEvent.connect(self._on_job)
        self.resultReady.connect(self._on_result)

    @Property(str, notify=changed)
    def title(self):
        return self.project.title

    @Property(str, notify=changed)
    def story(self):
        return self.project.story

    @Property(str, notify=changed)
    def projectJson(self):
        return self.project.model_dump_json(indent=2)

    @Property(str, notify=changed)
    def settingsJson(self):
        return json.dumps(self.settings, ensure_ascii=False, indent=2)

    @Property("QVariantList", notify=changed)
    def scenes(self):
        return [dict(title=s.title, duration=s.duration, engine=s.engine, narration=s.narration) for s in self.project.scenes]

    @Property("QVariantList", notify=changed)
    def recent(self):
        return self.store.recent()

    @Property("QVariantList", notify=changed)
    def history(self):
        return self.store.history()

    @Property("QVariantList", notify=changed)
    def assets(self):
        return self.registry.list()

    @Property(bool, notify=changed)
    def busy(self):
        return self._busy

    @Property(str, notify=changed)
    def message(self):
        return self._message

    @Property(float, notify=changed)
    def progress(self):
        return self._progress

    @Property(str, notify=changed)
    def previewUrl(self):
        return self._preview

    @Property(str, notify=changed)
    def outputPath(self):
        return self._last_output

    @Property(str, notify=changed)
    def planningWarnings(self):
        return "\n".join(self.project.planning_warnings)

    def error(self, exc):
        log.error("%s", exc, exc_info=True)
        self._message = str(exc)
        self.changed.emit()

    @Slot()
    def newProject(self):
        if self._busy:
            return
        self.project = Project()
        self.folder = None
        self._preview = ""
        self._message = "Yeni proje hazır. Hikâyenizi yazın."
        self.changed.emit()

    @Slot()
    def loadExample(self):
        if self._busy:
            return
        self.project = example_project()
        self.folder = None
        self.saveProject()
        self.preview(0, 1.5)
        self._message = "Elle hazırlanmış prosedürel örnek açıldı. Bu örnek bir LLM çıktısı değildir."
        self.changed.emit()

    @Slot(str, str, str, int, int)
    def updateDraft(self, title, story, aspect, resolution, fps):
        if self._busy:
            return
        try:
            data = self.project.model_dump()
            data.update(title=title, story=story, export=self.project.export.model_dump() | dict(aspect=aspect, resolution=resolution, fps=fps))
            self.project = Project.model_validate(data)
            self.changed.emit()
        except Exception as exc:
            self.error(exc)

    @Slot()
    def saveProject(self):
        if self._busy:
            return
        try:
            path = self.store.save(self.project, self.folder)
            self.folder = path.parent
            self._message = f"Kaydedildi: {path}"
            self.changed.emit()
        except Exception as exc:
            self.error(exc)

    @Slot(str)
    def openProject(self, path):
        if self._busy:
            return
        try:
            url = QUrl(path)
            manifest = Path(url.toLocalFile() if url.isLocalFile() else path)
            self.project = self.store.load(manifest)
            self.folder = manifest.parent
            self._preview = ""
            if self.project.scenes:
                self.preview(0, 0)
            self._message = f"Açıldı: {self.project.title}"
            self.changed.emit()
        except Exception as exc:
            self.error(exc)

    @Slot(str)
    def applyJson(self, raw):
        if self._busy:
            return
        try:
            self.project = Project.model_validate_json(raw)
            self.saveProject()
            if self.project.scenes:
                self.preview(0, 0)
        except Exception as exc:
            self.error(exc)

    @Slot(str)
    def saveSettings(self, raw):
        if self._busy:
            return
        try:
            data = json.loads(raw)
            if not isinstance(data, dict) or set(data) - set(self.settings):
                raise ValueError("Bilinmeyen ayar anahtarı")
            merged = self.settings | data
            for key, value in merged.items():
                if key == "gpu_layers":
                    if type(value) is not int or not 0 <= value <= 200:
                        raise ValueError("gpu_layers 0..200 tam sayı olmalı")
                elif not isinstance(value, str):
                    raise ValueError(f"{key} metin olmalı")
            merged["data_root"] = str(self.root)
            atomic_json(self.settings_path, merged)
            self.settings = merged
            self._message = "Ayarlar kaydedildi."
            self.changed.emit()
        except Exception as exc:
            self.error(exc)

    @Slot()
    def checkRuntime(self):
        self._start([Task("Runtime denetimi", lambda ctx: self._diagnose())])

    def _diagnose(self):
        report = doctor(self.settings)
        self.resultReady.emit(json.dumps(dict(type="doctor", report=report)))
        return report

    @Slot(int, float)
    def preview(self, index, second):
        try:
            if not 0 <= index < len(self.project.scenes):
                return
            scene = self.project.scenes[index]
            if scene.engine == "3d":
                self._preview = ""
                self._message = "3D sahne için 360p video önizle kullanın. Tek kare paneli 2D/motion içindir."
                self.changed.emit()
                return
            width, height = self.project.export.dimensions(preview=True)
            image = render(scene, max(0, min(second, scene.duration)), width, height)
            path = self.root / "preview.png"
            if not image.save(str(path)):
                raise RuntimeError("Önizleme kaydedilemedi")
            self._preview = QUrl.fromLocalFile(str(path)).toString() + f"?v={time.time_ns()}"
            self.changed.emit()
        except Exception as exc:
            self.error(exc)

    def _start(self, tasks):
        if self._busy:
            return
        try:
            self._busy = True
            self._progress = 0
            self._message = "Görev sıraya alındı"
            self.scheduler.start(tasks, self.jobEvent.emit)
            self.changed.emit()
        except Exception as exc:
            self._busy = False
            self.error(exc)

    @Slot()
    def plan(self):
        if self._busy:
            return
        if not self.project.story.strip():
            self.error(ValueError("Hikâye alanı boş"))
            return
        title, story = self.project.title, self.project.story
        settings = dict(self.settings)
        identity = self.project.id
        def run(ctx):
            project = LocalDirector(settings).plan(story, title, ctx)
            project.id = identity
            project.export = self.project.export.model_copy(deep=True)
            self.resultReady.emit(json.dumps(dict(type="project", project=project.model_dump())))
            return project
        self._start([Task("Yerel LLM sahne planı", run)])

    @Slot()
    def generate(self):
        if self._busy:
            return
        if not self.project.story.strip():
            self.error(ValueError("Hikâye alanı boş"))
            return
        self.saveProject()
        if not self.folder:
            return
        source = self.project.model_copy(deep=True)
        folder, settings = self.folder, dict(self.settings)
        def plan(ctx):
            project = LocalDirector(settings).plan(source.story, source.title, ctx)
            project.id = source.id
            project.export = source.export
            self.store.save(project, folder)
            return project
        def voice(ctx):
            return narrate(ctx.values["LLM"], folder, ctx, settings)
        def subtitles(ctx):
            project, audio = ctx.values["Kokoro"]
            return align(project, audio, folder, ctx, settings)
        def video(ctx):
            project, audio = ctx.values["Kokoro"]
            output = export_video(project, folder, ctx, settings, False, audio, ctx.values["Whisper"])
            self.store.save(project, folder)
            self.resultReady.emit(json.dumps(dict(type="export", path=str(output), project=project.model_dump())))
            return output
        self._start([Task("LLM", plan), Task("Kokoro", voice, ("LLM",)), Task("Whisper", subtitles, ("Kokoro",)), Task("MP4", video, ("Whisper",), weight=8)])

    @Slot(int, str)
    def saveAsset(self, index, name):
        if self._busy:
            return
        try:
            if not name.strip() or not 0 <= index < len(self.project.scenes):
                raise ValueError("Bir sahne seçin ve asset adı girin")
            key = self.registry.put(name.strip(), "scene", self.project.scenes[index].nodes)
            self._message = f"Sahne geometrisi kütüphaneye kaydedildi: {key[:12]}"
            self.changed.emit()
        except Exception as exc:
            self.error(exc)

    @Slot(str, int)
    def insertAsset(self, key, index):
        if self._busy:
            return
        try:
            if not 0 <= index < len(self.project.scenes):
                raise ValueError("Önce bir hedef sahne oluşturun")
            data = self.project.model_dump()
            nodes = self.registry.instantiate(key, f"a{time.time_ns() % 10000000}")
            for node in nodes:
                # Library geometry is reused; animations must fit the target duration.
                if any(k.time > self.project.scenes[index].duration for t in node.tracks for k in t.keys):
                    raise ValueError("Asset animasyonu hedef sahneden uzun; önce sahne süresini artırın")
            data["scenes"][index]["nodes"].extend(n.model_dump() for n in nodes)
            self.project = Project.model_validate(data)
            self.saveProject()
            self.preview(index, 0)
        except Exception as exc:
            self.error(exc)

    @Slot(bool, bool)
    def renderVideo(self, preview_mode, with_voice):
        if self._busy:
            return
        self.saveProject()
        if self.folder is None:
            return
        project = self.project.model_copy(deep=True)
        folder = self.folder
        settings = dict(self.settings)
        tasks = []
        if with_voice:
            def voice(ctx):
                return narrate(project, folder, ctx, settings)
            def subtitle(ctx):
                planned, audio = ctx.values["Kokoro İngilizce ses"]
                return align(planned, audio, folder, ctx, settings)
            tasks += [Task("Kokoro İngilizce ses", voice), Task("Whisper İngilizce altyazı", subtitle, ("Kokoro İngilizce ses",))]
        def video(ctx):
            planned, audio = ctx.values.get("Kokoro İngilizce ses", (project, None))
            srt = ctx.values.get("Whisper İngilizce altyazı")
            output = export_video(planned, folder, ctx, settings, preview_mode, audio, srt)
            self.store.save(planned, folder)
            self.resultReady.emit(json.dumps(dict(type="export", path=str(output), project=planned.model_dump())))
            return output
        tasks.append(Task("Prosedürel video render", video, ("Whisper İngilizce altyazı",) if with_voice else (), weight=8))
        self._start(tasks)

    @Slot()
    def cancel(self):
        self.scheduler.cancel()
        self._message = "İptal istendi; aktif yerel inference çağrısının dönüşü beklenebilir."
        self.changed.emit()

    @Slot()
    def openOutput(self):
        if self._last_output:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self._last_output))

    @Slot()
    def openFolder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str((self.folder or self.root) / "exports" if self.folder else self.root)))

    @Slot(str, float, str)
    def _on_job(self, status, progress, message):
        self._progress = progress
        self._message = f"{status}: {message}"
        if status in ("COMPLETED", "FAILED", "CANCELLED"):
            self._busy = False
        self.changed.emit()

    @Slot(str)
    def _on_result(self, raw):
        data = json.loads(raw)
        if data["type"] in ("project", "export"):
            self.project = Project.model_validate(data["project"])
            self.folder = self.store.save(self.project, self.folder).parent
            if self.project.scenes:
                self.preview(0, 0)
        if data["type"] == "export":
            self._last_output = data["path"]
        elif data["type"] == "doctor":
            path = self.root / "runtime-report.json"
            atomic_json(path, data["report"])
            self._message = json.dumps(data["report"], ensure_ascii=False, indent=2)
        elif data["type"] == "setup":
            self.settings.update(data["paths"])
            atomic_json(self.settings_path, self.settings)
        self.changed.emit()

    @Slot()
    def prepareModels(self):
        from .model_manager import CATALOG, prepare_asset, prepare_whisper
        tasks = []
        for key in CATALOG:
            tasks.append(Task(key, lambda ctx, name=key: prepare_asset(name, self.root, ctx)))
        tasks.append(Task("whisper_model", lambda ctx: prepare_whisper(self.root, ctx)))
        def finish(ctx):
            paths = {("llama_server" if key == "llama_archive" else key): str(value.resolve()) for key, value in ctx.values.items()}
            self.resultReady.emit(json.dumps(dict(type="setup", paths=paths)))
            return paths
        tasks.append(Task("Ayarları güncelle", finish, tuple(t.name for t in tasks)))
        self._start(tasks)
