from sqlalchemy import create_engine, text
from bs4 import BeautifulSoup
from datetime import datetime
import re

# Kết nối database bằng SQLAlchemy
username = "root"
password = "root"
host = "localhost"
database = "chatbot"
engine = create_engine(f"mysql+pymysql://{username}:{password}@{host}/{database}")

# Lấy dữ liệu từ bảng uet_content
with engine.connect() as conn:
    result = conn.execute(text("SELECT id, id_url, paragraph FROM uet_content WHERE type = 'url' AND chunking = 0;"))
    rows = result.fetchall()

# Hàm tách đoạn văn thành các đoạn nhỏ <= max_words từ
def split_into_chunks(html, max_words=200):
    soup = BeautifulSoup(html, "html.parser")
    content_div = soup.find(id="content")

    if content_div:
        raw_text = content_div.get_text(separator="\n")
        cleaned_text = re.sub(r'\n\s*\n+', '\n\n', raw_text.strip())
    else:
        print("Không tìm thấy thẻ có id='content'")
        cleaned_text = ""

    paragraphs = cleaned_text.split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        words = para.split()
        if len(words) <= max_words:
            # Gộp nếu còn dư chỗ trong chunk hiện tại
            if len(current_chunk.split()) + len(words) <= max_words:
                current_chunk += " " + " ".join(words)
            else:
                chunks.append(current_chunk.strip())
                current_chunk = " ".join(words)
        else:
            # Tách đoạn dài thành nhiều chunk con
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
                current_chunk = ""

            for i in range(0, len(words), max_words):
                chunk = " ".join(words[i:i + max_words])
                chunks.append(chunk.strip())

    # Thêm chunk cuối nếu còn
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks

# Xử lý từng dòng dữ liệu
with engine.connect() as conn:
    lenRow = len(rows)
    count = 0
    for row in rows:
        id_content, id_url, html_content = row
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Lấy nội dung của thẻ <title> làm main_title
        main_title = soup.title.get_text(strip=True) if soup.title else "No Title"
        
        chunks_to_insert = []
        
        chunks = split_into_chunks(html_content)

        for content_text in chunks:
            if not content_text:  # Bỏ qua đoạn không có text
                continue
            
            last_modified = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            
            chunks_to_insert.append({
                "id_url": id_url,
                "main_title": main_title,
                "sub_title": None,
                "content": content_text,
                "last_modified": last_modified
            })
        
        # Lưu tất cả chunks của một dòng vào bảng uet_chunking
        if chunks_to_insert:
            conn.execute(
                text("INSERT INTO uet_chunking (id_url, main_title, sub_title, content, last_modified) "
                     "VALUES (:id_url, :main_title, :sub_title, :content, :last_modified)"),
                chunks_to_insert
            )
            conn.commit()
        
        # Cập nhật trạng thái chunking = 1
        conn.execute(text("UPDATE uet_content SET chunking = 1 WHERE id = :id_content"), {"id_content": id_content})
        conn.commit()
        count += 1
        print(f"{count}/{lenRow}")

print("Chia chunk và lưu vào uet_chunking hoàn tất!")
