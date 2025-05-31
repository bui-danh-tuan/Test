import requests

API_KEY = ''
API_URL = 'https://api.deepseek.com/v1/chat/completions'

context = r"""https://uet.vnu.edu.vn/wp-content/uploads/2018/11/H%C6%B0%E1%BB%9Bng-d%E1%BA%ABn-%C4%91%C4%83ng-k%C3%BD-h%E1%BB%8Dc.pdf"""

question = " Quy trình đăng ký học lại/học cải thiện như thế nào?"
def call_deepseek():
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    messages = [
            {"role": "system", "content": "Bạn là trợ lý AI hãy đọc nội dung trong link được cung cấp để trả lời câu hỏi."},
            {"role": "user", "content": f"Link: {context}\nCâu hỏi: {question}"}
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

print(call_deepseek())