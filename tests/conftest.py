import os

import pytest
from PySide6.QtGui import QGuiApplication

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session", autouse=True)
def qt_app():
    app = QGuiApplication.instance() or QGuiApplication([])
    yield app
