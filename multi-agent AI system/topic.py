import requests

API_KEY = ""  # ← Thay bằng API key thật

def generate_chatbot_topics():
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    messages = [
        {
            "role": "system",
            "content": "Bạn là một trợ lý AI chuyên hỗ trợ xây dựng chatbot trong lĩnh vực giáo dục đại học."
        },
        {
            "role": "user",
            "content": "Hãy tạo ra 5 chủ đề hữu ích cho chatbot hỗ trợ sinh viên đại học Việt Nam. Trình bày dưới dạng danh sách đánh số, ngắn gọn, không thêm chú thích."
        }
    ]

    payload = {
        "model": "grok-3-latest",
        "messages": messages,
        "stream": False,
        "temperature": 0.5
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    result = response.json()
    return result["choices"][0]["message"]["content"]

# Test chạy
if __name__ == "__main__":
    topics = generate_chatbot_topics()
    print("✅ Các chủ đề được tạo:\n")
    print(topics)
