from sqlalchemy import create_engine, text
from bs4 import BeautifulSoup
from transformers import pipeline
import re

# corrector = pipeline("text2text-generation", model="bmd1905/vietnamese-correction-v2", device=0)
# MAX_LENGTH = 512

# def split_text_by_dot(text, max_words=512):
#     sentences = re.findall(r'[^.]+(?:\.)?', text)

#     chunks = []
#     current_chunk = []
#     current_word_count = 0

#     for sentence in sentences:
#         sentence_words = sentence.strip().split()
#         sentence_word_count = len(sentence_words)

#         if current_word_count + sentence_word_count > max_words:
#             if current_chunk:
#                 chunks.append(" ".join(current_chunk))
#             current_chunk = [sentence.strip()]
#             current_word_count = sentence_word_count
#         else:
#             current_chunk.append(sentence.strip())
#             current_word_count += sentence_word_count

#     if current_chunk:
#         chunks.append(" ".join(current_chunk))

#     return chunks

# def vietnamese_correction(text):
#     texts = split_text_by_dot(text)
#     predictions = corrector(texts, max_length=MAX_LENGTH, batch_size=8)  # Dùng batch_size
#     return " ".join([p['generated_text'] for p in predictions])

def get_clean_content(html):
    soup = BeautifulSoup(html, 'lxml')
    content = soup.find(id="content")
    if not content:
        return ["", ""]

    for tag in content.find_all(True): 
        if not isinstance(tag.attrs, dict):
            continue
        if tag.get('href') or tag.get('src'):
            tag.decompose()

    content_raw = content.get_text(separator=" ", strip=True)
    content_raw = re.sub(r'\s+', ' ', content_raw).strip()
    content_raw = re.sub(r'(.)\1{4,}', r'\1', content_raw)
    # return [content_raw, vietnamese_correction(content_raw)]
    return [content_raw, ""]

def html_to_title_and_text(html: str) -> tuple[str, str, str]:
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""
    content = get_clean_content(html)
    return title, content[0], content[1]

def process_and_save_to_db(engine):
    select_sql = text("""
        SELECT id, id_url, paragraph
        FROM uet_content
        WHERE clear = 0 and type = 'url'
    """)

    insert_sql = text("""
        INSERT INTO uet_clear (id_url, title, content_raw, content_clean)
        VALUES (:id_url, :title, :content_raw, :content_clean)
        ON DUPLICATE KEY UPDATE
            title = VALUES(title),
            content_raw = VALUES(content_raw),
            content_clean = VALUES(content_clean)
    """)

    update_chunking_sql = text("""
        UPDATE uet_content
        SET clear = 1
        WHERE id = :id
    """)
    
    with engine.connect() as conn:
        result = conn.execute(select_sql).fetchall()
        len_result = len(result)
        count = 0

        for row in result:
            count += 1
            content_id = row.id
            id_url = row.id_url
            html = row.paragraph

            title, content_raw, content_clean = html_to_title_and_text(html)

            conn.execute(insert_sql, {
                "id_url": id_url,
                "title": title,
                "content_raw": content_raw,
                "content_clean": content_clean
            })

            conn.execute(update_chunking_sql, {"id": content_id})
            conn.commit()
            print(f"{count}/{len_result}")

if __name__ == "__main__":
    engine = create_engine("mysql+pymysql://root:root@localhost/chatbot")
    process_and_save_to_db(engine)
    print("✅ Đã hoàn thành xử lý và lưu vào bảng uet_clear.")
