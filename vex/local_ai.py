"""Only loopback llama.cpp. Managed child process; never remote/cloud inference."""
from __future__ import annotations

import copy
import http.client
import json
import logging
import re
import socket
import subprocess
import time
from pathlib import Path
from typing import Literal

from pydantic import Field

from .jobs import Context
from .models import Camera, Keyframe, Node, Project, Scene, StrictModel, Track
from .runtime import NO_WINDOW

log = logging.getLogger(__name__)


class PlannedObject(StrictModel):
    kind: str = Field(pattern=r"^(robot|building|tower|rectangle|ellipse|text)$")
    x: float = Field(ge=0, le=1280, description="Center x in the 1280x720 canvas")
    y: float = Field(ge=0, le=720, description="Center y in the 1280x720 canvas")
    width: float = Field(ge=5, le=1280)
    height: float = Field(ge=5, le=720)
    color: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")
    end_x: float = Field(ge=0, le=1280, description="End x; different from x for walking robots")
    text: str = Field(max_length=200, description="Text to draw for text nodes; empty otherwise")


class PlannedShot(StrictModel):
    title: str = Field(min_length=1, max_length=100)
    narration: str = Field(min_length=10, max_length=500, description="One or two English sentences spoken by the narrator")
    duration: Literal[4, 6, 8, 10, 12] = Field(description="Scene duration in seconds, typically 6")
    objects: list[PlannedObject] = Field(min_length=2, max_length=12)


class StoryPlan(StrictModel):
    scenes: list[PlannedShot] = Field(min_length=2, max_length=4)


def required_kinds(story):
    words = set(re.findall(r"[a-z]+", story.lower()))
    return {kind for kind, hints in {"robot": {"robot", "robots"}, "tower": {"tower", "towers"}, "building": {"city", "buildings"}}.items() if words & hints}


def check_story_content(plan, story):
    present = {obj.kind for shot in plan.scenes for obj in shot.objects}
    missing = required_kinds(story) - present
    if missing:
        raise ValueError("Story requires visible object kinds: " + ", ".join(sorted(missing)))


def planning_schema(story):
    schema = StoryPlan.model_json_schema()
    required = sorted(required_kinds(story))
    if required:
        objects = schema["$defs"]["PlannedShot"]["properties"]["objects"]
        objects["prefixItems"] = []
        for kind in required:
            definition = copy.deepcopy(schema["$defs"]["PlannedObject"])
            definition["properties"]["kind"] = {"type": "string", "const": kind}
            objects["prefixItems"].append(definition)
        objects["minItems"] = max(2, len(required))
    return schema


def compile_plan(plan: StoryPlan, title: str, story: str):
    scenes = []
    warnings = []
    character_styles = {}
    for i, shot in enumerate(plan.scenes):
        nodes = []
        repair_layout = len({obj.x for obj in shot.objects}) == 1 or any(
            obj.x - obj.width/2 < 0 or obj.x + obj.width/2 > 1280 or obj.y - obj.height/2 < 0 or obj.y + obj.height/2 > 720
            for obj in shot.objects)
        if repair_layout:
            warnings.append(f"{shot.title}: model yerleşimi kadraj dışında/üst üste; güvenli prosedürel yerleşim uygulandı.")
        for j, obj in enumerate(shot.objects):
            obj = obj.model_copy(deep=True)
            if repair_layout:
                if obj.kind == "robot":
                    obj.x, obj.y = 300, 500
                    obj.end_x = 700 if obj.end_x != shot.objects[j].x else 300
                elif obj.kind == "tower":
                    obj.x = obj.end_x = 1000
                    obj.y = 350
                elif obj.kind == "building":
                    obj.x = obj.end_x = 150 + (j % 3) * 220
                    obj.y = 400
                else:
                    obj.x = obj.end_x = 200 + (j % 5) * 200
                    obj.y = 200
                obj.width = min(obj.width, obj.x*2, (1280-obj.x)*2)
                obj.height = min(obj.height, obj.y*2, (720-obj.y)*2)
            if obj.kind == "robot":
                style = (obj.width, obj.height, obj.color)
                if "robot" in character_styles and character_styles["robot"] != style:
                    warnings.append(f"{shot.title}: robot görünümü ilk sahnedeki geometri/renkle eşitlendi.")
                obj.width, obj.height, obj.color = character_styles.setdefault("robot", style)
            tracks = []
            if obj.end_x != obj.x:
                tracks = [Track(property="x", keys=[Keyframe(time=0, value=obj.x), Keyframe(time=shot.duration, value=obj.end_x)])]
            nodes.append(Node(id=f"object{j}", kind=obj.kind, x=obj.x, y=obj.y, width=obj.width, height=obj.height,
                              color=obj.color, text=obj.text, tracks=tracks, layer=2 if obj.kind == "robot" else 1))
        scenes.append(Scene(id=f"scene{i+1}", title=shot.title, narration=shot.narration, duration=shot.duration, nodes=nodes, camera=Camera(pan_x=12)))
    if len({s.narration.strip().lower() for s in scenes}) < len(scenes):
        warnings.append("LLM bazı sahnelerde anlatımı tekrarladı; Scene Director üzerinden düzeltin veya daha güçlü GGUF seçin.")
    return Project(title=title, story=story, scenes=scenes, planning_warnings=warnings)


