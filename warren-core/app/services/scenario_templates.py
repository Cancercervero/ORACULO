# warren-core/app/services/scenario_templates.py
import json
from pathlib import Path
from typing import Optional

_TEMPLATES: dict[str, list[str]] = {}


def load_templates(path: Optional[Path] = None) -> None:
    global _TEMPLATES
    if path is None:
        path = Path(__file__).parent.parent.parent / "data" / "scenario_templates.json"
    with open(path) as f:
        _TEMPLATES = json.load(f)


def get_node_labels(template: str) -> list[str]:
    if not _TEMPLATES:
        load_templates()
    labels = _TEMPLATES.get(template)
    if labels is None:
        raise ValueError(f"Unknown template: {template!r}. Valid: {list(_TEMPLATES.keys())}")
    return labels


def list_templates() -> list[str]:
    if not _TEMPLATES:
        load_templates()
    return list(_TEMPLATES.keys())
