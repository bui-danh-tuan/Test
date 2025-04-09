from bs4 import BeautifulSoup
import re

# Hàm chuyển HTML thành văn bản sạch
def html_to_text(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    return html

# Hàm tách đoạn văn thành các đoạn nhỏ <= 500 từ
def split_into_chunks(html, max_words=500):
    soup = BeautifulSoup(html, "html.parser")
    content_div = soup.find(id="content")

    if content_div:
        raw_text = content_div.get_text(separator="\n")
        cleaned_text = re.sub(r'\n\s*\n+', '\n\n', raw_text.strip())
    else:
        print("Không tìm thấy thẻ có id='content'")
        cleaned_text = ""


    paragraphs = cleaned_text.split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if not para.strip():
            continue
        words = para.strip().split()
        if len(current_chunk.split()) + len(words) <= max_words:
            current_chunk += " " + " ".join(words)
        else:
            chunks.append(current_chunk.strip())
            current_chunk = " ".join(words)

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks

# Sử dụng các hàm
html_path = "E:/Code/Master/BDT/Test/CloneData/test/test_chuking.html"
cleaned_text = html_to_text(html_path)

if cleaned_text:
    chunks = split_into_chunks(cleaned_text, max_words=500)
    for i, chunk in enumerate(chunks, start=1):
        print(f"--- Đoạn {i}-{len(chunk.split())} từ ---\n{chunk}\n")
