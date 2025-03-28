from scrapy.dupefilters import RFPDupeFilter

import datetime
import sqlite3


class CustomDupeFilter(RFPDupeFilter):
    def request_seen(self, request):
        if super().request_seen(request):
            self.on_duplicate_request(request)
            return True
        return False
    
    def mark_url_as_crawled(self, url):
        db_path = "scrapy.db"
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("UPDATE uet_url SET crawled=1, last_modified=? WHERE url=?", (datetime.datetime.now(),url,))
        conn.commit()
        conn.close()

    def on_duplicate_request(self, request):
        self.mark_url_as_crawled(request.url)
        
