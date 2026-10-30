import os
import shutil
import hashlib
from typing import Tuple, Optional
from app.core.config import settings


class StorageService:
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = os.path.abspath(base_dir or settings.STORAGE_DIR)
        os.makedirs(self.base_dir, exist_ok=True)

    def save_file(self, filename: str, content: bytes) -> Tuple[str, str, int]:
        """
        Saves a binary file to persistent storage.
        Returns: (file_path, sha256_hash, file_size)
        """
        sha256 = hashlib.sha256(content).hexdigest()
        ext = os.path.splitext(filename)[1] or ".pdf"
        storage_filename = f"{sha256}{ext}"
        target_path = os.path.join(self.base_dir, storage_filename)

        with open(target_path, "wb") as f:
            f.write(content)

        file_size = len(content)
        return target_path, sha256, file_size

    def get_file_bytes(self, file_path: str) -> Optional[bytes]:
        """Reads file bytes from storage."""
        if not os.path.exists(file_path):
            return None
        with open(file_path, "rb") as f:
            return f.read()

    def delete_file(self, file_path: str) -> bool:
        """Deletes file from storage."""
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True
            except OSError:
                return False
        return False


storage_service = StorageService()
