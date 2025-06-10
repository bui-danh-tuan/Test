import re
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, text
import nltk
nltk.download("punkt", quiet=True)

# ───────────────────────────────────────────────────────────────
def table_to_text(tbl) -> str:
    headers = [th.get_text(" ", strip=True) for th in tbl.select("thead tr th, thead tr td")]
    body_rows = tbl.select("tbody tr")

    if not headers:
        first_tr, *rest = tbl.find_all("tr")
        headers = [td.get_text(" ", strip=True) for td in first_tr.find_all(["td", "th"])]
        body_rows = rest

    out_lines = []
    for tr in body_rows:
        cells = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
        if not any(cells): continue
        pairs = [f"{headers[i]} là {cells[i]}" for i in range(min(len(headers), len(cells)))]
        out_lines.append("\t".join(pairs))
    return ". ".join(out_lines)

def extract_main_content(html_text: str):
    soup = BeautifulSoup(html_text, "html.parser")
    root = soup.select_one("div.single-post-content-text.content-pad")
    if not root:
        return "", ""

    # Tiêu đề
    h = soup.select_one("h2.single-content-title") or soup.h1 or soup.title
    title = h.get_text(" ", strip=True) if h else ""

    # Chuyển bảng thành text
    for tbl in root.select("table"):
        tbl.replace_with(table_to_text(tbl))

    full_text = root.get_text(" ", strip=True)
    return title, full_text

# ───────────────────────────────────────────────────────────────
engine = create_engine("mysql+pymysql://root:root@localhost/chatbot", future=True)

SQL_HTML = text("""
    SELECT id, paragraph
    FROM uet_content
    WHERE paragraph LIKE '%<article class="single-post-content single-content">%';
""")

SQL_INSERT = text("""
    INSERT INTO uet_content_text (id_content, title, content)
    VALUES (:id_content, :title, :content);
""")

# ───────────────────────────────────────────────────────────────
with engine.connect() as conn:
    rows = conn.execute(SQL_HTML).all()

for id_content, html in rows:
    with engine.begin() as tx:
        title, content = extract_main_content(html)
        tx.execute(SQL_INSERT, {
            "id_content": id_content,
            "title": title,
            "content": content,
        })
        tx.commit()
        print(f"✔ ID {id_content} đã lưu")
