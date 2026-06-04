from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

class StorageProvider(ABC):
    @abstractmethod
    def load_country_inventory(self, user_id: str, country_code: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def save_country_inventory(self, user_id: str, country_code: str, inventory: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def load_global_inventory(self, user_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def save_global_inventory(self, user_id: str, inventory: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def load_parallel_inventory(self, user_id: str, country_code: str) -> Dict[str, Dict[str, int]]:
        pass

    @abstractmethod
    def save_parallel_inventory(self, user_id: str, country_code: str, data: Dict[str, Dict[str, int]]) -> None:
        pass

    @abstractmethod
    def update_parallel_count(self, user_id: str, country_code: str, sticker_id: str, parallel_type: str, count: int) -> None:
        pass
