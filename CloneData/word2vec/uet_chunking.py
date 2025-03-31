from sqlalchemy import create_engine, text
from bs4 import BeautifulSoup
from datetime import datetime

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
        
        # Chia nội dung theo từng đoạn <p>
        for p in soup.find_all("p"):
            content_text = p.get_text(strip=True)
            if not content_text:  # Bỏ qua đoạn không có text
                continue
            
            # Kiểm tra nếu có bất kỳ thẻ nào chứa link (href hoặc src)
            links = [tag['href'] for tag in p.find_all(href=True)] + [tag['src'] for tag in p.find_all(src=True)]
            if links:
                content_text += "\n" + "\n".join(links)
            
            last_modified = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            
            chunks_to_insert.append({
                "id_url": id_url, "main_title": main_title, "sub_title": None, "content": content_text, "last_modified": last_modified
            })
        
        # Lưu tất cả chunks của một dòng vào bảng uet_chunking
        if chunks_to_insert:
            conn.execute(
                text("INSERT INTO uet_chunking (id_url, main_title, sub_title, content, last_modified) "
                     "VALUES (:id_url, :main_title, :sub_title, :content, :last_modified)"),
                chunks_to_insert
            )
            conn.commit()
        
        # Cập nhật trạng thái chunkin = 1
        conn.execute(text("UPDATE uet_content SET chunking = 1 WHERE id = :id_content"), {"id_content": id_content})
        conn.commit()
        count += 1
        print(f"{count}/{lenRow}")

print("Chia chunk và lưu vào uet_chunking hoàn tất!")
