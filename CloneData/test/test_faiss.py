import torch
from transformers import AutoTokenizer, AutoModel
import faiss
import pandas as pd
import numpy as np
import os
import pickle
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Load PhoBERT
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_name = "vinai/phobert-large"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name).to(device)

base_path = r"E:\Code\Master\BDT\Test\CloneData"
faiss_has_accent_path = os.path.join(base_path, "faiss_has_accent.index")
faiss_no_accent_path = os.path.join(base_path, "faiss_no_accent.index")
faiss_ids_path = os.path.join(base_path, "faiss_ids.pkl")

# Kết nối MySQL bằng SQLAlchemy
engine = create_engine("mysql+pymysql://root:root@localhost/chatbot")
Session = sessionmaker(bind=engine)
session = Session()

# Chuyển văn bản thành vector sử dụng mean pooling
def get_vector(text):
    input_ids = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)["input_ids"].to(device)
    with torch.no_grad():
        outputs = model(input_ids)
        last_hidden_state = outputs.last_hidden_state
        # Mean pooling
        vector = last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
    return vector

# Tạo FAISS index từ danh sách ID và text
def build_faiss_index(data):
    vectors = []
    new_ids = []

    # Load index và id_map nếu đã tồn tại
    if os.path.exists(faiss_has_accent_path) and os.path.exists(faiss_ids_path):
        index = faiss.read_index(faiss_has_accent_path)
        with open(faiss_ids_path, 'rb') as f:
            id_map = pickle.load(f)
        start_index = index.ntotal
    else:
        index = None
        id_map = {}
        start_index = 0

    # Duyệt qua từng dòng và xử lý nếu ID chưa tồn tại
    for i, row in data.iterrows():
        text_id = row['id']
        text = row['text']
        if text_id in id_map:
            print(f"ID '{text_id}' đã tồn tại. Bỏ qua.")
            continue
        vec = get_vector(text)
        vectors.append(vec)
        new_ids.append(text_id)

    # Nếu không có vector mới thì kết thúc
    if not vectors:
        print("Không có vector mới để thêm.")
        return

    vectors_np = np.stack(vectors).astype('float32')

    # Nếu index chưa tồn tại, tạo mới
    if index is None:
        dim = vectors_np.shape[1]
        index = faiss.IndexFlatL2(dim)

    index.add(vectors_np)

    # Cập nhật id_map với các id mới
    for i, text_id in enumerate(new_ids):
        id_map[text_id] = start_index + i

    # Lưu lại
    faiss.write_index(index, faiss_has_accent_path)
    with open(faiss_ids_path, 'wb') as f:
        pickle.dump(id_map, f)

    print(f"Đã thêm {len(new_ids)} vector mới. Tổng số vector: {index.ntotal}")

# Truy xuất vector theo ID
def get_vector_by_id(text_id):
    index = faiss.read_index(faiss_has_accent_path)
    with open(faiss_ids_path, 'rb') as f:
        id_map = pickle.load(f)

    if text_id not in id_map:
        print("ID not found.")
        return None

    vector_index = id_map[text_id]
    return index.reconstruct(vector_index)

# Truy xuất ID gần nhất theo vector
def get_id_by_text(text):
    index = faiss.read_index(faiss_has_accent_path)
    with open(faiss_ids_path, 'rb') as f:
        id_map = pickle.load(f)
    rev_id_map = {v: k for k, v in id_map.items()}

    query_vec = get_vector(text).reshape(1, -1).astype('float32')
    distances, indices = index.search(query_vec, 1)
    nearest_index = indices[0][0]
    return rev_id_map.get(nearest_index), distances[0][0]

# ================================
# Ví dụ sử dụng:
# ================================

if __name__ == "__main__":
    result = session.execute(text("SELECT id, main_title, main_title_no_accent, content, content_no_accent FROM uet_clear WHERE vector = 0"))
    data = []
    list_data = []
    count = 0
    number_split = 100
    for row in result:
        id_clear, main_title, main_title_no_accent, content, content_no_accent = row
        data.append({
            'id': id_clear,
            'text': content
        })

        if len(data) == number_split:
            list_data.append(data)
            data = []

    # Thêm phần còn lại nếu có
    if data:
        list_data.append(data)

    for data_ in list_data:
        build_faiss_index(pd.DataFrame(data_))