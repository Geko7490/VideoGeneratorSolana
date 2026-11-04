import pytest
from pydantic import ValidationError

from vex.local_ai import StoryPlan, compile_plan


def test_story_contract_requires_real_narration_and_compiles_motion():
    obj = dict(kind="robot", x=300, y=500, width=100, height=160, color="#a78bfa", end_x=700, text="")
    shot = dict(title="Walking", narration="The robot walks through the city.", duration=6, objects=[obj, obj | dict(kind="tower", x=1000, end_x=1000)])
    plan = StoryPlan.model_validate(dict(scenes=[shot, shot | dict(title="Discovery")]))
    project = compile_plan(plan, "Robot", "A robot explores.")
    assert project.scenes[0].nodes[0].tracks[0].keys[-1].value == 700
    assert project.scenes[1].nodes[0].color == project.scenes[0].nodes[0].color
    assert project.scenes[0].narration
    with pytest.raises(ValidationError):
        StoryPlan.model_validate(dict(scenes=[shot | dict(narration=""), shot]))
    with pytest.raises(ValidationError):
        StoryPlan.model_validate(dict(scenes=[shot | dict(duration=500), shot]))


def test_planner_offscreen_overlap_recovery_is_visible_and_consistent():
    obj = dict(kind="robot", x=1280, y=500, width=100, height=160, color="#ff5733", end_x=700, text="")
    shot = dict(title="Walking", narration="The robot explores the abandoned city.", duration=6,
                objects=[obj, obj | dict(kind="tower", y=350, height=400, end_x=1280), obj | dict(kind="building", y=400, height=300, end_x=1280)])
    second = shot | dict(title="Discovery", objects=[obj | dict(color="#aabbcc"), *shot["objects"][1:]])
    project = compile_plan(StoryPlan.model_validate(dict(scenes=[shot, second])), "Robot", "Robot city tower")
    assert project.planning_warnings
    assert len({n.x for n in project.scenes[0].nodes}) == 3
    assert project.scenes[0].nodes[0].color == project.scenes[1].nodes[0].color
    assert project.scenes[0].camera.pan_x != 0
