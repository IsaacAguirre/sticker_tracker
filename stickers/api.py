from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
import os
import re

from fastapi import Depends, FastAPI, HTTPException, Header
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, validator

from storage.base import StorageProvider
from storage.local_storage import LocalStorageProvider

from inventory import (
    BASE_DIR,
    COUNTRY_INVENTORY_DIR,
    apply_stickers,
    get_parallel_types,
    update_sticker_count,
    get_types_by_scope,
    load_countries,
    load_groups,
    load_types,
    load_json,
)

app = FastAPI(
    title="Panini World Cup Sticker Tracker",
    description="API for updating country sticker inventory and reporting missing stickers.",
)

STATIC_DIR = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class StickerUpdate(BaseModel):
    stickers: list[str] | str

    @validator("stickers", pre=True)
    def parse_stickers(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return [str(item) for item in value]
        return []

    @validator("stickers")
    def validate_stickers(cls, stickers: list[str]) -> list[str]:
        if not stickers:
            raise ValueError("stickers list must not be empty")
        return sorted(stickers)


class StickerCountUpdate(BaseModel):
    sticker_id: str
    count: int

class ParallelUpdate(BaseModel):
    sticker_id: str
    parallel_type: str
    count: int


def normalize_country_code(country_code: str) -> str:
    return country_code.strip().upper()


def get_inventory_path_for_country(country_code: str) -> Path:
    return COUNTRY_INVENTORY_DIR / f"{country_code}.json"


def get_global_types() -> list[str]:
    types = load_types()
    global_types_config = get_types_by_scope(types, "global")
    # Explicitly define the order for FWC and CC
    ordered_global_types = []
    if "FWC" in global_types_config:
        ordered_global_types.append("FWC")
    if "CC" in global_types_config:
        ordered_global_types.append("CC")
    return ordered_global_types


def load_country_names() -> dict[str, str]:
    names_path = BASE_DIR / "country_names.json"
    try:
        return load_json(names_path)
    except FileNotFoundError:
        return {}


def get_country_name(country_code: str) -> str:
    return load_country_names().get(normalize_country_code(country_code), country_code)

STORAGE_PROVIDER = os.getenv("STORAGE_PROVIDER", "local").lower()


def get_storage() -> StorageProvider:
    if STORAGE_PROVIDER == "firestore":
        from storage.firestore_storage import FirestoreStorageProvider

        return FirestoreStorageProvider()
    return LocalStorageProvider()


def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    if STORAGE_PROVIDER == "local":
        return "local_user"

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    from firebase_auth import verify_firebase_token

    try:
        return verify_firebase_token(authorization)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def natural_sort_key(s: str) -> list[int | str]:
    """Helper to sort strings containing numbers numerically (e.g., MEX2 before MEX10)."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]


def ensure_country_exists(country_code: str) -> None:
    country_code = normalize_country_code(country_code)
    if country_code in [t.upper() for t in get_global_types()]:
        return
    if country_code not in load_countries():
        raise HTTPException(status_code=404, detail=f"Country {country_code} not found")


def collect_country_reports(storage: StorageProvider, user_id: str) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    tracked_countries = set(load_countries())

    for country_code in sorted(tracked_countries):
        try:
            inventory = storage.load_country_inventory(user_id, country_code)
        except FileNotFoundError:
            continue
        reports.append(build_inventory_report(country_code, inventory, storage, user_id))

    return reports


def collect_global_reports(storage: StorageProvider, user_id: str) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    global_map = {t.upper(): t for t in get_global_types()}

    try:
        inventory = storage.load_global_inventory(user_id)
    except FileNotFoundError:
        return reports

    for code, section_name in global_map.items():
        reports.append(build_inventory_report(section_name, inventory, storage, user_id, target_section=section_name))

    return reports


def slice_reports_with_ties(reports: list[dict[str, Any]], limit: int = 10) -> tuple[list[dict[str, Any]], int, float | None]:
    displayed_reports = reports[:limit]
    tie_count = 0
    tie_percentage = None

    if len(reports) > limit:
        tie_percentage = displayed_reports[-1]["completion_percentage"]
        tie_count = sum(
            1
            for report in reports[limit:]
            if report["completion_percentage"] == tie_percentage
        )

    return displayed_reports, tie_count, tie_percentage


def build_inventory_report(name: str, inventory: dict[str, Any], storage: StorageProvider, user_id: str, target_section: str | None = None) -> dict[str, Any]:
    found = []
    missing = []
    duplicates = {}
    total_count = 0
    total_duplicates_count = 0
    found_count = 0
    unique_filled_count = 0
    sections_data = {}
    lookup_code = target_section if target_section else name
    parallels = storage.load_parallel_inventory(user_id, lookup_code)

    for type_name, stickers in inventory.items():
        if not isinstance(stickers, dict) or type_name in ("country", "inventory"):
            continue
        
        if target_section and type_name != target_section:
            continue

        sections_data[type_name] = stickers
        for key, value in stickers.items():
            count = int(value)
            total_count += 1

            # Check if we have either the base sticker OR any parallel version
            has_parallel = any(v > 0 for v in parallels.get(key, {}).values())
            if count > 0 or has_parallel:
                unique_filled_count += 1

            if count > 0:
                found.append(key)
                found_count += 1
                if count > 1:
                    duplicates[key] = (count - 1)
                    total_duplicates_count += (count - 1)
            else:
                missing.append(key)

    percentage = (found_count / total_count * 100) if total_count > 0 else 0

    return {
        "country": name,
        "found": found,
        "missing": missing,
        "duplicates": duplicates,
        "completion_percentage": round(percentage, 2),
        "counts": {
            "found": found_count,
            "unique_filled": unique_filled_count,
            "missing": len(missing),
            "total": total_count,
            "total_duplicates": total_duplicates_count,
        },
        "sections": sections_data,
        "parallels": parallels,
        "parallel_types": get_parallel_types() if lookup_code.upper() not in [t.upper() for t in get_global_types()] else [],
    }


@app.get("/countries")
def list_countries() -> dict[str, Any]:
    ordered_list = []
    
    global_types = get_global_types() # Returns ['FWC', 'CC']
    all_country_codes = load_countries() # All 48 country codes
    wc_groups = load_groups() # Group A, B, C... with their countries

    # 1. Add FWC
    if "FWC" in global_types:
        ordered_list.append("FWC")

    # 2. Add countries by World Cup group order (A, B, C...)
    for group_letter in sorted(wc_groups.keys()): # Ensures A, B, C order
        for country_code_in_group in wc_groups[group_letter]:
            if country_code_in_group in all_country_codes: # Only add if it's a valid country code we track
                ordered_list.append(country_code_in_group)
    
    # 3. Add CC
    if "CC" in global_types:
        ordered_list.append("CC")

    return {"countries": ordered_list}


@app.get("/groups")
def list_groups() -> dict[str, Any]:
    groups = {"Global": ["FWC", "CC"]}
    groups.update(load_groups())
    return {"groups": groups}


@app.get("/summary")
def summary_report(storage: StorageProvider = Depends(get_storage), user_id: str = Depends(get_current_user)) -> dict[str, Any]:
    country_reports = collect_country_reports(storage, user_id)
    global_reports = collect_global_reports(storage, user_id)
    for report in country_reports:
        report["country_name"] = get_country_name(report["country"])
    for report in global_reports:
        report["country_name"] = report["country"]

    total_reports = country_reports + global_reports
    total_possible_stickers = sum(report["counts"]["total"] for report in total_reports)
    total_owned_sticker_ids = sum(report["counts"]["found"] for report in total_reports)
    total_unique_slots_filled = sum(report["counts"]["unique_filled"] for report in total_reports)
    total_missing_sticker_ids = sum(report["counts"]["missing"] for report in total_reports)
    total_duplicates = sum(report["counts"].get("total_duplicates", 0) for report in total_reports)

    # Calculate global completion stats
    total_inventories_completed = sum(
        1 for report in total_reports if report["counts"]["found"] == report["counts"]["total"]
    )
    inventory_completion_percentage = (
        round((total_inventories_completed / len(total_reports) * 100), 2) if total_reports else 0
    )
    overall_sticker_completion_percentage = (
        round((total_owned_sticker_ids / total_possible_stickers * 100), 2) if total_possible_stickers > 0 else 0
    )
    overall_unique_completion_percentage = (
        round((total_unique_slots_filled / total_possible_stickers * 100), 2) if total_possible_stickers > 0 else 0
    )

    sorted_desc = sorted(
        country_reports,
        key=lambda report: (-report["completion_percentage"], report["country_name"], report["country"]),
    )
    sorted_asc = sorted(
        country_reports,
        key=lambda report: (report["completion_percentage"], report["country_name"], report["country"]),
    )

    top_countries, top_tie_count, top_tie_percentage = slice_reports_with_ties(sorted_desc)
    bottom_countries, bottom_tie_count, bottom_tie_percentage = slice_reports_with_ties(sorted_asc)

    return {
        "country_count": len(country_reports),
        "global_count": len(global_reports),
        "total_tracked_inventories": len(total_reports),
        "total_possible_stickers": total_possible_stickers,
        "total_owned_sticker_ids": total_owned_sticker_ids,
        "total_duplicates": total_duplicates,
        "total_inventories_completed": total_inventories_completed,
        "inventory_completion_percentage": inventory_completion_percentage,
        "overall_sticker_completion_percentage": overall_sticker_completion_percentage,
        "total_unique_slots_filled": total_unique_slots_filled,
        "overall_unique_completion_percentage": overall_unique_completion_percentage,
        "total_missing_sticker_ids": total_missing_sticker_ids,
        "top_countries": top_countries,
        "top_tie_count": top_tie_count,
        "top_tie_percentage": top_tie_percentage,
        "bottom_countries": bottom_countries,
        "bottom_tie_count": bottom_tie_count,
        "bottom_tie_percentage": bottom_tie_percentage,
    }


@app.get("/add", response_class=HTMLResponse)
def add_page() -> HTMLResponse:
    add_path = STATIC_DIR / "add.html"
    if not add_path.exists():
        raise HTTPException(status_code=500, detail="Add sticker page not found")
    return HTMLResponse(add_path.read_text(encoding="utf-8"))


@app.get("/inventory/{country_code}")
def read_country_inventory(
    country_code: str,
    storage: StorageProvider = Depends(get_storage),
    user_id: str = Depends(get_current_user),
) -> dict[str, Any]:
    normalized_code = normalize_country_code(country_code)
    
    global_map = {t.upper(): t for t in get_global_types()}
    if normalized_code in global_map:
        inventory = storage.load_global_inventory(user_id)
        section_name = global_map[normalized_code]
        report = build_inventory_report(section_name, inventory, storage, user_id, target_section=section_name)
        report["country_name"] = section_name
        return report

    ensure_country_exists(normalized_code)
    try:
        inventory = storage.load_country_inventory(user_id, normalized_code)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Inventory file not found for {normalized_code}")

    report = build_inventory_report(normalized_code, inventory, storage, user_id)
    report["country_name"] = get_country_name(normalized_code)
    return report


@app.post("/inventory/{country_code}")
def add_country_stickers(
    country_code: str,
    payload: StickerUpdate,
    storage: StorageProvider = Depends(get_storage),
    user_id: str = Depends(get_current_user),
) -> dict[str, Any]:
    normalized_code = normalize_country_code(country_code)
    
    global_map = {t.upper(): t for t in get_global_types()}
    if normalized_code in global_map:
        inventory = storage.load_global_inventory(user_id)
        section_name = global_map[normalized_code]
        try:
            apply_stickers(inventory, payload.stickers)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        storage.save_global_inventory(user_id, inventory)
        return build_inventory_report(section_name, inventory, storage, user_id, target_section=section_name)

    ensure_country_exists(normalized_code)
    try:
        inventory = storage.load_country_inventory(user_id, normalized_code)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Inventory file not found for {normalized_code}")

    try:
        apply_stickers(inventory, payload.stickers)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    storage.save_country_inventory(user_id, normalized_code, inventory)
    report = build_inventory_report(normalized_code, inventory, storage, user_id)
    report["country_name"] = get_country_name(normalized_code)
    return report

@app.patch("/inventory/{country_code}/sticker")
def update_single_sticker(
    country_code: str,
    payload: StickerCountUpdate,
    storage: StorageProvider = Depends(get_storage),
    user_id: str = Depends(get_current_user),
) -> dict[str, Any]:
    normalized_code = normalize_country_code(country_code)
    
    global_map = {t.upper(): t for t in get_global_types()}
    if normalized_code in global_map:
        inventory = storage.load_global_inventory(user_id)
        section_name = global_map[normalized_code]
        try:
            update_sticker_count(inventory, payload.sticker_id, payload.count)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        storage.save_global_inventory(user_id, inventory)
        return build_inventory_report(section_name, inventory, storage, user_id, target_section=section_name)

    ensure_country_exists(normalized_code)
    try:
        inventory = storage.load_country_inventory(user_id, normalized_code)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Inventory file not found for {normalized_code}")

    try:
        update_sticker_count(inventory, payload.sticker_id, payload.count)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    storage.save_country_inventory(user_id, normalized_code, inventory)
    return build_inventory_report(normalized_code, inventory, storage, user_id)


@app.patch("/inventory/{country_code}/parallel")
def update_parallel_inventory(
    country_code: str,
    payload: ParallelUpdate,
    storage: StorageProvider = Depends(get_storage),
    user_id: str = Depends(get_current_user),
) -> dict[str, Any]:
    normalized_code = normalize_country_code(country_code)
    ensure_country_exists(normalized_code)

    try:
        storage.update_parallel_count(user_id, normalized_code, payload.sticker_id, payload.parallel_type, payload.count)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    try:
        inventory = storage.load_country_inventory(user_id, normalized_code)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Inventory file not found for {normalized_code}")

    return build_inventory_report(normalized_code, inventory, storage, user_id)


@app.get("/reports", response_class=HTMLResponse)
def reports_page() -> HTMLResponse:
    reports_path = STATIC_DIR / "reports.html"
    if not reports_path.exists():
        raise HTTPException(status_code=500, detail="Reports page not found")
    return HTMLResponse(reports_path.read_text(encoding="utf-8"))


@app.get("/reports/duplicates")
def get_duplicates_report(
    storage: StorageProvider = Depends(get_storage),
    user_id: str = Depends(get_current_user),
) -> list[dict[str, Any]]:
    all_groups = list_groups()["groups"]
    country_names = load_country_names()
    global_inv = None
    try:
        global_inv = storage.load_global_inventory(user_id)
    except FileNotFoundError:
        pass

    results = []
    for group_name, codes in all_groups.items():
        entries = []
        for code in codes:
            if code in ["FWC", "CC"]:
                if global_inv:
                    report = build_inventory_report(code, global_inv, storage, user_id, target_section=code)
                    if report["duplicates"]:
                        sorted_dups = dict(sorted(report["duplicates"].items(), key=lambda x: natural_sort_key(x[0])))
                        entries.append({
                            "name": code,
                            "code": code,
                            "duplicates": sorted_dups
                        })
            else:
                try:
                    inv = storage.load_country_inventory(user_id, code)
                    report = build_inventory_report(code, inv, storage, user_id)
                    if report["duplicates"]:
                        sorted_dups = dict(sorted(report["duplicates"].items(), key=lambda x: natural_sort_key(x[0])))
                        entries.append({
                            "name": country_names.get(code, code),
                            "code": code,
                            "duplicates": sorted_dups
                        })
                except FileNotFoundError:
                    continue
        if entries:
            results.append({"group": group_name, "entries": entries})
    return results


@app.get("/reports/missing")
def get_missing_report(
    storage: StorageProvider = Depends(get_storage),
    user_id: str = Depends(get_current_user),
) -> list[dict[str, Any]]:
    all_groups = list_groups()["groups"]
    country_names = load_country_names()
    global_inv = None
    try:
        global_inv = storage.load_global_inventory(user_id)
    except FileNotFoundError:
        pass

    results = []
    for group_name, codes in all_groups.items():
        entries = []
        for code in codes:
            if code in ["FWC", "CC"]:
                if global_inv:
                    report = build_inventory_report(code, global_inv, storage, user_id, target_section=code)
                    if report["missing"]:
                        entries.append({
                            "name": code,
                            "code": code,
                            "missing": sorted(report["missing"], key=natural_sort_key)
                        })
            else:
                try:
                    inv = storage.load_country_inventory(user_id, code)
                    report = build_inventory_report(code, inv, storage, user_id)
                    if report["missing"]:
                        entries.append({
                            "name": country_names.get(code, code),
                            "code": code,
                            "missing": sorted(report["missing"], key=natural_sort_key)
                        })
                except FileNotFoundError:
                    continue
        if entries:
            results.append({"group": group_name, "entries": entries})
    return results


@app.get("/reports/parallels")
def get_parallels_report(
    storage: StorageProvider = Depends(get_storage),
    user_id: str = Depends(get_current_user),
) -> list[dict[str, Any]]:
    all_groups = list_groups()["groups"]
    country_names = load_country_names()
    results = []
    for group_name, codes in all_groups.items():
        entries = []
        for code in codes:
            if code in ["FWC", "CC"]:
                continue
            p_inv = storage.load_parallel_inventory(user_id, code)
            valid_p = {}
            for sid, types in p_inv.items():
                found_types = {t: c for t, c in types.items() if c > 0}
                if found_types:
                    valid_p[sid] = found_types
            if valid_p:
                sorted_p = dict(sorted(valid_p.items(), key=lambda x: natural_sort_key(x[0])))
                entries.append({
                    "name": country_names.get(code, code),
                    "code": code,
                    "parallels": sorted_p
                })
        if entries:
            results.append({"group": group_name, "entries": entries})
    return results


@app.get("/", response_class=HTMLResponse)
def root() -> HTMLResponse:
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=500, detail="Static UI not found")
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
