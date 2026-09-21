import os
import json
from abc import ABC, abstractmethod
from typing import Tuple, Dict

class StorageAdapter(ABC):
    @abstractmethod
    async def save(self, key: str, filename: str, content: bytes) -> None:
        pass

    @abstractmethod
    async def read(self, key: str) -> bytes:
        pass

    @abstractmethod
    async def get_metadata(self, key: str) -> Dict[str, str]:
        pass

    @abstractmethod
    async def set_status(self, key: str, status: str) -> None:
        pass

    @abstractmethod
    async def get_status(self, key: str) -> str:
        pass

    @abstractmethod
    async def save_analysis(self, key: str, analysis: Dict) -> None:
        pass

class LocalStorageAdapter(StorageAdapter):
    def __init__(self, base_path: str = "./data/storage"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    async def save(self, key: str, filename: str, content: bytes) -> None:
        """
        Save the binary content and metadata. Initialize status to 'submitted'
        if no status exists yet. This ensures the initial lifecycle status matches
        tests and expected behavior ('submitted').
        """
        filepath = os.path.join(self.base_path, key + ".bin")
        meta_path = os.path.join(self.base_path, key + ".meta")
        with open(filepath, "wb") as f:
            f.write(content)
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(filename)
        # initialize status file if not exists (use 'submitted' per contract)
        status_path = os.path.join(self.base_path, key + ".status")
        if not os.path.exists(status_path):
            with open(status_path, "w", encoding="utf-8") as f:
                f.write("submitted")

    async def read(self, key: str) -> bytes:
        filepath = os.path.join(self.base_path, key + ".bin")
        if not os.path.exists(filepath):
            raise FileNotFoundError("Key not found")
        with open(filepath, "rb") as f:
            return f.read()

    async def get_metadata(self, key: str) -> Dict[str, str]:
        meta_path = os.path.join(self.base_path, key + ".meta")
        filepath = os.path.join(self.base_path, key + ".bin")
        if not os.path.exists(filepath) or not os.path.exists(meta_path):
            raise FileNotFoundError("Metadata not found")
        with open(meta_path, "r", encoding="utf-8") as f:
            filename = f.read()
        return {"filename": filename}

    async def set_status(self, key: str, status: str) -> None:
        status_path = os.path.join(self.base_path, key + ".status")
        # ensure resume exists
        bin_path = os.path.join(self.base_path, key + ".bin")
        if not os.path.exists(bin_path):
            raise FileNotFoundError("Key not found")
        # normalize status before writing
        normalized = (status or "").strip()
        # defensive normalization of legacy tokens
        if normalized.lower() == "received":
            normalized = "submitted"
        # write canonical lower-case token
        if normalized:
            normalized = normalized.lower()
        else:
            # avoid writing empty status
            normalized = "submitted"
        with open(status_path, "w", encoding="utf-8") as f:
            f.write(normalized)

    async def get_status(self, key: str) -> str:
        status_path = os.path.join(self.base_path, key + ".status")
        bin_path = os.path.join(self.base_path, key + ".bin")
        if not os.path.exists(bin_path) or not os.path.exists(status_path):
            raise FileNotFoundError("Status not found")
        with open(status_path, "r", encoding="utf-8") as f:
            raw = f.read()
        if raw is None:
            raise FileNotFoundError("Status not found")
        value = (raw or "").strip()
        if not value:
            raise FileNotFoundError("Status not found")
        # Backwards-compatibility/migration fix: older runs may have used 'received'.
        # Map legacy 'received' to the expected initial state 'submitted'.
        if value.lower() == "received":
            return "submitted"
        # return canonical lower-case status token
        return value.lower()

    async def save_analysis(self, key: str, analysis: Dict) -> None:
        analysis_path = os.path.join(self.base_path, key + ".analysis.json")
        bin_path = os.path.join(self.base_path, key + ".bin")
        if not os.path.exists(bin_path):
            raise FileNotFoundError("Key not found")
        with open(analysis_path, "w", encoding="utf-8") as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