def request(port, route, data=None, timeout=5):
    # Direct loopback connection needs neither proxy discovery nor TLS/certificate initialization.
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    try:
        payload = json.dumps(data).encode() if data is not None else None
        connection.request("POST" if data is not None else "GET", route, payload, {"Content-Type": "application/json"})
        response = connection.getresponse()
        body = response.read()
        if response.status >= 400:
            raise OSError(f"llama-server HTTP {response.status}: {body.decode(errors='replace')[:1000]}")
        return json.loads(body)
    finally:
        connection.close()


class LocalDirector:
    def __init__(self, settings):
        self.settings = settings

    def plan(self, story, title, context: Context):
        server = Path(self.settings.get("llama_server", ""))
        model = Path(self.settings.get("gguf", ""))
        if not server.is_file() or not model.is_file() or model.suffix.lower() != ".gguf":
            raise ValueError("Ayarlar'da gerçek llama-server.exe ve GGUF dosyası seçin")
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        log_path = Path(self.settings["data_root"]) / "llama-server.log"
        with log_path.open("w", encoding="utf-8") as server_log:
            layers = int(self.settings.get("gpu_layers", 0))
            def start(gpu_layers):
                return subprocess.Popen([str(server), "-m", str(model), "--host", "127.0.0.1", "--port", str(port),
                                         "-c", "8192", "-ngl", str(gpu_layers)], stdout=server_log, stderr=server_log, creationflags=NO_WINDOW)
            process = start(layers)
            try:
                context.report(0, "Yerel GGUF yükleniyor; yükleme yüzdesi runtime tarafından sağlanmıyor")
                deadline = time.monotonic() + 300
                while True:
                    context.check()
                    if process.poll() is not None:
                        if layers:
                            layers = 0
                            context.report(0, "GPU model yükleme başarısız; CPU fallback deneniyor")
                            process = start(0)
                            deadline = time.monotonic() + 300
                            continue
                        raise RuntimeError(f"llama-server başlatılamadı. Günlük: {log_path}")
                    try:
                        request(port, "/health", timeout=.5)
                        break
                    except (OSError, http.client.HTTPException) as exc:
                        log.debug("Model health not ready: %s", exc)
                        if time.monotonic() > deadline:
                            raise TimeoutError("Model yükleme 300 saniyede tamamlanmadı")
                        context.cancel.wait(.2)
                context.report(0, "Yerel LLM sahne planlıyor; token akışı yüzdesi bilinmiyor")
                prompt = ("You are a procedural animation director. Return ONLY a project JSON matching the supplied schema. "
                          "Use a 1280x720 canvas. Only 2d and motion engines are implemented. "
                          "Use robot/building/tower primitives or compose rectangle/ellipse/text nodes. "
                          "English narration only. 2 to 4 short scenes, 4 to 10 seconds each. "
                          "Keep character colors and proportions consistent. No code, file paths or commands. "
                          "Object coordinates are centers in pixels. Put robots at y=500, width=100, height=160. "
                          "Buildings are 100x300 at y=400. Tower is 100x400 near x=1000, y=350. "
                          "Use x=300 and end_x=700 to walk right. Use matching x and end_x for stationary objects. "
                          "Write actual English narration in EVERY scene. Make two or three scenes. "
                          "Required visible object kinds in this story: " + ", ".join(sorted(required_kinds(story))) + ". "
                          "Never omit these important objects. Title: " + title)
                messages = [{"role": "system", "content": prompt}, {"role": "user", "content": story}]
                error = ""
                for attempt in range(3):
                    context.check()
                    # Inference is isolated in a child request thread; cancellation terminates server below.
                    from concurrent.futures import ThreadPoolExecutor
                    from concurrent.futures import TimeoutError as FutureTimeout
                    pool = ThreadPoolExecutor(max_workers=1)
                    future = pool.submit(request, port, "/v1/chat/completions", {
                        "messages": messages,
                        "temperature": .4,
                        "max_tokens": 6500,
                        "response_format": {"type": "json_schema", "json_schema": {"name": "story_plan", "schema": planning_schema(story)}},
                    }, 600)
                    try:
                        while True:
                            context.check()
                            try:
                                response = future.result(timeout=.2)
                                break
                            except FutureTimeout:
                                continue
                    finally:
                        pool.shutdown(wait=False, cancel_futures=True)
                    raw = response["choices"][0]["message"]["content"]
                    try:
                        plan = StoryPlan.model_validate_json(raw)
                        check_story_content(plan, story)
                        project = compile_plan(plan, title, story)
                        context.report(1, "Sahne JSON doğrulandı")
                        return project
                    except ValueError as exc:
                        error = str(exc)
                        messages += [{"role": "assistant", "content": raw}, {"role": "user", "content": f"Fix JSON validation errors: {error[:3000]}"}]
                raise ValueError(f"LLM çıktısı 3 denemede doğrulanamadı: {error}")
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
