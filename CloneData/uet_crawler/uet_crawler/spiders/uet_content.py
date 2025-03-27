import datetime
import scrapy
import sqlite3
import os
import re

class ContentSpider(scrapy.Spider):
    name = "uet_content"

    def __init__(self):
        """Khởi tạo CSDL SQLite và tạo bảng nếu chưa tồn tại."""
        self.conn = sqlite3.connect("scrapy.db")  # Kết nối đến SQLite
        self.cursor = self.conn.cursor()
        self.cursor.execute("SELECT url FROM uet_url WHERE content = 0")
        self.start_urls = [row[0] for row in self.cursor.fetchall()]
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS uet_content (
                url TEXT,
                paragraph TEXT,
                last_modified DATE -- Thời gian cập nhật
            )
        """)
        self.conn.commit()
    
    def updateContent(self, page_url, cleaned_para):
        self.cursor.execute("INSERT INTO uet_content (url, paragraph, last_modified) VALUES (?, ?, ?)", (page_url, cleaned_para, datetime.datetime.now()))
        self.conn.commit()
        
    def updateUrl(self, url):
        self.cursor.execute("UPDATE uet_url SET content = 1 WHERE url = ? AND last_modified = ?", (url, datetime.datetime.now()))
        self.conn.commit()

    def parse(self, response):
        content_type = response.headers.get('Content-Type', b'').decode()
        if 'text/html' not in content_type:
            print(f"⚠️ Bỏ qua {response.url} vì không phải HTML (Content-Type: {content_type})")
            return

        """Lấy toàn bộ nội dung HTML của trang và lưu vào SQLite."""
        full_page_content = response.text  # Lấy toàn bộ nội dung trang HTML
        page_url = response.url  # Lấy URL của trang

        # Lưu toàn bộ nội dung trang thay vì chỉ lưu các thẻ <p>
        self.updateContent(page_url, full_page_content)
        self.updateUrl(page_url)

        print(f"✅ Đã lấy nội dung từ url {page_url}")


    def closed(self, reason):
        """Đóng kết nối SQLite sau khi thu thập dữ liệu xong."""
        self.conn.close()
