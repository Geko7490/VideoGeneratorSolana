import pytest
from pydantic import ValidationError

from vex.drawing import render
from vex.models import Node, Scene


def test_motion_text_particles_gradient_and_bezier(qt_app):
    scene = Scene(id="motion", title="Motion", engine="motion", nodes=[
        Node(id="background", kind="rectangle", x=640, y=360, width=1280, height=720, color="#112244", gradient="#441122"),
        Node(id="particles", kind="particles", x=640, y=360, width=600, height=400, color="#aabbcc", clip=True),
        Node(id="title", kind="text", x=640, y=360, width=1000, height=80, text="HELLO VEX", text_effect="typewriter"),
        Node(id="curve", kind="path", x=100, y=100, points=[(0, 0), (40, 80), (80, 40), (160, 0)], stroke_width=3),
    ])
    first = render(scene, 0, 640, 360)
    later = render(scene, 1, 640, 360)
    assert first.pixelColor(1, 1) != first.pixelColor(1, 358)
    assert bytes(first.constBits()) != bytes(later.constBits())
    assert bytes(later.constBits()) == bytes(render(scene, 1, 640, 360).constBits())
    with pytest.raises(ValidationError):
        Node(id="bad", kind="path", points=[(0, 0), (1, 1)])
