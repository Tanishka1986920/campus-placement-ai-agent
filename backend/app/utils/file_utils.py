import os
import shutil
import aiofiles
from fastapi import UploadFile
from app.core.config import settings

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "txt"}

def allowed_file_type(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS

async def save_upload_file_tmp(upload_file: UploadFile) -> str:
    # Save to configured tmp dir with a unique name
    basename = os.path.basename(upload_file.filename or "upload")
    safe_name = f"upload_{os.urandom(8).hex()}_{basename}"
    tmp_path = os.path.join(settings.tmp_dir, safe_name)
    # Ensure dir exists
    os.makedirs(settings.tmp_dir, exist_ok=True)
    async with aiofiles.open(tmp_path, "wb") as out_file:
        content = await upload_file.read()
        await out_file.write(content)
    await upload_file.close()
    return tmp_path
