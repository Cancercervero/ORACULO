from pathlib import Path

_PERSONAS_DIR = Path(__file__).parent / "personas"

_REGION_MAP: dict[str, list[str]] = {
    "Baltic":   ["putin_persona", "trump_persona", "dalio_persona", "powell_persona"],
    "Taiwan":   ["xi_jinping_persona", "trump_persona", "dalio_persona"],
    "MidEast":  ["trump_persona", "dalio_persona", "powell_persona"],
    "Ukraine":  ["putin_persona", "trump_persona", "dalio_persona"],
    "Global":   ["dalio_persona", "powell_persona", "musk_persona"],
}

_TEMPLATE_MAP: dict[str, list[str]] = {
    "economic_crisis":  ["dalio_persona", "powell_persona", "musk_persona"],
    "diplomatic":       ["trump_persona", "putin_persona", "xi_jinping_persona"],
    "cyber_incident":   ["musk_persona", "trump_persona", "dalio_persona"],
}

_DEFAULT_PERSONAS = ["trump_persona", "dalio_persona", "powell_persona"]


def select_personas(region: str, template: str) -> list[str]:
    """
    Returns persona base names (without .json) for a given region + template.
    Only returns personas whose JSON file actually exists.
    """
    candidates = _REGION_MAP.get(region) or _TEMPLATE_MAP.get(template) or _DEFAULT_PERSONAS
    return [p for p in candidates if (_PERSONAS_DIR / f"{p}.json").exists()]
