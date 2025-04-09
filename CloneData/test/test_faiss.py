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
tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-large")
model = AutoModel.from_pretrained("vinai/phobert-large").to(device)

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
def build_faiss_index(data, index_path='index.faiss', id_map_path='id_map.pkl'):
    vectors = []
    new_ids = []

    # Load index và id_map nếu đã tồn tại
    if os.path.exists(index_path) and os.path.exists(id_map_path):
        index = faiss.read_index(index_path)
        with open(id_map_path, 'rb') as f:
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
    faiss.write_index(index, index_path)
    with open(id_map_path, 'wb') as f:
        pickle.dump(id_map, f)

    print(f"Đã thêm {len(new_ids)} vector mới. Tổng số vector: {index.ntotal}")

# Truy xuất vector theo ID
def get_vector_by_id(text_id, index_path='index.faiss', id_map_path='id_map.pkl'):
    index = faiss.read_index(index_path)
    with open(id_map_path, 'rb') as f:
        id_map = pickle.load(f)

    if text_id not in id_map:
        print("ID not found.")
        return None

    vector_index = id_map[text_id]
    return index.reconstruct(vector_index)

# Truy xuất ID gần nhất theo vector
def get_id_by_text(text, index_path='index.faiss', id_map_path='id_map.pkl'):
    index = faiss.read_index(index_path)
    with open(id_map_path, 'rb') as f:
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

    # Bước 2: Truy xuất vector theo ID
    # vector = get_vector_by_id("2")
    # print("Vector for ID 2:", vector[:5], "...")  # In 5 giá trị đầu tiên

    # Bước 3: Truy xuất ID gần nhất theo câu truy vấn
    test_text = "ữa vì thế các em nên tiếp tục nâng cao và trau dồi ngoại ngữ là những chuyên gia công nghệ nên có thái độ mở và lấy mục tiêu học tập suốt đời để trở thành những người d"
    matched_id, distance = get_id_by_text(test_text)
    print(f"Closest ID to query: {matched_id}, distance: {distance:.4f}")