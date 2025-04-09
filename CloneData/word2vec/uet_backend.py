from flask import Flask, request, jsonify
import torch
from transformers import AutoTokenizer, AutoModel
import faiss
import os
import pickle
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import requests
from flask_cors import CORS  

# === Cấu hình Flask ===
app = Flask(__name__)
CORS(app)

# === Cấu hình DeepSeek API ===
API_KEY = 'sk-28d50b0bd2614132a76b99517444980f'
API_URL = 'https://api.deepseek.com/v1/chat/completions'

# === Load PhoBERT ===
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_name = "vinai/phobert-large"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name).to(device)

# === FAISS paths ===
base_path = r"E:\Code\Master\BDT\Test\CloneData"
faiss_has_accent_path = os.path.join(base_path, "faiss_has_accent.index")
faiss_ids_path = os.path.join(base_path, "faiss_ids.pkl")

# === MySQL connection ===
engine = create_engine("mysql+pymysql://root:root@localhost/chatbot")
Session = sessionmaker(bind=engine)
session = Session()


# === Hàm chuyển văn bản thành vector ===
def get_vector(text):
    input_ids = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)["input_ids"].to(device)
    with torch.no_grad():
        outputs = model(input_ids)
        last_hidden_state = outputs.last_hidden_state
        vector = last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
    return vector


# === Lấy các ID gần nhất theo vector ===
def get_ids_by_text(text, top_k=5):
    index = faiss.read_index(faiss_has_accent_path)
    with open(faiss_ids_path, 'rb') as f:
        id_map = pickle.load(f)
    rev_id_map = {v: k for k, v in id_map.items()}

    query_vec = get_vector(text).reshape(1, -1).astype('float32')
    distances, indices = index.search(query_vec, top_k)

    results = []
    for i in range(top_k):
        faiss_idx = indices[0][i]
        distance = distances[0][i]
        original_id = rev_id_map.get(faiss_idx)
        results.append((original_id, distance))

    return results


# === Gọi API DeepSeek để lấy câu trả lời ===
def call_deepseek(question, context):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    messages = [
        {"role": "system", "content": "Bạn là trợ lý AI thông minh. Trả lời ngắn gọn, đúng trọng tâm theo văn bản tham khảo. Không được đưa ra nhận xét hoặc suy đoán. Nếu câu trả lời không có trong văn bản, hãy im lặng và không trả lời gì cả."},
        {"role": "user", "content": f"Văn bản tham khảo:\n{context}"},
        {"role": "user", "content": f"Câu hỏi: {question}"}
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


# === API: Nhận câu hỏi và trả về câu trả lời ===
@app.route("/chatbot", methods=["POST"])
def chatbot():
    data = request.json
    question = data.get("question")

    if not question:
        return jsonify({"error": "Thiếu câu hỏi"}), 400

    try:
        list_context = get_ids_by_text(question)
        list_ids = [l[0] for l in list_context]

        placeholders = ','.join([':id'+str(i) for i in range(len(list_ids))])
        sql = text(f"SELECT id, content FROM uet_clear WHERE id IN ({placeholders})")
        params = {f'id{i}': list_ids[i] for i in range(len(list_ids))}
        results = session.execute(sql, params).fetchall()

        context = "\n\n".join([row[1] for row in results])

        answer = call_deepseek(question, context)
        return jsonify({"context": context, "answer": answer})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# === Chạy server Flask ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
