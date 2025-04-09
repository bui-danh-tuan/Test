import os
import faiss
import pickle
import torch
from transformers import AutoTokenizer, AutoModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import numpy as np

# Đường dẫn tới các file
base_path = r"E:\Code\Master\BDT\Test\CloneData"
faiss_has_accent_path = os.path.join(base_path, "faiss_has_accent.index")
faiss_no_accent_path = os.path.join(base_path, "faiss_no_accent.index")
faiss_ids_path = os.path.join(base_path, "faiss_ids.pkl")
modelName = "bert-base-multilingual-cased"
# modelName = "vinai/phobert-large"

# Kết nối MySQL bằng SQLAlchemy
def connect_db():
    engine = create_engine("mysql+pymysql://root:root@localhost/chatbot")
    return engine

# Load BERT model và tokenizer
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tokenizer = AutoTokenizer.from_pretrained(modelName)
model = AutoModel.from_pretrained(modelName).to(device)

# Hàm mã hóa văn bản thành vector
def encode_text(text):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512).to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state[:, 0, :].cpu().numpy().astype(np.float32)

# Kết nối DB
engine = connect_db()
Session = sessionmaker(bind=engine)
session = Session()

# FAISS index
embedding_dim = 768

# Load FAISS index nếu có, nếu không tạo mới
if os.path.exists(faiss_has_accent_path):
    index_has_accent = faiss.read_index(faiss_has_accent_path)
    print(f"📂 Đã load faiss_has_accent.index với {index_has_accent.ntotal} vector")
else:
    index_has_accent = faiss.IndexFlatL2(embedding_dim)
    print("📁 Tạo mới faiss_has_accent.index")

if os.path.exists(faiss_no_accent_path):
    index_no_accent = faiss.read_index(faiss_no_accent_path)
    print(f"📂 Đã load faiss_no_accent.index với {index_no_accent.ntotal} vector")
else:
    index_no_accent = faiss.IndexFlatL2(embedding_dim)
    print("📁 Tạo mới faiss_no_accent.index")

# Load danh sách ID đã lưu nếu có
if os.path.exists(faiss_ids_path):
    with open(faiss_ids_path, "rb") as f:
        id_list = pickle.load(f)
    print(f"📂 Đã load faiss_ids.pkl với {len(id_list)} ID")
else:
    id_list = []

# Lấy dữ liệu chưa vector hóa
result = session.execute(text("SELECT id, main_title, main_title_no_accent, content, content_no_accent FROM uet_clear WHERE vector = 0"))
total = result.rowcount
count = 0

for row in result:
    id_clear, main_title, main_title_no_accent, content, content_no_accent = row
    text_has_accent = f"{main_title} {content}" if main_title else content
    text_no_accent = f"{main_title_no_accent} {content_no_accent}" if main_title_no_accent else content_no_accent

    before_ha = index_has_accent.ntotal
    before_na = index_no_accent.ntotal

    vector_has_accent = encode_text(text_has_accent)
    vector_no_accent = encode_text(text_no_accent)
    index_has_accent.add(vector_has_accent)
    index_no_accent.add(vector_no_accent)

    after_ha = index_has_accent.ntotal
    after_na = index_no_accent.ntotal

    id_list.append(id_clear)
    session.execute(text("UPDATE uet_clear SET vector = 1 WHERE id = :id_clear"), {"id_clear": id_clear})
    session.commit()


    count += 1
    if count % 5000 == 0:
        # Lưu ngay sau mỗi lần thêm vector
        faiss.write_index(index_has_accent, faiss_has_accent_path)
        faiss.write_index(index_no_accent, faiss_no_accent_path)
        with open(faiss_ids_path, "wb") as f:
            pickle.dump(id_list, f)
        print(f"✅ {count}/{total} - ID {id_clear} | +1 vector (HA: {before_ha} → {after_ha}, NA: {before_na} → {after_na})")


faiss.write_index(index_has_accent, faiss_has_accent_path)
faiss.write_index(index_no_accent, faiss_no_accent_path)
with open(faiss_ids_path, "wb") as f:
    pickle.dump(id_list, f)

print("✅ Hoàn tất cập nhật và lưu FAISS index! Tổng vector hiện tại:")
print(f"   - Có dấu: {index_has_accent.ntotal}")
print(f"   - Không dấu: {index_no_accent.ntotal}")
session.close()
