import pytest

from vex.assets import AssetRegistry
from vex.models import Node


def test_asset_versions_are_immutable_and_references_are_namespaced(tmp_path):
    registry = AssetRegistry(tmp_path)
    nodes = [Node(id="body", kind="group"), Node(id="head", kind="ellipse", parent="body", color="#abcdef")]
    first = registry.put("Robot", "character", nodes)
    nodes[1].color = "#112233"
    second = registry.put("Robot", "character", nodes)
    assert first != second
    assert registry.get(first).nodes[1].color == "#abcdef"
    assert registry.get(second).version == 2
    instance = registry.instantiate(first, "hero")
    assert instance[1].parent == "hero_body"
    assert instance[1].color == "#abcdef"
    with pytest.raises(ValueError):
        registry.get("../../bad")
