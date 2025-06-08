from sqlalchemy import create_engine, text
from datetime import datetime
import sqlite3

# 🔹 Kết nối đến MySQL
username = "root"
password = "root"
host = "localhost"
database = "chatbot"

# SQLite
db_path = r"E:\Code\Master\BDT\Test\CloneData\uet_crawler\scrapy.db"  # Đường dẫn đến file .db

# Mysql
engine = create_engine(f"mysql+pymysql://{username}:{password}@{host}/{database}")
last_modified_sql = text("SELECT MAX(last_modified) FROM uet_url")
with engine.connect() as connection:
    last_modified = connection.execute(last_modified_sql, {}).fetchone()[0]
last_modified_str = last_modified.strftime("%Y-%m-%d %H:%M:%S.%f") if last_modified else "2000-03-25 18:07:12.922654"

# 🔹 Danh sách dữ liệu cần chèn
def sqlite_to_dict(last_modified, table_name):
    # Kết nối đến database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Lấy dữ liệu từ bảng
    cursor.execute(f"SELECT * FROM {table_name} WHERE last_modified > '{last_modified}'")
    columns = [desc[0] for desc in cursor.description]  # Lấy tên cột
    rows = cursor.fetchall()  # Lấy tất cả dữ liệu

    # Chuyển thành danh sách dictionary
    data = [dict(zip(columns, row)) for row in rows]

    # Đóng kết nối
    conn.close()
    
    return data

def insertMySQL_url(data_list):

    # 🔹 Câu lệnh SQL INSERT
    insert_sql = text("""
        INSERT INTO uet_url (id_parents, url, crawled, depth, last_modified, content) 
        VALUES (:id_parents, :url, :crawled, :depth, :last_modified, :content) 
        ON DUPLICATE KEY UPDATE 
            content = VALUES(content), 
            last_modified = VALUES(last_modified);
    """)

    # 🔹 Câu lệnh SQL để tìm id của `id_parents`
    find_parent_sql = text("""
        SELECT id FROM uet_url WHERE url = :parent_url LIMIT 1
    """)

    # 🔹 Thực hiện chèn dữ liệu vào database
    with engine.connect() as connection:
        for data in data_list:
            # Tìm id_parents nếu có giá trị
            id_parents = None
            if data["parents"]:
                result = connection.execute(find_parent_sql, {"parent_url": data["parents"]}).fetchone()
                if result:
                    id_parents = result[0]

            # Chèn dữ liệu vào bảng uet_url với last_modified dạng datetime
            connection.execute(insert_sql, {
                "id_parents": id_parents,
                "url": data["url"],
                "crawled": data["crawled"],
                "depth": data["depth"],
                "content": data["content"],
                "last_modified": datetime.strptime(data["last_modified"], "%Y-%m-%d %H:%M:%S.%f")
            })
        
        connection.commit()

    print("Dữ liệu đã được chèn thành công!")


def insertMySQL_content(data_list):

    # 🔹 Câu lệnh SQL INSERT
    insert_sql = text("""
        INSERT INTO uet_content (id_url, paragraph, type, last_modified) 
        VALUES (:id_url, :paragraph, :type, :last_modified) 
    """)

    # 🔹 Câu lệnh SQL để tìm id của `id_parents`
    find_parent_sql = text("""
        SELECT id FROM uet_url WHERE url = :url LIMIT 1
    """)

    # 🔹 Thực hiện chèn dữ liệu vào database
    with engine.connect() as connection:
        for data in data_list:
            # Tìm id_parents nếu có giá trị
            id_url = None
            result = connection.execute(find_parent_sql, {"url": data["url"]}).fetchone()
            if result:
                id_url = result[0]

            # Chèn dữ liệu vào bảng uet_url với last_modified dạng datetime
            connection.execute(insert_sql, {
                "id_url": id_url,
                "paragraph": data["paragraph"],
                "type": data["type"],
                "last_modified": datetime.strptime(data["last_modified"], "%Y-%m-%d %H:%M:%S.%f")
            })
        
        connection.commit()

    print("Dữ liệu đã được chèn thành công!")

insertMySQL_url(sqlite_to_dict(last_modified_str, "uet_url"))
insertMySQL_content(sqlite_to_dict(last_modified_str, "uet_content"))