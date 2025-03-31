import datetime
import scrapy
import sqlite3
from urllib.parse import urljoin

class UETSpider(scrapy.Spider):
    name = "uet_url"
    allowed_domains = ["uet.vnu.edu.vn"]
    db_path = "scrapy.db"
    max_depth = 10  # Giới hạn độ sâu tối đa
    base_depth = 0

    def __init__(self, *args, **kwargs):
        super(UETSpider, self).__init__(*args, **kwargs)
        self.create_db()
        baseUrl = self.get_base_url()
        if baseUrl[0] != None and len(baseUrl[0]) > 0:
            self.start_urls = baseUrl[0]
            self.base_depth = baseUrl[1]
        else:
            self.start_urls = ["https://uet.vnu.edu.vn/"]

    def get_base_url(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""SELECT url, depth
            FROM uet_url
            WHERE crawled = 0
            AND depth = (SELECT MIN(depth) FROM uet_url WHERE crawled = 0);""")
        result = c.fetchall()
        conn.close()
        if result != None and len(result) > 0:
            return ([r[0] for r in result], result[0][1])
        return (None, None)


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
        """Kiểm tra xem URL đã có trong database và đã visited chưa."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT url FROM uet_url WHERE url=?", (url,))
        result = c.fetchone()
        conn.close()
        
        if result is None:
            return False  # Chưa thu thập lần nào
        return len(result) >= 1  # True nếu đã thu thập toàn bộ

    def is_crawled(self, url):
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
        c.execute("INSERT OR IGNORE INTO uet_url (url, crawled, depth, last_modified, parents) VALUES (?, 0, ?, ?, ?)", (url, depth, last_modified, parents,))
        conn.commit()
        conn.close()

    def mark_crawled(self, url, last_modified):
        """Đánh dấu URL đã thu thập hoàn toàn (bao gồm tất cả link con)."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("UPDATE uet_url SET crawled=1, last_modified=? WHERE url=?", (last_modified,url,))
        conn.commit()
        conn.close()

    def error_handler(self, failure, response, depth=0, parents="", lastUrl=False):
        request = failure.request

        if lastUrl:
            self.mark_crawled(parents, datetime.datetime.now())
        if not self.is_visited(request.url):
            self.mark_visited(request.url, depth, datetime.datetime.now(), parents)  # Đánh dấu URL đã thu thập

        self.mark_crawled(request.url, datetime.datetime.now())

        if hasattr(failure.value, "response"):  # Kiểm tra nếu failure có response
            status = failure.value.response.status
            print(f"Request failed with status {status}: {request.url}")
        else:
            print(f"Unexpected error: {failure.value} at {request.url}")

    def parse(self, response, depth=0, parents="", lastUrl=False):

        currentUrl = response.url
        depth = max(depth, self.base_depth)

        if lastUrl:
            self.mark_crawled(parents, datetime.datetime.now())
        if self.is_crawled(currentUrl):
            return
        if not self.is_visited(currentUrl):
            self.mark_visited(currentUrl, depth, datetime.datetime.now(), parents)  # Đánh dấu URL đã thu thập
        if depth >= self.max_depth:
            self.mark_crawled(currentUrl, datetime.datetime.now())  # Đánh dấu hoàn tất nếu đạt độ sâu tối đa
            return

        content_type = response.headers.get('Content-Type', b'').decode()
        if 'text/html' not in content_type:
            self.mark_crawled(currentUrl, datetime.datetime.now())  # Ko lấy link con nếu ko phải html
            return
        
        links = response.xpath("//*[@href]/@href | //*[@src]/@src").getall()
        links = list(set(links))
        validateLinks = []
        for link in links:
            if(not link.startswith("http")):
                full_url = urljoin(currentUrl, link)
            else: full_url = link
            
            if full_url.startswith("https://uet.vnu.edu.vn/") and not self.is_crawled(full_url) and not self.is_visited(full_url):
                validateLinks.append(full_url)
                
        lenLinks = len(validateLinks)

        if(lenLinks == 0):
            self.mark_crawled(currentUrl, datetime.datetime.now())
            return

        for i, link in enumerate(validateLinks):
            if i == lenLinks-1:
                yield response.follow(link, callback=self.parse, errback=self.error_handler, cb_kwargs={"depth": depth + 1, "parents": currentUrl, "lastUrl": True})
            else:
                yield response.follow(link, callback=self.parse, errback=self.error_handler, cb_kwargs={"depth": depth + 1, "parents": currentUrl, "lastUrl": False})
