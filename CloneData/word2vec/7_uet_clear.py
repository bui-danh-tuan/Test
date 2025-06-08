"""
7_uet_to_clear.py  ─ Ghi leaf-chunk sạch sang uet_clear (schema 2025-06-08)

uet_chunking(id, id_content, clear, main_title, sub_title, content,…)
        │
        └─►  làm sạch  ─►  uet_clear(id, id_chunking, vector, main_title,
                                     sub_title, content, last_modified)
"""

# ─────────────────────────────────────────────────────────────────────
# 0) IMPORT & CÀI ĐẶT
# ─────────────────────────────────────────────────────────────────────
import re, unicodedata, time
from sqlalchemy import create_engine, text

ENGINE = create_engine(
    "mysql+pymysql://root:root@localhost/chatbot",
    pool_recycle=3600, pool_pre_ping=True
)

# ─────────────────────────────────────────────────────────────────────
# 1) HÀM LÀM SẠCH
# ─────────────────────────────────────────────────────────────────────
BULLET = re.compile(r"^[•\-\u2022]\s*")
SPACE  = re.compile(r"\s+")
REP    = re.compile(r"(.)\1{4,}", flags=re.I)

def clean(text: str) -> str:
    """Bỏ bullet, ghép khoảng trắng, rút ký tự lặp ≥5, chuẩn NFKC."""
    text = BULLET.sub("", text)
    text = SPACE.sub(" ", text).strip()
    text = REP.sub(r"\1", text)
    return unicodedata.normalize("NFKC", text)

# ─────────────────────────────────────────────────────────────────────
# 2) SQL
# ─────────────────────────────────────────────────────────────────────
SEL = text("""
    SELECT id, main_title, sub_title, content
    FROM   uet_chunking
    WHERE  clear = 0
""")

INS = text("""
    INSERT INTO uet_clear (id_chunking, main_title, sub_title, content)
    VALUES (:id_chunking, :main_title, :sub_title, :content)
    ON DUPLICATE KEY UPDATE
        main_title = VALUES(main_title),
        sub_title  = VALUES(sub_title),
        content    = VALUES(content)
""")

UPD = text("UPDATE uet_chunking SET clear = 1 WHERE id = :id")

# ─────────────────────────────────────────────────────────────────────
# 3) PIPELINE
# ─────────────────────────────────────────────────────────────────────
def run(batch=500):
    with ENGINE.begin() as conn:
        rows = conn.execute(SEL).fetchall()
        if not rows:
            print("✔ Không còn leaf mới.")
            return

        buf, done, total = [], 0, len(rows)
        print(f"→ Xử lý {total} leaf-chunks …")

        for r in rows:
            buf.append({
                "id_chunking": r.id,
                "main_title" : clean(r.main_title),
                "sub_title"  : clean(r.sub_title),
                "content"    : clean(r.content)
            })

            if len(buf) >= batch:
                flush(conn, buf); done += len(buf); buf.clear()
                print(f"  • {done}/{total} đã ghi")

        if buf:
            flush(conn, buf); done += len(buf)
            print(f"  • {done}/{total} đã ghi")

        print("✅ Hoàn tất – dữ liệu đã sang uet_clear.")

def flush(conn, buf):
    conn.execute(INS, buf)
    conn.execute(UPD, [{"id": x["id_chunking"]} for x in buf])

# ─────────────────────────────────────────────────────────────────────
# 4) MAIN
# ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    t0 = time.time()
    run(batch=500)
    print("⏱  %.2fs" % (time.time() - t0))
