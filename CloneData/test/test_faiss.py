import os
import torch
import pickle
import faiss
import numpy as np
from transformers import AutoTokenizer, AutoModel

def save_text_vector_to_faiss(
    text, id,
    index_path="E:/Code/Master/BDT/Test/CloneData/faiss_has_accent.index",
    id_path="E:/Code/Master/BDT/Test/CloneData/faiss_ids.pkl"
):
    # Khởi tạo PhoBERT
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-large")
    model = AutoModel.from_pretrained("vinai/phobert-large").to(device)
    model.eval()

    # Tokenize văn bản với max_length và truncation
    inputs = tokenizer(
        text,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=256  # bạn có thể điều chỉnh giới hạn này
    ).to(device)

    with torch.no_grad():
        outputs = model(**inputs)

    # Trích xuất vector CLS
    cls_vector = outputs.last_hidden_state[:, 0, :].detach().cpu().numpy()

    # Đảm bảo vector có shape (1, 768)
    if cls_vector.ndim == 1:
        cls_vector = cls_vector.reshape(1, -1)

    # Load hoặc khởi tạo FAISS index
    if os.path.exists(index_path):
        index = faiss.read_index(index_path)
    else:
        index = faiss.IndexFlatL2(768)  # PhoBERT-large => 768 chiều

    # Load hoặc khởi tạo danh sách ID
    if os.path.exists(id_path):
        with open(id_path, "rb") as f:
            id_list = pickle.load(f)
    else:
        id_list = []

    # Thêm vector và ID
    index.add(cls_vector.astype("float32"))
    id_list.append(id)

    # Lưu lại index và ID
    faiss.write_index(index, index_path)
    with open(id_path, "wb") as f:
        pickle.dump(id_list, f)

    print(f"✅ Vector cho ID '{id}' đã được lưu vào FAISS.")

# ==========================
# ✅ Ví dụ sử dụng:
# ==========================
if __name__ == "__main__":
    save_text_vector_to_faiss("Trường Đại học Công nghệ - ĐHQGHN", "uet001")
    save_text_vector_to_faiss("Khoa Công nghệ thông tin - UET", "uet002")
    save_text_vector_to_faiss("Chương trình đào tạo kỹ sư tài năng", "uet003")
