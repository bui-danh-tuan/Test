import faiss
import pickle
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sentence_transformers import SentenceTransformer
import numpy as np

# Đường dẫn
faiss_index_path = r"E:\Code\Master\BDT\Test\CloneData\faiss_has_accent.index"
faiss_ids_path = r"E:\Code\Master\BDT\Test\CloneData\faiss_ids.pkl"

# Load SentenceTransformer model (giống model đã dùng để tạo index)
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# DB connection
def connect_db():
    engine = create_engine("mysql+pymysql://root:root@localhost/chatbot")
    return engine

def search_by_text(input_text):
    # Chuyển văn bản thành vector
    vec = model.encode([input_text])
    
    # Load FAISS index
    index = faiss.read_index(faiss_index_path)

    # Load danh sách ID
    with open(faiss_ids_path, "rb") as f:
        id_list = pickle.load(f)

    # Tìm top 5 vector gần nhất
    D, I = index.search(np.array(vec), k=5)

    # Kết nối DB
    engine = connect_db()
    Session = sessionmaker(bind=engine)
    session = Session()

    print(f"\n🔍 Top 5 kết quả gần nhất với chuỗi: \"{input_text}\"")
    for rank, idx in enumerate(I[0]):
        id_matched = id_list[idx]
        distance = D[0][rank]

        result = session.execute(text(
            "SELECT main_title, content FROM uet_clear WHERE id = :id"
        ), {"id": id_matched}).fetchone()

        print(f"\n#{rank+1}: ID {id_matched} (index {idx}) | Distance: {distance:.4f}")
        if result:
            title, content = result
            print(f"- Tiêu đề: {title}")
            print(f"- Nội dung: {content[:200]}...")
        else:
            print("⚠️ Không tìm thấy trong DB")

    session.close()

# Ví dụ sử dụng
search_by_text("chương trình đào tạo ngành công nghệ kỹ thuật điện tử truyền thông chương trình chuẩn quốc tế trường đại học công nghệ đhqghn univeristy of engineering and technology")
