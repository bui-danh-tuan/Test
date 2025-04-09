from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import re
import unicodedata
from datetime import datetime

# Kết nối MySQL bằng SQLAlchemy
def connect_db():
    engine = create_engine("mysql+pymysql://root:root@localhost/chatbot")
    return engine

# Chuẩn hóa văn bản tiếng Việt
def normalize_text(text):
    text = text.lower()
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r'[^\w\s]', '', text)  # Loại bỏ ký tự đặc biệt
    return text.strip()

# Loại bỏ dấu tiếng Việt
def remove_accents(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

# Thay thế từ viết tắt
abbreviations = {
    "sv": "sinh viên",
    "đh": "đại học",
    "ktx": "ký túc xá",
    "pđk": "phòng đăng ký"
}

def expand_abbreviations(text):
    words = text.split()
    words = [abbreviations.get(word, word) for word in words]
    return " ".join(words)

# Xử lý toàn bộ pipeline
def preprocess_text(text, max_length=30):
    text = normalize_text(text)  # Bước 1: Chuẩn hóa
    text = expand_abbreviations(text)  # Bước 2: Xử lý viết tắt
    text = ' '.join([t for t in text.split() if len(t) < max_length]) # Bước 3: Loại bỏ các từ quá dài
    return text, remove_accents(text)  # Bước 4: Tạo phiên bản không dấu

# Trích xuất dữ liệu từ bảng uet_chunking và lưu vào uet_clear
def process_and_store_data():
    engine = connect_db()
    Session = sessionmaker(bind=engine)
    session = Session()
    
    result = session.execute(text("SELECT id, main_title, sub_title, content FROM uet_chunking WHERE clear = 0")).fetchall()

    len_result = len(result)
    count = 0
    
    for row in result:
        id_chunking, main_title, sub_title, content = row
        
        # Làm sạch dữ liệu (chỉ xử lý nếu không rỗng)
        main_title, main_title_no_accent = preprocess_text(main_title) if main_title else (None, None)
        sub_title, sub_title_no_accent = preprocess_text(sub_title) if sub_title else (None, None)
        content, content_no_accent = preprocess_text(content) if content else (None, None)
        
        session.execute(
            text("""
                INSERT INTO uet_clear (id_chunking, main_title, main_title_no_accent, sub_title, sub_title_no_accent, content, content_no_accent, last_modified)
                VALUES (:id_chunking, :main_title, :main_title_no_accent, :sub_title, :sub_title_no_accent, :content, :content_no_accent, :last_modified)
            """),
            {
                "id_chunking": id_chunking,
                "main_title": main_title,
                "main_title_no_accent": main_title_no_accent,
                "sub_title": sub_title,
                "sub_title_no_accent": sub_title_no_accent,
                "content": content,
                "content_no_accent": content_no_accent,
                "last_modified": datetime.utcnow()
            }
        )
        
        # Cập nhật trạng thái đã làm sạch trong uet_chunking
        session.execute(text("UPDATE uet_chunking SET clear = 1 WHERE id = :id_chunking"), {"id_chunking": id_chunking})
        session.commit()
        count += 1
        print(f"{len_result - count}")
    
    session.close()
    print("✅ Dữ liệu đã được xử lý và lưu vào bảng uet_clear!")

if __name__ == "__main__":
    process_and_store_data()
