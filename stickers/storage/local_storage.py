from __future__ import annotations

from typing import Any, Dict
from .base import StorageProvider
from inventory import (
    GLOBAL_INVENTORY_FILE,
    load_country_inventory_by_code,
    load_global_inventory,
    load_parallel_inventory,
    save_country_inventory,
    save_global_inventory,
    save_parallel_inventory,
    update_parallel_count,
)


class LocalStorageProvider(StorageProvider):
    def load_country_inventory(self, user_id: str, country_code: str) -> Dict[str, Any]:
        return load_country_inventory_by_code(country_code)

    def save_country_inventory(self, user_id: str, country_code: str, inventory: Dict[str, Any]) -> None:
        save_country_inventory(country_code, inventory)

    def load_global_inventory(self, user_id: str) -> Dict[str, Any]:
        return load_global_inventory(GLOBAL_INVENTORY_FILE)

    def save_global_inventory(self, user_id: str, inventory: Dict[str, Any]) -> None:
        save_global_inventory(inventory)

    def load_parallel_inventory(self, user_id: str, country_code: str) -> Dict[str, Dict[str, int]]:
        return load_parallel_inventory(country_code)

    def save_parallel_inventory(self, user_id: str, country_code: str, data: Dict[str, Dict[str, int]]) -> None:
        save_parallel_inventory(country_code, data)

    def update_parallel_count(self, user_id: str, country_code: str, sticker_id: str, parallel_type: str, count: int) -> None:
        update_parallel_count(country_code, sticker_id, parallel_type, count)
