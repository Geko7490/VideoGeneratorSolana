from pathlib import Path

from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from vex.bridge import Bridge


def test_qml_loads_and_project_actions_refresh_actual_fields(qt_app, tmp_path):
    backend = Bridge(tmp_path)
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda items: warnings.extend(str(item) for item in items))
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(Path(__file__).parents[1] / "vex/ui/Main.qml")))
    assert len(engine.rootObjects()) == 1
    window = engine.rootObjects()[0]
    assert isinstance(window, QQuickWindow)
    backend.loadExample()
    qt_app.processEvents()
    assert window.findChild(QObject, "titleField").property("text") == "The Last Signal"
    assert "robot" in window.findChild(QObject, "storyField").property("text")
    assert backend.folder.joinpath("project.json").is_file()
    assert backend.previewUrl.startswith("file:")
    path = backend.folder / "project.json"
    backend.newProject()
    qt_app.processEvents()
    assert window.findChild(QObject, "titleField").property("text") == "Untitled story"
    backend.openProject(str(path))
    qt_app.processEvents()
    assert window.findChild(QObject, "titleField").property("text") == "The Last Signal"
    assert not warnings
    backend.scheduler.close()
    window.close()
    engine.deleteLater()
    qt_app.processEvents()
