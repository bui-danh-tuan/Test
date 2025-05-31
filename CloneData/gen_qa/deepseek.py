import requests
from sqlalchemy import create_engine, text


API_KEY = 'sk-28d50b0bd2614132a76b99517444980f'
API_URL = 'https://api.deepseek.com/v1/chat/completions'


def call_deepseek(context):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    messages = [
        {"role": "system", "content": "Bạn là trợ lý AI thông minh. Hãy dựa vào đoạn văn tôi gửi hãy sinh ra duy nhất 1 câu hỏi và 1 câu trả lời.Câu hỏi trong 1 đoạn câu trả lời trong 1 đoạn. không xuống dòng trong mỗi đoạn."},
        {"role": "user", "content": f"Văn bản tham khảo:\n{context}"}
    ]

    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.5
    }

    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return f"Lỗi khi gọi API: {response.text}"

engine = create_engine("mysql+pymysql://root:root@localhost/chatbot")
select_sql = text("SELECT * FROM uet_clear WHERE LENGTH(content_raw) > 5000 ORDER BY RAND() LIMIT 60")
with engine.connect() as conn:
    result = conn.execute(select_sql).fetchall()
for row in result:
    a = call_deepseek(row.content_raw)
    print(f"{row.id_url}|{a}")