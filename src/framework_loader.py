from __future__ import annotations

from pathlib import Path

import yaml

from .models import Framework


def load_framework(path: str | Path) -> Framework:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        payload = yaml.safe_load(f)
    return Framework.model_validate(payload)


def load_frameworks(root: str | Path) -> dict[str, Framework]:
    root = Path(root)
    frameworks: dict[str, Framework] = {}
    for path in sorted(root.rglob("*.yaml")):
        if path.name == "source_registry.yaml":
            continue
        framework = load_framework(path)
        if framework.framework_id in frameworks:
            raise ValueError(f"Duplicate framework_id: {framework.framework_id}")
        frameworks[framework.framework_id] = framework
    return frameworks
