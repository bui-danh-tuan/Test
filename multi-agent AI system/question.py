import requests

API_KEY = ""  # ← Thay bằng khóa API thực tế
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

headers = {
    "Content-Type": "application/json"
}

context = r"""https://uet.vnu.edu.vn/wp-content/uploads/2018/11/H%C6%B0%E1%BB%9Bng-d%E1%BA%ABn-%C4%91%C4%83ng-k%C3%BD-h%E1%BB%8Dc.pdf"""

payload = {
    "contents": [
        {
            "parts": [
                {
                    "text": f"Tạo câu hỏi từ link sau: {context}"
                }
            ]
        }
    ]
}

response = requests.post(URL, headers=headers, json=payload)
response.raise_for_status()

data = response.json()
print("✅ Phản hồi từ Gemini:")
print(data["candidates"][0]["content"]["parts"][0]["text"])
