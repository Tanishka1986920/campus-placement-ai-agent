import os
from typing import List

class Settings:
    def __init__(self):
        raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
        # ALLOWED_ORIGINS can be a comma-separated list
        self.allowed_origins = [o.strip() for o in raw.split(",") if o.strip()]
        self.tmp_dir = os.getenv("TMP_DIR", "/tmp")

settings = Settings()
