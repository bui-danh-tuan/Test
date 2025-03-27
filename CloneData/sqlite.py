import sqlite3

# Kết nối đến database scrapy.db
conn = sqlite3.connect(r"E:\Code\Master\BDT\Test\CloneData\uet_crawler\uet_crawler\spiders\scrapy.db")
cursor = conn.cursor()

# Cập nhật toàn bộ cột content về 0
cursor.execute("UPDATE uet_url SET content = 0")

# Lưu thay đổi và đóng kết nối
conn.commit()
conn.close()

print("✅ Đã cập nhật toàn bộ cột content về 0 trong bảng uet_url.")
