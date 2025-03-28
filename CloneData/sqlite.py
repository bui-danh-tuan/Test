import sqlite3

# Kết nối đến database scrapy.db
conn = sqlite3.connect(r"E:\Code\Master\BDT\Test\CloneData\uet_crawler\uet_crawler\spiders\scrapy.db")

def get_base_url():
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
x = get_base_url()
[print(t) for t in x[0]]