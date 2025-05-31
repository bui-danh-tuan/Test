from pathlib import Path
import os

# Thư mục mặc định chứa mô hình Hugging Face đã tải
cache_dir = Path.home() / ".cache" / "huggingface" / "transformers"

# Duyệt thư mục và liệt kê tên mô hình (folder chứa checkpoint)
def list_downloaded_models(cache_dir):
    models = set()
    for path in cache_dir.glob("**/model.safetensors"):
        model_dir = path.parent
        models.add(str(model_dir))
    return sorted(models)

models = list_downloaded_models(cache_dir)
print("Các mô hình đã tải về:")
for m in models:
    print("-", m)
