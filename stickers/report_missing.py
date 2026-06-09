from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from inventory import (
    BASE_DIR,
    GLOBAL_INVENTORY_FILE,
    load_all_inventories,
    load_parallel_inventory,
    load_global_inventory,
    load_types,
    load_groups,
    get_types_by_scope,
    summarize_missing,
    summarize_duplicates,
    missing_items,
)


def format_summary(country_code: str, inventory: dict[str, Any], target_section: str | None = None) -> str:
    parallels = load_parallel_inventory(target_section if target_section else country_code)
    missing = summarize_missing(inventory, parallels)
    duplicates = summarize_duplicates(inventory, parallels)
    missing_map = missing_items(inventory, parallels)

    if target_section:
        missing = {target_section: missing.get(target_section, 0)}
        duplicates = {target_section: duplicates.get(target_section, 0)}
        missing_map = {target_section: missing_map.get(target_section, [])}

    total_missing = sum(missing.values())
    total_items = 0
    for k, v in inventory.items():
        if isinstance(v, dict) and k not in ("country", "inventory"):
            if target_section and k != target_section:
                continue
            total_items += len(v)
    
    completion = (1 - total_missing / total_items) * 100 if total_items > 0 else 0

    lines = [f"Summary for {country_code} ({completion:.1f}% complete):"]
    for sticker_type, count in missing.items():
        lines.append(f"  - {sticker_type}: {count} missing")
        if count > 0:
            lines.append(f"    {', '.join(missing_map[sticker_type])}")
        if duplicates.get(sticker_type, 0) > 0:
            lines.append(f"    ({duplicates[sticker_type]} duplicates found)")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Report missing Panini sticker inventory by country or overall."
    )
    parser.add_argument(
        "--country",
        help="Only show missing stickers for the given 3-letter country code.",
    )
    parser.add_argument(
        "--show-global",
        action="store_true",
        help="Show missing stickers for the shared global inventory (FWC and CC).",
    )
    parser.add_argument(
        "--inventory-dir",
        default=str(BASE_DIR / "country_inventory"),
        help="Directory where country inventory JSON files are stored.",
    )
    parser.add_argument(
        "--global-inventory",
        default=str(GLOBAL_INVENTORY_FILE),
        help="Path to the shared global inventory JSON file.",
    )
    args = parser.parse_args()

    inventories = load_all_inventories(Path(args.inventory_dir))
    if not inventories:
        print("No inventory files found. Run generate_inventory.py first.")
        return

    if args.country:
        code = args.country.upper()
        inventory = inventories.get(code)
        if inventory is None:
            print(f"No inventory found for {code}.")
            return
        print(format_summary(code, inventory))
        return

    if args.show_global:
        try:
            global_inventory = load_global_inventory(Path(args.global_inventory))
            global_types_config = get_types_by_scope(load_types(), "global")
        except FileNotFoundError:
            print(f"Global inventory not found at {args.global_inventory}. Run generate_inventory.py first.")
            return
        
        for section_name in ["FWC", "CC"]: # Explicit order for global types
            print(format_summary(section_name, global_inventory, target_section=section_name))
            print()
        return

    for country_code, inventory in sorted(inventories.items()):
        parallels = load_parallel_inventory(country_code)
        missing = summarize_missing(inventory, parallels)
        total_missing = sum(missing.values())
        total_items = sum(len(v) for k, v in inventory.items() if isinstance(v, dict) and k != "country")
        completion = (1 - total_missing / total_items) * 100 if total_items > 0 else 0
        
        duplicates = sum(summarize_duplicates(inventory, parallels).values())
        dup_str = f" [{duplicates} dups]" if duplicates > 0 else ""
        print(f"{country_code}: {total_missing} missing ({completion:.1f}%){dup_str}")

    # Custom order for countries based on World Cup groups
    ordered_country_codes = []
    wc_groups = load_groups()
    for group_letter in sorted(wc_groups.keys()):
        for country_code_in_group in wc_groups[group_letter]:
            if country_code_in_group in inventories:
                ordered_country_codes.append(country_code_in_group)

    print("\n--- Country Summaries (Ordered by World Cup Group) ---")
    for country_code in ordered_country_codes:
        inventory = inventories[country_code]
        parallels = load_parallel_inventory(country_code)
        missing = summarize_missing(inventory, parallels)
        total_missing = sum(missing.values())
        total_items = sum(len(v) for k, v in inventory.items() if isinstance(v, dict) and k != "country")
        completion = (1 - total_missing / total_items) * 100 if total_items > 0 else 0
        duplicates = sum(summarize_duplicates(inventory, parallels).values())
        dup_str = f" [{duplicates} dups]" if duplicates > 0 else ""
        print(f"{country_code}: {total_missing} missing ({completion:.1f}%){dup_str}")

    try:
        global_inventory = load_global_inventory(Path(args.global_inventory))
        global_types_config = get_types_by_scope(load_types(), "global")
        missing_all = summarize_missing(global_inventory)
        dups_all = summarize_duplicates(global_inventory)
        
        print("\n--- Global Sticker Summaries ---")
        for section_name in ["FWC", "CC"]: # Explicit order for global types
            m_count = missing_all.get(section_name, 0)
            d_count = dups_all.get(section_name, 0)
            total = len(global_inventory.get(section_name, {}))
            comp = (1 - m_count / total) * 100 if total > 0 else 0
            dup_str = f" [{d_count} dups]" if d_count > 0 else ""
            print(f"{section_name}: {m_count} missing ({comp:.1f}%){dup_str}")
    except FileNotFoundError:
        pass

    print("\nRun with --country CODE to see detailed missing stickers for a single country.")


if __name__ == "__main__":
    main()
