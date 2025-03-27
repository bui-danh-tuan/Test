import datetime
import scrapy
import sqlite3
from urllib.parse import urljoin

class UETSpider(scrapy.Spider):
    name = "uet_url"
    allowed_domains = ["uet.vnu.edu.vn"]
    start_urls = ["https://uet.vnu.edu.vn/"]
    db_path = "scrapy.db"
    max_depth = 10  # Giới hạn độ sâu tối đa

    def __init__(self, *args, **kwargs):
        super(UETSpider, self).__init__(*args, **kwargs)
        self.create_db()

    def create_db(self):
        """Tạo database để lưu trạng thái URL đã duyệt."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS uet_url (
                url TEXT PRIMARY KEY,
                parents TEXT,
                crawled INTEGER DEFAULT 0,  -- 0: chưa crawl hết, 1: đã hoàn tất,
                depth INTEGER DEFAULT 0,  -- Độ sâu
                content INTEGER DEFAULT 0,  -- Đã lấy html
                last_modified DATE -- Thời gian cập nhật
            )
        """)
        conn.commit()
        conn.close()

    def is_visited(self, url):
        """Kiểm tra xem URL đã có trong database và đã crawl hết chưa."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT crawled FROM uet_url WHERE url=?", (url,))
        result = c.fetchone()
        conn.close()
        
        if result is None:
            return False  # Chưa thu thập lần nào
        return result[0] == 1  # True nếu đã thu thập toàn bộ

    def mark_visited(self, url, depth, last_modified, parents):
        """Đánh dấu URL đã thu thập nhưng chưa hoàn thành."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO uet_url (url, crawled, depth, last_modified, parents) VALUES (?, 0, ?, ?, ?)", (url, depth, last_modified,parents,))
        conn.commit()
        conn.close()

    def mark_crawled(self, url, depth, last_modified):
        """Đánh dấu URL đã thu thập hoàn toàn (bao gồm tất cả link con)."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("UPDATE uet_url SET crawled=1, depth=?, last_modified=? WHERE url=?", (depth,last_modified,url,))
        conn.commit()
        conn.close()

    def parse(self, response):
        """Duyệt qua các link trên trang và thu thập dữ liệu."""
        depth = response.meta.get("depth", 0)  # Lấy độ sâu hiện tại, mặc định là 0
        parents = response.meta.get("parents", "")  # Lấy độ sâu hiện tại, mặc định là 0
        self.mark_visited(response.url, depth, datetime.datetime.now(),parents)  # Đánh dấu URL đã thu thập
        print(f"✅ Đã lấy url {response.url}")
        if depth >= self.max_depth:
            self.mark_crawled(response.url, depth, datetime.datetime.now())  # Đánh dấu hoàn tất nếu đạt độ sâu tối đa
            return
        
        content_type = response.headers.get('Content-Type', b'').decode()
        if 'text/html' not in content_type:
            self.mark_crawled(response.url, depth, datetime.datetime.now())  # Ko lấy link con nếu ko phải html
            print(f"⚠️ Bỏ qua {response.url} vì không phải HTML (Content-Type: {content_type})")
            return

        new_links = []
        for link in response.xpath("//*[@href]/@href | //*[@src]/@src").getall():
            full_url = urljoin(response.url, link)

            if full_url.startswith("https://uet.vnu.edu.vn/") and not self.is_visited(full_url):
                new_links.append(full_url)
                yield response.follow(full_url, callback=self.parse, meta={"depth": depth + 1, "parents": response.url})


        self.mark_crawled(response.url, depth, datetime.datetime.now())
