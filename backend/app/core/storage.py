import os
import json
from typing import Any
from fastapi import UploadFile
import asyncio

# Try to import aiofiles for async file IO; if unavailable, fall back to sync IO
try:
    import aiofiles  # type: ignore
    _HAS_AIOFILES = True
except Exception:
    _HAS_AIOFILES = False


class StorageManager:
    """Pluggable storage manager. Default: local filesystem for dev.
    If aiofiles is available it will use async file IO. Otherwise it falls back to
    synchronous IO run in a thread to preserve async function signatures so tests
    and application imports do not fail when aiofiles is not installed.

    Secrets and production S3 adapters should be provided via environment or
    Foundry secret store; do not store secrets in repository.
    """

    def __init__(self, base_path: str = "data"):
        self.base_path = base_path

    async def initialize(self):
        # ensure base path exists
        loop = asyncio.get_running_loop()
        if _HAS_AIOFILES:
            os.makedirs(self.base_path, exist_ok=True)
        else:
            # run sync os.makedirs in thread
            await loop.run_in_executor(None, lambda: os.makedirs(self.base_path, exist_ok=True))

    async def save_file(self, upload_file: UploadFile, filename: str) -> str:
        path = os.path.join(self.base_path, filename)

        if _HAS_AIOFILES:
            # Use aiofiles to write binary content
            content = await upload_file.read()
            async with aiofiles.open(path, "wb") as out_file:  # type: ignore
                await out_file.write(content)
            return path
        else:
            # Fallback: read async then run sync write in thread
            content = await upload_file.read()

            def _write():
                with open(path, "wb") as f:
                    f.write(content)

            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, _write)
            return path

    async def save_json(self, filename: str, data: Any):
        path = os.path.join(self.base_path, filename)
        json_text = json.dumps(data, ensure_ascii=False, indent=2)

        if _HAS_AIOFILES:
            async with aiofiles.open(path, "w", encoding="utf-8") as f:  # type: ignore
                await f.write(json_text)
            return path
        else:
            def _write():
                with open(path, "w", encoding="utf-8") as f:
                    f.write(json_text)

            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, _write)
            return path

    async def load_json(self, filename: str) -> Any:
        path = os.path.join(self.base_path, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(filename)

        if _HAS_AIOFILES:
            async with aiofiles.open(path, "r", encoding="utf-8") as f:  # type: ignore
                content = await f.read()
                return json.loads(content)
        else:
            def _read():
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()

            loop = asyncio.get_running_loop()
            content = await loop.run_in_executor(None, _read)
            return json.loads(content)
