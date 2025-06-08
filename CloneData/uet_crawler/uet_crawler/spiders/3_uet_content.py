import datetime
import scrapy
import sqlite3
import os
import re
from bs4 import BeautifulSoup  # Import BeautifulSoup để xử lý HTML

class ContentSpider(scrapy.Spider):
    name = "uet_content"

    def __init__(self):
        """Khởi tạo CSDL SQLite và tạo bảng nếu chưa tồn tại."""
        db_path = r"E:\Code\Master\BDT\Test\CloneData\uet_crawler\scrapy.db"  # Đường dẫn đến file .db
        self.conn = sqlite3.connect(db_path)  # Kết nối đến SQLite
        self.cursor = self.conn.cursor()

        # Lấy danh sách URL cần thu thập
        self.cursor.execute("SELECT url FROM uet_url WHERE content = 0")
        self.start_urls = [row[0] for row in self.cursor.fetchall()]

        # Tạo bảng uet_content nếu chưa tồn tại
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS uet_content (
                url TEXT,
                paragraph TEXT,
                type TEXT CHECK(type IN ('url', 'file')),  -- Loại dữ liệu: 'url' hoặc 'file'
                last_modified DATE  -- Thời gian cập nhật
            )
        """)
        self.conn.commit()

    def updateContent(self, page_url, content, content_type):
        """Cập nhật nội dung vào bảng uet_content"""
        self.cursor.execute("""
            INSERT INTO uet_content (url, paragraph, type, last_modified) 
            VALUES (?, ?, ?, ?)""",
            (page_url, content, content_type, datetime.datetime.now())
        )
        self.conn.commit()
        
    def updateUrl(self, url):
        """Đánh dấu URL đã được thu thập nội dung"""
        self.cursor.execute("UPDATE uet_url SET content = 1, last_modified = ? WHERE url = ?", 
                            (datetime.datetime.now(), url))
        self.conn.commit()

    def parse(self, response):
        content_type = response.headers.get('Content-Type', b'').decode()
        page_url = response.url  # Lấy URL của trang
        save_dir = r"E:\Code\Master\BDT\CloneFile"  # Thư mục lưu file

        if 'text/html' in content_type:
            # Sử dụng BeautifulSoup để phân tích HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Xóa các thẻ <script> và <style>
            for tag in soup(["script", "style"]):
                tag.decompose()

            # Lấy nội dung HTML đã lọc bỏ JS & CSS
            cleaned_html = str(soup)

            # Lưu vào SQLite với type='url'
            self.updateContent(page_url, cleaned_html, "url")
            self.updateUrl(page_url)

            # print(f"✅ Đã lấy nội dung từ {page_url} (Không có JS & CSS)")

        else:
            # Chuyển đổi URL thành tên file hợp lệ
            safe_filename = re.sub(r'[<>:"/\\|?*]', '_', page_url)  

            # Định dạng file dựa vào Content-Type
            ext = {
                'application/pdf': '.pdf',
                'image/jpeg': '.jpg',
                'image/png': '.png',
                'image/gif': '.gif',
                'application/zip': '.zip',
                'application/msword': '.doc',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            }.get(content_type, '')  # Mặc định không có đuôi

            MAX_LEN = 200
            if len(safe_filename) + len(ext) > MAX_LEN:
                safe_filename = safe_filename[-(MAX_LEN - len(ext)):]  # cắt từ cuối

            filename = f"{safe_filename}{ext}"  
            filepath = os.path.join(save_dir, filename)

            # Đảm bảo thư mục tồn tại
            os.makedirs(save_dir, exist_ok=True)

            # Lưu file vào ổ đĩa
            with open(filepath, "wb") as f:
                f.write(response.body)

            # Lưu vào SQLite với type='file' và paragraph là đường dẫn file
            self.updateContent(page_url, filepath, "file")
            self.updateUrl(page_url)

            # print(f"📂 File đã lưu: {filepath}")

    def closed(self, reason):
        """Đóng kết nối SQLite sau khi thu thập dữ liệu xong."""
        self.conn.close()
