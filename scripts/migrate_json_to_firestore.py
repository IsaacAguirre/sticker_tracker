from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from stickers.inventory import (
    BASE_DIR,
    GLOBAL_INVENTORY_FILE,
    PARALLEL_INVENTORY_DIR,
    load_json,
)
from stickers.storage.firestore_storage import FirestoreStorageProvider


def load_json_file(path: Path) -> Any:
    try:
        return load_json(path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Source file not found: {path}")


def get_country_files(inventory_dir: Path) -> list[Path]:
    return sorted(
        [path for path in inventory_dir.glob("*.json") if path.name != "global_inventory.json"]
    )


def get_parallel_files(parallel_dir: Path) -> list[Path]:
    return sorted(parallel_dir.glob("*.json"))


def migrate_country_inventory(
    storage: FirestoreStorageProvider,
    user_id: str,
    inventory_dir: Path,
    dry_run: bool,
) -> int:
    country_files = get_country_files(inventory_dir)
    if not country_files:
        print("No country JSON inventory files found to migrate.")
        return 0

    migrated = 0
    for path in country_files:
        country_code = path.stem.upper()
        inventory = load_json_file(path)
        if dry_run:
            print(f"[DRY RUN] Would migrate country {country_code} from {path}")
        else:
            storage.save_country_inventory(user_id, country_code, inventory)
            print(f"Migrated country {country_code} from {path}")
        migrated += 1

    return migrated


def migrate_global_inventory(
    storage: FirestoreStorageProvider,
    user_id: str,
    global_path: Path,
    dry_run: bool,
) -> bool:
    global_inventory = load_json_file(global_path)
    if dry_run:
        print(f"[DRY RUN] Would migrate global inventory from {global_path}")
        return True

    storage.save_global_inventory(user_id, global_inventory)
    print(f"Migrated global inventory from {global_path}")
    return True


def migrate_parallel_inventory(
    storage: FirestoreStorageProvider,
    user_id: str,
    parallel_dir: Path,
    dry_run: bool,
) -> int:
    parallel_files = get_parallel_files(parallel_dir)
    if not parallel_files:
        print("No parallel inventory JSON files found to migrate.")
        return 0

    migrated = 0
    for path in parallel_files:
        country_code = path.stem.upper()
        inventory = load_json_file(path)
        if dry_run:
            print(f"[DRY RUN] Would migrate parallels for {country_code} from {path}")
        else:
            storage.save_parallel_inventory(user_id, country_code, inventory)
            print(f"Migrated parallels for {country_code} from {path}")
        migrated += 1

    return migrated


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migrate local sticker inventory JSON files to Firestore for a single user."
    )
    parser.add_argument(
        "--user-id",
        required=True,
        help="Firebase user UID to associate with migrated inventory.",
    )
    parser.add_argument(
        "--inventory-dir",
        default=str(BASE_DIR / "country_inventory"),
        help="Local directory containing country inventory JSON files.",
    )
    parser.add_argument(
        "--parallel-dir",
        default=str(PARALLEL_INVENTORY_DIR),
        help="Local directory containing parallel inventory JSON files.",
    )
    parser.add_argument(
        "--global-inventory",
        default=str(GLOBAL_INVENTORY_FILE),
        help="Local global inventory JSON file path.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without writing to Firestore.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    inventory_dir = Path(args.inventory_dir)
    parallel_dir = Path(args.parallel_dir)
    global_inventory_path = Path(args.global_inventory)

    print("Starting Firestore migration")
    print(f"  user_id: {args.user_id}")
    print(f"  inventory_dir: {inventory_dir}")
    print(f"  parallel_dir: {parallel_dir}")
    print(f"  global_inventory: {global_inventory_path}")
    print(f"  dry_run: {args.dry_run}")

    storage = FirestoreStorageProvider()

    countries_migrated = migrate_country_inventory(
        storage, args.user_id, inventory_dir, args.dry_run
    )
    global_migrated = migrate_global_inventory(
        storage, args.user_id, global_inventory_path, args.dry_run
    )
    parallels_migrated = migrate_parallel_inventory(
        storage, args.user_id, parallel_dir, args.dry_run
    )

    print("\nMigration summary:")
    print(f"  country inventories migrated: {countries_migrated}")
    print(f"  global inventory migrated: {'yes' if global_migrated else 'no'}")
    print(f"  parallel inventories migrated: {parallels_migrated}")
    print("Migration complete.")


if __name__ == "__main__":
    main()
