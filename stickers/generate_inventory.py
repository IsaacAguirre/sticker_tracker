from __future__ import annotations

import argparse
from pathlib import Path

from inventory import (
    BASE_DIR,
    build_country_inventory,
    build_global_inventory,
    load_countries,
    load_types,
    save_json,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create one country inventory JSON file for each sticker country code."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate all inventory files even if they already exist.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(BASE_DIR / "country_inventory"),
        help="Directory to write country inventory files.",
    )
    args = parser.parse_args()

    country_codes = load_countries()
    types = load_types()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for code in country_codes:
        file_path = output_dir / f"{code}.json"
        if file_path.exists() and not args.force:
            print(f"Skipping existing {file_path.name}")
            continue

        inventory = build_country_inventory(code, types=types)
        save_json(file_path, inventory)
        print(f"Created {file_path.name}")

    global_inventory = build_global_inventory(types=types)
    global_file = output_dir / "global_inventory.json"
    save_json(global_file, global_inventory)
    print(f"Created {global_file.name}")

    print("Inventory generation complete.")


if __name__ == "__main__":
    main()
