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
PARALLEL_INVENTORY_DIR = COUNTRY_INVENTORY_DIR / "parallels"
PARALLEL_TYPES = ["blue", "red", "purple", "green", "gold"]

def get_parallel_types() -> list[str]:
    return PARALLEL_TYPES

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

def update_sticker_count(inventory: Dict[str, Any], sticker_id: str, count: int) -> None:
    sections = [v for k, v in inventory.items() if isinstance(v, dict) and k not in ("country", "inventory")]
    
    if not sections:
        raise ValueError("Inventory does not contain any sticker sections")

    found = False
    for section in sections:
        if sticker_id in section:
            section[sticker_id] = max(0, count)
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

def get_parallel_inventory_path(country_code: str) -> Path:
    return PARALLEL_INVENTORY_DIR / f"{country_code.upper()}.json"

def load_parallel_inventory(country_code: str) -> Dict[str, Dict[str, int]]:
    path = get_parallel_inventory_path(country_code)
    if not path.exists():
        return {}
    return load_json(path)

def save_parallel_inventory(country_code: str, data: Dict[str, Dict[str, int]]) -> None:
    save_json(get_parallel_inventory_path(country_code), data)

def update_parallel_count(country_code: str, sticker_id: str, parallel_type: str, count: int, counts_as_base: bool = False) -> None:
    inventory = load_parallel_inventory(country_code)
    
    if sticker_id not in inventory:
        inventory[sticker_id] = {
            "counts": {pt: 0 for pt in PARALLEL_TYPES},
            "counts_as_base": False
        }
    elif "counts" not in inventory[sticker_id] and isinstance(inventory[sticker_id], dict):
        # Migrate old format to new format
        old_counts = inventory[sticker_id]
        inventory[sticker_id] = {"counts": old_counts, "counts_as_base": False}

    if parallel_type in PARALLEL_TYPES:
        inventory[sticker_id]["counts"][parallel_type] = max(0, count)
    elif parallel_type != "":
        raise ValueError(f"Invalid parallel type: {parallel_type}")
    
    inventory[sticker_id]["counts_as_base"] = counts_as_base
    save_parallel_inventory(country_code, inventory)

def summarize_missing(inventory: Dict[str, Any], parallels: Dict[str, Any] | None = None) -> Dict[str, int]:
    missing: Dict[str, int] = {}
    parallels = parallels or {}
    for type_name, values in inventory.items():
        if type_name in ("country", "inventory"):
            continue
        if isinstance(values, dict):
            count = 0
            for sid, val in values.items():
                p_data = parallels.get(sid, {})
                p_counts = p_data.get("counts", p_data) if isinstance(p_data, dict) else {}
                p_flag = p_data.get("counts_as_base", False) if isinstance(p_data, dict) else False
                has_eligible_parallel = p_flag and any(v > 0 for v in p_counts.values())
                
                if not (int(val) > 0 or has_eligible_parallel):
                    count += 1
            missing[type_name] = count
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


def missing_items(inventory: Dict[str, Any], parallels: Dict[str, Any] | None = None) -> Dict[str, list[str]]:
    missing_by_type: Dict[str, list[str]] = {}
    parallels = parallels or {}
    for type_name, values in inventory.items():
        if type_name in ("country", "inventory") or not isinstance(values, dict):
            continue
        m_list = []
        for sid, val in values.items():
            p_data = parallels.get(sid, {})
            p_counts = p_data.get("counts", p_data) if isinstance(p_data, dict) else {}
            p_flag = p_data.get("counts_as_base", False) if isinstance(p_data, dict) else False
            has_eligible_parallel = p_flag and any(v > 0 for v in p_counts.values())
            
            if not (int(val) > 0 or has_eligible_parallel):
                m_list.append(sid)
        missing_by_type[type_name] = m_list
    return missing_by_type


def load_countries() -> list[str]:
    return load_json(COUNTRIES_FILE)


def load_types() -> Dict[str, Dict[str, Any]]:
    return load_json(TYPES_FILE)


def load_groups() -> Dict[str, list[str]]:
    return load_json(GROUPS_FILE)
