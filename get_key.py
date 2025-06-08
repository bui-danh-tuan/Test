from pathlib import Path
from typing import Optional
import os

def get_env(key: str, default: Optional[str] = None, *, required: bool = False) -> Optional[str]:

    from dotenv import load_dotenv

    ENV_PATH: Path = Path(r"E:\Code\Master\BDT\Test\key.env")

    load_dotenv(dotenv_path=ENV_PATH, override=False)
    value = os.getenv(key, default)
    
    if required and (value is None or value == ""):
        raise RuntimeError(f"Biến môi trường '{key}' không tồn tại hoặc rỗng.")
    
    return value
