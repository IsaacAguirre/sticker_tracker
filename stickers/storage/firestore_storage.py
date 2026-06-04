from __future__ import annotations

from typing import Any, Dict
from firebase_auth import initialize_firebase_app
from firebase_admin import firestore
from inventory import build_country_inventory, build_global_inventory, load_types
from .base import StorageProvider


class FirestoreStorageProvider(StorageProvider):
    def __init__(self) -> None:
        initialize_firebase_app()
        self.db = firestore.client()

    def _user_root(self, user_id: str):
        return self.db.collection("users").document(user_id)

    def _country_docref(self, user_id: str, country_code: str):
        return self._user_root(user_id).collection("countries").document(country_code.upper())

    def _global_docref(self, user_id: str):
        return self._user_root(user_id).collection("global").document("inventory")

    def _parallel_docref(self, user_id: str, country_code: str):
        return self._user_root(user_id).collection("parallels").document(country_code.upper())

    def load_country_inventory(self, user_id: str, country_code: str) -> Dict[str, Any]:
        doc = self._country_docref(user_id, country_code).get()
        if doc.exists:
            return doc.to_dict() or {}

        inventory = build_country_inventory(country_code.upper(), load_types())
        self.save_country_inventory(user_id, country_code, inventory)
        return inventory

    def save_country_inventory(self, user_id: str, country_code: str, inventory: Dict[str, Any]) -> None:
        self._country_docref(user_id, country_code).set(inventory)

    def load_global_inventory(self, user_id: str) -> Dict[str, Any]:
        doc = self._global_docref(user_id).get()
        if doc.exists:
            return doc.to_dict() or {}

        inventory = build_global_inventory(load_types())
        self.save_global_inventory(user_id, inventory)
        return inventory

    def save_global_inventory(self, user_id: str, inventory: Dict[str, Any]) -> None:
        self._global_docref(user_id).set(inventory)

    def load_parallel_inventory(self, user_id: str, country_code: str) -> Dict[str, Dict[str, int]]:
        doc = self._parallel_docref(user_id, country_code).get()
        if not doc.exists:
            return {}
        return doc.to_dict() or {}

    def save_parallel_inventory(self, user_id: str, country_code: str, data: Dict[str, Dict[str, int]]) -> None:
        self._parallel_docref(user_id, country_code).set(data)

    def update_parallel_count(self, user_id: str, country_code: str, sticker_id: str, parallel_type: str, count: int) -> None:
        inventory = self.load_parallel_inventory(user_id, country_code)
        if sticker_id not in inventory:
            inventory[sticker_id] = {"blue": 0, "red": 0, "purple": 0, "green": 0, "gold": 0}
        inventory[sticker_id][parallel_type] = max(0, count)
        self.save_parallel_inventory(user_id, country_code, inventory)
