import requests
from bs4 import BeautifulSoup
import urllib3
from sqlalchemy import create_engine, text

engine = create_engine("mysql+pymysql://root:root@localhost/chatbot")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sitemap_url = "https://uet.vnu.edu.vn/sitemap_index.xml"
response = requests.get(sitemap_url, verify=False)
soup = BeautifulSoup(response.content, 'xml')

sitemaps = soup.find_all('sitemap')
print(f"Tổng số sitemap con: {len(sitemaps)}")

total_urls = 0
new_urls = 0

def url_exists(url):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1 FROM uet_url WHERE url = :url LIMIT 1"), {"url": url})
        return result.first() is not None

def insert_url(url):
    with engine.begin() as conn:   # <-- mỗi lần thêm là commit luôn!
        conn.execute(
            text("INSERT INTO uet_url (url, depth, id_parents) VALUES (:url, 0, NULL)"),
            {"url": url}
        )
        print(f"add url: {url}")

for sitemap in sitemaps:
    loc = sitemap.find('loc').text
    res = requests.get(loc, verify=False)
    sub_soup = BeautifulSoup(res.content, 'xml')
    urls = sub_soup.find_all('url')
    count_new = 0
    for u in urls:
        url = u.find('loc').text
        total_urls += 1
        if not url_exists(url):
            insert_url(url)  # commit ngay mỗi lần thêm
            new_urls += 1
            count_new += 1
    print(f"{loc}: {len(urls)} URL, trong đó {count_new} URL mới")

print(f"Tổng số URL: {total_urls}")
print(f"Tổng số URL chưa có trong uet_url: {new_urls}")
