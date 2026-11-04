from threading import Event

import pytest
from pydantic import ValidationError

from vex.drawing import evaluate, render
from vex.jobs import Cancelled, Context, Scheduler, Task
from vex.models import Keyframe, Project, Scene, Track
from vex.sample import example_project
from vex.storage import Store


def test_project_round_trip_and_invalid_manifest(tmp_path):
    store = Store(tmp_path)
    project = example_project()
    path = store.save(project)
    assert store.load(path) == project
    assert store.recent()[0]["title"] == project.title
    original = path.read_bytes()
    invalid = project.model_dump()
    invalid["scenes"][0]["nodes"][0]["kind"] = "python"
    with pytest.raises(ValidationError):
        store.save(Project.model_validate(invalid))
    assert path.read_bytes() == original
    path.write_text('{"schema_version": 999}', encoding="utf-8")
    with pytest.raises(ValidationError):
        store.load(path)


@pytest.mark.parametrize("mutate", [
    lambda p: p["scenes"][0]["nodes"][0].update(kind="shell"),
    lambda p: p["scenes"][0]["nodes"][0].update(parent="missing"),
    lambda p: p["scenes"][0]["nodes"][0].update(parent="moon"),
    lambda p: p["scenes"][0]["nodes"][0].update(x=float("nan")),
    lambda p: p["scenes"][0]["nodes"][0].update(script="print('bad')"),
    lambda p: p["scenes"][0]["nodes"].append(p["scenes"][0]["nodes"][0]),
    lambda p: p.update(id="../../outside"),
])
def test_dsl_rejects_unsafe_or_broken_graph(mutate):
    data = example_project().model_dump()
    mutate(data)
    with pytest.raises(ValidationError):
        Project.model_validate(data)


def test_time_based_animation():
    track = Track(property="x", keys=[Keyframe(time=0, value=0), Keyframe(time=2, value=100)])
    assert evaluate(track, 1) == 50
    assert evaluate(track, 30 / 30) == evaluate(track, 60 / 60)
    assert evaluate(track, 10) == 100
    with pytest.raises(ValidationError):
        Track(property="x", keys=[Keyframe(time=2, value=1), Keyframe(time=1, value=2)])


def test_actual_frame_and_parent_transforms():
    scene = Scene.model_validate(dict(id="test", title="Test", background="#000000", nodes=[
        dict(id="root", kind="group", x=100, y=100),
        dict(id="child", kind="rectangle", parent="root", x=20, y=20, width=10, height=10, color="#ff0000"),
    ]))
    image = render(scene, 0, 1280, 720)
    assert image.pixelColor(120, 120).name() == "#ff0000"
    assert image.pixelColor(20, 20).name() == "#000000"
    animated = example_project().scenes[0]
    assert bytes(render(animated, 0, 640, 360).constBits()) != bytes(render(animated, 2, 640, 360).constBits())


def test_scheduler_dependencies_failure_and_persistence(tmp_path):
    store = Store(tmp_path)
    scheduler = Scheduler(store)
    events = []
    first = Task("one", lambda ctx: 42)
    second = Task("two", lambda ctx: ctx.values["one"] + 1, ("one",))
    result = scheduler.start([first, second], lambda *event: events.append(event)).result(timeout=5)
    assert result["two"] == 43
    assert events[-1][0] == "COMPLETED"
    assert store.history()[0]["status"] == "COMPLETED"
    with pytest.raises(ValueError):
        scheduler.start([second, first], lambda *event: None)
    with pytest.raises(ZeroDivisionError):
        scheduler.start([Task("bad", lambda ctx: 1 / 0)], lambda *event: None).result(timeout=5)
    assert store.history()[0]["status"] == "FAILED"
    scheduler.close()


def test_cancel_and_interrupted_recovery(tmp_path):
    store = Store(tmp_path)
    scheduler = Scheduler(store)
    started = Event()
    def wait(ctx):
        started.set()
        ctx.cancel.wait(5)
        ctx.check()
    future = scheduler.start([Task("wait", wait)], lambda *event: None)
    assert started.wait(3)
    scheduler.cancel()
    with pytest.raises(Cancelled):
        future.result(timeout=3)
    assert store.history()[0]["status"] == "CANCELLED"
    scheduler.close()
    store.job("crashed", "Render", "RUNNING", .3)
    assert Store(tmp_path).history()[0]["status"] == "INTERRUPTED"


def test_cancel_context():
    event = Event()
    event.set()
    with pytest.raises(Cancelled):
        Context(event, lambda *args: None).check()
