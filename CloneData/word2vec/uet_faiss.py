import faiss  # FAISS chạy trên CPU
import pickle
import torch
from transformers import BertModel, BertTokenizer
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import numpy as np

# Kết nối MySQL bằng SQLAlchemy
def connect_db():
    engine = create_engine("mysql+pymysql://root:root@localhost/chatbot")
    return engine

# Load BERT model và tokenizer, đảm bảo Torch chạy trên GPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tokenizer = BertTokenizer.from_pretrained("bert-base-multilingual-uncased")
model = BertModel.from_pretrained("bert-base-multilingual-uncased").to(device)

# Hàm mã hóa văn bản thành vector
def encode_text(text):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512).to(device)  # Chạy trên GPU
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state[:, 0, :].cpu().numpy().astype(np.float32)  # Chuyển về CPU & float32

# Kết nối DB
engine = connect_db()
Session = sessionmaker(bind=engine)
session = Session()

# FAISS chạy trên CPU
embedding_dim = 768
index_has_accent = faiss.IndexFlatL2(embedding_dim)
index_no_accent = faiss.IndexFlatL2(embedding_dim)
id_list = []

# Lấy dữ liệu từ uet_clear
result = session.execute(text("SELECT id, main_title, main_title_no_accent, content, content_no_accent FROM uet_clear WHERE vector = 0"))

total = result.rowcount
count = 0

for row in result:
    id_clear, main_title, main_title_no_accent, content, content_no_accent = row
    text_has_accent = f"{main_title} {content}" if main_title else content
    text_no_accent = f"{main_title_no_accent} {content_no_accent}" if main_title_no_accent else content_no_accent
    
    # Mã hóa thành vector trên GPU, rồi chuyển về CPU trước khi dùng FAISS
    vector_has_accent = encode_text(text_has_accent)  # Torch chạy trên GPU, output về CPU
    vector_no_accent = encode_text(text_no_accent)

    # Thêm vào FAISS (chạy trên CPU)
    index_has_accent.add(vector_has_accent)
    index_no_accent.add(vector_no_accent)
    id_list.append(id_clear)
    
    # Cập nhật trạng thái đã mã hóa trong DB
    session.execute(text("UPDATE uet_clear SET vector = 1 WHERE id = :id_clear"), {"id_clear": id_clear})
    session.commit()
    count += 1
    print(f"✅ Đã xử lý {count}/{total} dòng")

# Lưu FAISS index và danh sách ID
faiss.write_index(index_has_accent, "faiss_has_accent.index")
faiss.write_index(index_no_accent, "faiss_no_accent.index")
with open("faiss_ids.pkl", "wb") as f:
    pickle.dump(id_list, f)

print("✅ Hoàn tất mã hóa và lưu FAISS index!")
session.close()
