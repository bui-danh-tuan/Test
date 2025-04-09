import requests

# === Thay bằng API Key thật của bạn ===
API_KEY = 'sk-28d50b0bd2614132a76b99517444980f'
API_URL = 'https://api.deepseek.com/v1/chat/completions'

# === Ngữ cảnh và câu hỏi ===
context = """
Nguyễn Du là một đại thi hào dân tộc Việt Nam, tác giả của Truyện Kiều – một kiệt tác văn học nổi tiếng được viết bằng chữ Nôm.
Tác phẩm nói về số phận của nàng Kiều trong xã hội phong kiến, thể hiện tấm lòng nhân đạo sâu sắc.
Bùi Danh Tuấn là một sinh viên trường uet.
"""

question = "Nguyễn Du đã viết tác phẩm gì nổi tiếng?"

# === Gửi yêu cầu đến DeepSeek ===
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

messages = [
    {"role": "system", "content": "Bạn là trợ lý AI thông minh, chỉ trả lời dựa vào ngữ cảnh người dùng cung cấp."},
    {"role": "user", "content": f"Văn bản tham khảo:\n{context}"},
    {"role": "user", "content": f"Câu hỏi: {question}"}
]

payload = {
    "model": "deepseek-chat",
    "messages": messages,
    "temperature": 0.5
}

response = requests.post(API_URL, headers=headers, json=payload)

# === In kết quả ra màn hình ===
if response.status_code == 200:
    answer = response.json()['choices'][0]['message']['content']
    print("Câu trả lời:", answer)
else:
    print("Lỗi khi gọi API:", response.text)
