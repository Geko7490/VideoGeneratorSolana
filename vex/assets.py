"""Immutable content-addressed procedural assets with explicit versioning."""
from pathlib import Path

from .export import fingerprint
from .models import Node, Scene, StrictModel
from .storage import atomic_json


class Asset(StrictModel):
    name: str
    category: str
    version: int
    nodes: list[Node]


class AssetRegistry:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, name, category, nodes: list[Node]):
        # Validate parent references and cycles before storing reusable geometry.
        Scene(id="asset", title=name, duration=600, nodes=nodes)
        previous = [a for a in self.list() if a["name"] == name]
        version = max((a["version"] for a in previous), default=0) + 1
        asset = Asset(name=name, category=category, version=version, nodes=nodes)
        key = fingerprint(asset.model_dump())
        atomic_json(self.root / f"{key}.json", asset.model_dump())
        return key

    def get(self, key):
        import re
        if not re.fullmatch(r"[a-f0-9]{64}", key):
            raise ValueError("Geçersiz asset kimliği")
        return Asset.model_validate_json((self.root / f"{key}.json").read_text(encoding="utf-8"))

    def list(self):
        result = []
        for path in self.root.glob("*.json"):
            asset = Asset.model_validate_json(path.read_text(encoding="utf-8"))
            result.append(dict(key=path.stem, name=asset.name, category=asset.category, version=asset.version, count=len(asset.nodes)))
        return result

    def instantiate(self, key, prefix):
        asset = self.get(key)
        nodes = []
        for node in asset.nodes:
            data = node.model_dump()
            data["id"] = prefix + "_" + node.id
            if node.parent:
                data["parent"] = prefix + "_" + node.parent
            nodes.append(Node.model_validate(data))
        return nodes
