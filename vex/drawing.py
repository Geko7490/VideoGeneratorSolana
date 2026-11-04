"""Resolution independent QPainter scene graph and time-based animation."""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QLinearGradient, QPainter, QPainterPath, QPen, QPolygonF

from .models import Node, Scene, Track

RENDERER_VERSION = "procedural-1.1"


def evaluate(track: Track, time: float):
    if time <= track.keys[0].time:
        return track.keys[0].value
    for a, b in zip(track.keys, track.keys[1:]):
        if time <= b.time:
            u = (time - a.time) / (b.time - a.time)
            if b.easing == "smooth":
                u = u * u * (3 - 2 * u)
            elif b.easing == "in":
                u *= u
            elif b.easing == "out":
                u = 1 - (1 - u) ** 2
            return a.value + (b.value - a.value) * u
    return track.keys[-1].value


def state(node: Node, time):
    values = {key: getattr(node, key) for key in ("x", "y", "rotation", "scale", "opacity")}
    for track in node.tracks:
        values[track.property] = evaluate(track, time)
    return values


def paint_shape(p: QPainter, node: Node, time: float):
    w, h = node.width, node.height
    color = QColor(node.color)
    p.setBrush(color)
    p.setPen(QPen(QColor(node.stroke), node.stroke_width) if node.stroke_width else Qt.NoPen)
    rect = QRectF(-w / 2, -h / 2, w, h)
    if node.gradient:
        gradient = QLinearGradient(0, -h/2, 0, h/2)
        gradient.setColorAt(0, color)
        gradient.setColorAt(1, QColor(node.gradient))
        p.setBrush(gradient)
    if node.clip:
        p.setClipRect(rect, Qt.IntersectClip)
    if node.kind == "rectangle":
        p.drawRect(rect)
    elif node.kind == "ellipse":
        p.drawEllipse(rect)
    elif node.kind == "line":
        p.setPen(QPen(color, max(1, node.stroke_width)))
        p.drawLine(QPointF(-w / 2, -h / 2), QPointF(w / 2, h / 2))
    elif node.kind == "polygon":
        p.drawPolygon(QPolygonF([QPointF(x, y) for x, y in node.points]))
    elif node.kind == "path":
        path = QPainterPath(QPointF(*node.points[0]))
        for index in range(1, len(node.points), 3):
            path.cubicTo(*[QPointF(*point) for point in node.points[index:index+3]])
        p.drawPath(path)
    elif node.kind == "particles":
        base_opacity = p.opacity()
        for index in range(node.particle_count):
            # Deterministic phase; geometry is reproducible at a timestamp for any FPS.
            phase = (index * .61803398875 + time * .2) % 1
            x = math.sin(index * 17.31) * w * .5
            y = h * (.5-phase)
            p.setOpacity(base_opacity * (1-phase))
            p.drawEllipse(QPointF(x, y), 2+index%4, 2+index%4)
        p.setOpacity(base_opacity)
    elif node.kind == "text":
        font = QFont("Segoe UI")
        font.setPixelSize(max(1, int(h * 0.65)))
        font.setBold(True)
        p.setFont(font)
        p.setPen(color)
        text = node.text
        if node.text_effect == "typewriter":
            text = text[:int(time * node.text_rate)]
        elif node.text_effect == "reveal":
            p.setClipRect(QRectF(-w/2, -h/2, min(w, time*node.text_rate*10), h), Qt.IntersectClip)
        p.drawText(rect, Qt.AlignCenter | Qt.TextWordWrap, text)
    elif node.kind == "building":
        p.drawRoundedRect(rect, 4, 4)
        p.setBrush(QColor(node.stroke))
        for row in range(1, 6):
            for col in range(1, 4):
                p.drawRect(QRectF(-w / 2 + col * w / 4 - 4, -h / 2 + row * h / 7, 8, 12))
    elif node.kind == "tower":
        p.drawRoundedRect(QRectF(-w * .28, -h * .3, w * .56, h * .8), 6, 6)
        p.setBrush(QColor(node.stroke))
        p.drawEllipse(QRectF(-w * .4, -h * .5, w * .8, w * .8))
        p.setPen(QPen(QColor(node.stroke), 3))
        p.drawLine(QPointF(0, -h * .4), QPointF(0, h * .5))
    elif node.kind == "robot":
        # Identical proportions and palette across all scenes; motion is time based.
        p.scale(w / 100, h / 160)
        stride = math.sin(time * 7) * 12 if any(t.property == "x" for t in node.tracks) else 0
        p.setPen(QPen(QColor("#151a2c"), 3))
        p.drawRoundedRect(QRectF(-25, -22, 50, 57), 10, 10)
        p.drawRoundedRect(QRectF(-34, -70, 68, 45), 12, 12)
        p.drawRoundedRect(QRectF(-43, -15 + stride, 13, 46), 5, 5)
        p.drawRoundedRect(QRectF(30, -15 - stride, 13, 46), 5, 5)
        p.drawRoundedRect(QRectF(-24 + stride, 32, 18, 40), 6, 6)
        p.drawRoundedRect(QRectF(6 - stride, 32, 18, 40), 6, 6)
        p.setBrush(QColor("#111526"))
        p.drawRoundedRect(QRectF(-26, -60, 52, 23), 7, 7)
        p.setBrush(QColor(node.stroke))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(-18, -54, 10, 10))
        p.drawEllipse(QRectF(8, -54, 10, 10))
        p.drawEllipse(QRectF(-6, -8, 12, 12))
        p.drawRect(QRectF(-2, -80, 4, 10))


def render(scene: Scene, time: float, width: int, height: int) -> QImage:
    image = QImage(width, height, QImage.Format_RGBA8888)
    image.fill(QColor(scene.background))
    painter = QPainter(image)
    try:
        painter.setRenderHint(QPainter.Antialiasing)
        # Letterbox a 1280x720 design canvas; preserve geometry for vertical/square exports.
        factor = min(width / 1280, height / 720)
        painter.translate((width - 1280 * factor) / 2, (height - 720 * factor) / 2)
        painter.scale(factor, factor)
        camera = scene.camera
        fraction = min(1, max(0, time / scene.duration))
        painter.translate(640, 360)
        painter.scale(camera.zoom, camera.zoom)
        painter.translate(-640 - camera.x - camera.pan_x * fraction, -360 - camera.y - camera.pan_y * fraction)
        children: dict[str | None, list[Node]] = {}
        for node in scene.nodes:
            children.setdefault(node.parent, []).append(node)

        def draw(parent):
            for node in sorted(children.get(parent, []), key=lambda n: n.layer):
                values = state(node, time)
                painter.save()
                painter.translate(values["x"], values["y"])
                painter.rotate(values["rotation"])
                painter.scale(values["scale"], values["scale"])
                painter.setOpacity(painter.opacity() * values["opacity"])
                paint_shape(painter, node, time)
                draw(node.id)
                painter.restore()
        draw(None)
    finally:
        painter.end()
    return image
