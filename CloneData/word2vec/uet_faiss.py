from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from bs4 import BeautifulSoup
import re
import unicodedata
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Kết nối MySQL bằng SQLAlchemy
def connect_db():
    engine = create_engine("mysql+pymysql://root:root@localhost/chatbot")
    return engine

# Làm sạch HTML
def clean_html(raw_html):
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text()
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Loại bỏ dấu tiếng Việt
def remove_accents(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

# Chuẩn hóa văn bản tiếng Việt
def normalize_text(text):
    text = text.lower()
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()

# Trích xuất dữ liệu từ MySQL
def fetch_paragraphs():
    engine = connect_db()
    Session = sessionmaker(bind=engine)
    session = Session()
    result = session.execute(text("SELECT id, paragraph FROM uet_content"))

    data = []
    for row in result:
        clean_text = clean_html(row[1])
        normalized_text = normalize_text(clean_text)
        no_accent_text = remove_accents(normalized_text)  # Phiên bản không dấu
        data.append((row[0], normalized_text, no_accent_text))

    session.close()
    return data

# Khởi tạo mô hình SBERT
model = SentenceTransformer('bert-base-nli-mean-tokens')

# Chuyển văn bản thành embedding
def get_embedding(text):
    return model.encode(text)

# Lưu embeddings vào FAISS
def save_to_faiss(data):
    embeddings = np.array([get_embedding(text) for _, text, _ in data])
    index = faiss.IndexFlatL2(768)
    index.add(embeddings)
    faiss.write_index(index, "uet_vector.index")

# Tìm kiếm trong FAISS và hiển thị nội dung văn bản
def search(query, data, top_k=5):
    index = faiss.read_index("uet_vector.index")
    query_normalized = normalize_text(query)
    query_vector = get_embedding(query_normalized).reshape(1, -1)
    distances, indices = index.search(query_vector, top_k)

    results = []
    for idx in indices[0]:  # indices[0] chứa danh sách index
        results.append(data[idx])  # Lấy đoạn văn bản theo index

    return results

if __name__ == "__main__":
    data = fetch_paragraphs()
    save_to_faiss(data)
    print("Dữ liệu đã được làm sạch và lưu vào FAISS.")

    # Test tìm kiếm
    query = "Thời gian đăng ký môn học?"
    results = search(query, data)

    print("\n🔎 Kết quả tìm kiếm:")
    for r in results:
        print(f"📌 ID: {r[0]} - Nội dung: {r[1]}")
