from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable

BASE_DIR = Path(__file__).resolve().parent
COUNTRIES_FILE = BASE_DIR / "countries.json"
TYPES_FILE = BASE_DIR / "types.json"
GROUPS_FILE = BASE_DIR / "groups.json"
COUNTRY_INVENTORY_DIR = BASE_DIR / "country_inventory"
GLOBAL_INVENTORY_FILE = COUNTRY_INVENTORY_DIR / "global_inventory.json"

def save_global_inventory(inventory: Dict[str, Any]) -> None:
    save_json(GLOBAL_INVENTORY_FILE, inventory)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)


def make_flag_map(prefix: str, count: int) -> Dict[str, int]:
    return {
        f"{prefix}{i}" if prefix else str(i): 0
        for i in range(1, count + 1)
    }


def get_types_by_scope(types: Dict[str, Dict[str, Any]], scope: str) -> Dict[str, Dict[str, Any]]:
    return {
        type_name: type_config
        for type_name, type_config in types.items()
        if type_config.get("scope", "country") == scope
    }


def build_country_inventory(country_code: str, types: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    inventory: Dict[str, Any] = {
        "country": country_code,
    }

    country_types = get_types_by_scope(types, "country")
    for type_name, type_config in country_types.items():
        inventory[type_name] = make_flag_map(
            prefix=type_config.get("prefix", ""),
            count=int(type_config.get("count", 0)),
        )

    return inventory


def build_global_inventory(types: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    inventory: Dict[str, Any] = {
        "inventory": "global",
    }

    global_types = get_types_by_scope(types, "global")
    for type_name, type_config in global_types.items():
        inventory[type_name] = make_flag_map(
            prefix=type_config.get("prefix", ""),
            count=int(type_config.get("count", 0)),
        )

    return inventory


def load_country_inventory(path: Path) -> Dict[str, Any]:
    return load_json(path)


def get_country_inventory_path(country_code: str, folder: Path | None = None) -> Path:
    if folder is None:
        folder = COUNTRY_INVENTORY_DIR
    return folder / f"{country_code.upper()}.json"


def load_country_inventory_by_code(country_code: str, folder: Path | None = None) -> Dict[str, Any]:
    return load_country_inventory(get_country_inventory_path(country_code, folder))


def save_country_inventory(country_code: str, inventory: Dict[str, Any], folder: Path | None = None) -> None:
    save_json(get_country_inventory_path(country_code, folder), inventory)


def apply_stickers(inventory: Dict[str, Any], sticker_ids: Iterable[str]) -> None:
    sections = [v for k, v in inventory.items() if isinstance(v, dict) and k not in ("country", "inventory")]
    
    if not sections:
        raise ValueError("Inventory does not contain any sticker sections")

    for sticker_id in sticker_ids:
        found = False
        for section in sections:
            if sticker_id in section:
                section[sticker_id] = int(section.get(sticker_id, 0)) + 1
                found = True
                break
        if not found:
            raise ValueError(f"Sticker id '{sticker_id}' is invalid")


def load_all_inventories(folder: Path) -> Dict[str, Dict[str, Any]]:
    inventories: Dict[str, Dict[str, Any]] = {}
    for json_path in sorted(folder.glob("*.json")):
        inventory = load_country_inventory(json_path)
        country_code = inventory.get("country")
        if not country_code:
            continue
        inventories[country_code] = inventory
    return inventories


def load_global_inventory(path: Path) -> Dict[str, Any]:
    return load_json(path)


def summarize_missing(inventory: Dict[str, Any]) -> Dict[str, int]:
    missing: Dict[str, int] = {}
    for type_name, values in inventory.items():
        if type_name in ("country", "inventory"):
            continue
        if isinstance(values, dict):
            missing[type_name] = sum(1 for flag in values.values() if not flag)
    return missing


def summarize_duplicates(inventory: Dict[str, Any]) -> Dict[str, int]:
    duplicates: Dict[str, int] = {}
    for type_name, values in inventory.items():
        if type_name in ("country", "inventory"):
            continue
        if isinstance(values, dict):
            # Sum up extra copies (count - 1 for those > 1)
            duplicates[type_name] = sum(int(val) - 1 for val in values.values() if int(val) > 1)
    return duplicates


def missing_items(inventory: Dict[str, Any]) -> Dict[str, list[str]]:
    missing_by_type: Dict[str, list[str]] = {}
    for type_name, values in inventory.items():
        if type_name in ("country", "inventory") or not isinstance(values, dict):
            continue
        missing_by_type[type_name] = [key for key, flag in values.items() if not int(flag)]
    return missing_by_type


def load_countries() -> list[str]:
    return load_json(COUNTRIES_FILE)


def load_types() -> Dict[str, Dict[str, Any]]:
    return load_json(TYPES_FILE)


def load_groups() -> Dict[str, list[str]]:
    return load_json(GROUPS_FILE)
