"""Declarative scene language. Data never becomes executable code."""
from __future__ import annotations

import math
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, validate_assignment=True)


class Keyframe(StrictModel):
    time: float = Field(ge=0, le=3600)
    value: float = Field(ge=-100000, le=100000)
    easing: Literal["linear", "smooth", "in", "out"] = "smooth"


class Track(StrictModel):
    property: Literal["x", "y", "rotation", "scale", "opacity"]
    keys: list[Keyframe] = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def ordered(self):
        if any(a.time >= b.time for a, b in zip(self.keys, self.keys[1:])):
            raise ValueError("Keyframe zamanları benzersiz ve artan olmalı")
        if self.property == "opacity" and any(not 0 <= k.value <= 1 for k in self.keys):
            raise ValueError("Opacity 0..1 aralığında olmalı")
        if self.property == "scale" and any(not 0.001 <= k.value <= 100 for k in self.keys):
            raise ValueError("Scale 0.001..100 aralığında olmalı")
        return self


class Node(StrictModel):
    id: str = Field(pattern=r"^[a-zA-Z][a-zA-Z0-9_-]{0,63}$")
    kind: Literal["rectangle", "ellipse", "line", "polygon", "path", "text", "particles", "robot", "building", "tower", "group"]
    parent: str | None = None
    x: float = Field(default=0, ge=-100000, le=100000)
    y: float = Field(default=0, ge=-100000, le=100000)
    width: float = Field(default=100, gt=0, le=10000)
    height: float = Field(default=100, gt=0, le=10000)
    rotation: float = Field(default=0, ge=-100000, le=100000)
    scale: float = Field(default=1, ge=0.001, le=100)
    opacity: float = Field(default=1, ge=0, le=1)
    color: str = Field(default="#a78bfa", pattern=r"^#[0-9a-fA-F]{6}$")
    stroke: str = Field(default="#e9e5ff", pattern=r"^#[0-9a-fA-F]{6}$")
    stroke_width: float = Field(default=0, ge=0, le=100)
    text: str = Field(default="", max_length=2000)
    text_effect: Literal["none", "typewriter", "reveal"] = "none"
    text_rate: float = Field(default=16, gt=0, le=200)
    gradient: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    clip: bool = False
    particle_count: int = Field(default=40, ge=1, le=500)
    points: list[tuple[float, float]] = Field(default_factory=list, max_length=256)
    layer: int = Field(default=0, ge=-1000, le=1000)
    tracks: list[Track] = Field(default_factory=list, max_length=5)

    @model_validator(mode="after")
    def valid_geometry(self):
        if self.kind == "polygon" and len(self.points) < 3:
            raise ValueError("Polygon en az üç nokta gerektirir")
        if self.kind == "path" and (len(self.points) < 4 or (len(self.points) - 1) % 3):
            raise ValueError("Bezier path: başlangıç noktası ve üçlü kontrol/kontrol/bitiş noktaları gerekir")
        if any(not math.isfinite(v) or abs(v) > 100000 for p in self.points for v in p):
            raise ValueError("Geçersiz polygon koordinatı")
        if len({t.property for t in self.tracks}) != len(self.tracks):
            raise ValueError("Aynı özellik için birden fazla track olamaz")
        return self


class Camera(StrictModel):
    x: float = Field(default=0, ge=-100000, le=100000)
    y: float = Field(default=0, ge=-100000, le=100000)
    zoom: float = Field(default=1, ge=0.01, le=20)
    pan_x: float = Field(default=0, ge=-100000, le=100000)
    pan_y: float = Field(default=0, ge=-100000, le=100000)


class Scene(StrictModel):
    id: str = Field(pattern=r"^[a-zA-Z][a-zA-Z0-9_-]{0,63}$")
    title: str = Field(min_length=1, max_length=200)
    duration: float = Field(default=5, ge=0.1, le=600)
    engine: Literal["2d", "motion", "3d"] = "2d"
    narration: str = Field(default="", max_length=5000)
    background: str = Field(default="#111526", pattern=r"^#[0-9a-fA-F]{6}$")
    camera: Camera = Field(default_factory=Camera)
    nodes: list[Node] = Field(default_factory=list, max_length=500)

    @model_validator(mode="after")
    def graph(self):
        lookup = {node.id: node for node in self.nodes}
        if len(lookup) != len(self.nodes):
            raise ValueError("Nesne kimlikleri sahne içinde benzersiz olmalı")
        for node in self.nodes:
            seen = {node.id}
            parent = node.parent
            while parent is not None:
                if parent not in lookup:
                    raise ValueError(f"Parent bulunamadı: {parent}")
                if parent in seen:
                    raise ValueError("Scene graph döngü içeriyor")
                seen.add(parent)
                if len(seen) > 32:
                    raise ValueError("Scene graph derinlik sınırı 32")
                parent = lookup[parent].parent
            if any(k.time > self.duration for tr in node.tracks for k in tr.keys):
                raise ValueError("Keyframe sahne süresini aşıyor")
        return self


class ExportSettings(StrictModel):
    resolution: Literal[480, 720, 1080, 1440, 2160] = 720
    fps: Literal[24, 30, 60] = 24
    aspect: Literal["16:9", "9:16", "1:1"] = "16:9"
    burn_subtitles: bool = False

    def dimensions(self, preview=False):
        side = 360 if preview else self.resolution
        if self.aspect == "1:1":
            return side, side
        long_side = round(side * 16 / 9 / 2) * 2
        return (long_side, side) if self.aspect == "16:9" else (side, long_side)


class Project(StrictModel):
    schema_version: Literal[1] = 1
    id: str = Field(default_factory=lambda: str(uuid4()), pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    title: str = Field(default="Untitled story", min_length=1, max_length=200)
    story: str = Field(default="", max_length=20000)
    export: ExportSettings = Field(default_factory=ExportSettings)
    scenes: list[Scene] = Field(default_factory=list, max_length=100)
    planning_warnings: list[str] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def unique_scenes(self):
        if len({s.id for s in self.scenes}) != len(self.scenes):
            raise ValueError("Sahne kimlikleri benzersiz olmalı")
        if sum(s.duration for s in self.scenes) > 3600:
            raise ValueError("Proje en fazla bir saat olabilir")
        return self
