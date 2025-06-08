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
import nltk
from rouge_score import rouge_scorer
import bert_score
from transformers import AutoTokenizer, AutoModel
import torch.nn.functional as F
from collections import Counter

# === Cấu hình Flask ===
app = Flask(__name__)
CORS(app)

# === Cấu hình DeepSeek API ===
API_KEY = ''
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
        {"role": "system", "content": "Bạn là trợ lý AI thông minh. Trả lời ngắn gọn, đúng trọng tâm theo văn bản tham khảo. Không được đưa ra nhận xét hoặc suy đoán. Nếu câu trả lời không có trong văn bản, hãy trả vễ chuỗi rỗng."},
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

def evaluate_text_generation(generated_answer, reference_answer, top_k_ids, relevant_id):
    import torch
    import numpy as np
    import torch.nn.functional as F
    from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
    from rouge import Rouge
    from transformers import AutoTokenizer, AutoModel

    # Khởi tạo PhoBERT
    tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-large")
    model = AutoModel.from_pretrained("vinai/phobert-large")

    # Hàm con: tạo embedding
    def embed(text):
        tokens = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            outputs = model(**tokens)
        return outputs.last_hidden_state.mean(dim=1).squeeze(0)

    # BLEU
    smoothie = SmoothingFunction().method4
    bleu = sentence_bleu([reference_answer.split()], generated_answer.split(), smoothing_function=smoothie)

    # ROUGE
    rouge = Rouge()
    scores = rouge.get_scores(generated_answer, reference_answer)[0]
    rouge_score = scores['rouge-l']['f']

    # Embedding và cosine
    gen_embed = embed(generated_answer)
    ref_embed = embed(reference_answer)
    cosine_sim = F.cosine_similarity(gen_embed, ref_embed, dim=0).item()
    bert_score = cosine_sim  # approximation dùng cosine toàn câu

    # Recall@k
    recall_at_k = 1 if relevant_id in top_k_ids else 0

    # MAP@k
    map_at_k = 1 / (top_k_ids.index(relevant_id) + 1) if relevant_id in top_k_ids else 0

    return {
        "BLEU": round(bleu, 4),
        "ROUGE-L": round(rouge_score, 4),
        "BERTScore": round(bert_score, 4),
        "CosineSimilarity": round(cosine_sim, 4),
        "Recall@k": recall_at_k,
        "MAP@k": round(map_at_k, 4)
    }


# === API: Nhận câu hỏi và trả về câu trả lời ===
@app.route("/chatbot", methods=["POST"])
def chatbot():
    data = request.json
    question = data.get("question")
    k = 5

    if not question:
        return jsonify({"error": "Thiếu câu hỏi"}), 400

    try:
        # Truy hồi các đoạn liên quan bằng FAISS
        list_context = get_ids_by_text(question)
        list_ids = [l[0] for l in list_context]
        counter = Counter(list_ids)
        top_k_ids = [id_ for id_, _ in counter.most_common(k)]

        # Lấy content để sinh phản hồi (từ bảng uet_chunking)
        placeholders = ','.join([f':id{i}' for i in range(len(list_ids))])
        sql = text(f"""
            SELECT content
            FROM uet_chunking
            WHERE id IN ({placeholders})
        """)
        results = session.execute(sql, {f'id{i}': list_ids[i] for i in range(len(list_ids))}).fetchall()
        context = "\n\n".join([row[0] for row in results])

        # Gọi mô hình sinh phản hồi
        answer = call_deepseek(question, context)

        # Truy vấn câu trả lời kỳ vọng và ID đoạn đúng
        sql = text("SELECT expected_answer, expected_context FROM uet_qa WHERE question = :question")
        result = session.execute(sql, {"question": question}).fetchone()

        if not result:
            return jsonify({"error": "Không tìm thấy expected_answer"}), 404

        expected_answer = result[0]
        relevant_id = result[1]

        # Tính điểm
        point_dict = evaluate_text_generation(
            generated_answer=answer,
            reference_answer=expected_answer,
            top_k_ids=top_k_ids,
            relevant_id=int(relevant_id)
        )

        return jsonify({
            "answer": answer,
            "expected_answer": expected_answer,
            "context": context,
            "relevant_id": relevant_id,
            "top_k_ids": top_k_ids,
            "point": point_dict
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === Chạy server Flask ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
