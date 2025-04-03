import pickle  # ✅ Thêm import pickle
import torch
import faiss  # ✅ Thêm FAISS
import numpy as np
from transformers import BertModel, BertTokenizer, BertForQuestionAnswering, AutoTokenizer
from sqlalchemy import create_engine, text
from flask import Flask, request, jsonify
from flask_cors import CORS  # ✅ Thêm CORS để fix lỗi kết nối React

app = Flask(__name__)
CORS(app)  # ✅ Cho phép frontend kết nối với backend

modelName = "bert-base-multilingual-uncased"

# Kết nối MySQL
def connect_db():
    engine = create_engine("mysql+pymysql://root:root@localhost/chatbot")
    return engine

# Load FAISS index
def load_faiss_index():
    index_has_accent = faiss.read_index(r"E:\\Code\\Master\\BDT\\Test\\CloneData\\faiss_has_accent.index")
    index_no_accent = faiss.read_index(r"E:\\Code\\Master\\BDT\\Test\\CloneData\\faiss_no_accent.index")
    with open(r"E:\\Code\\Master\\BDT\\Test\\CloneData\\faiss_ids.pkl", "rb") as f:
        id_list = pickle.load(f)  # 🔥 Đảm bảo danh sách ID được load đúng
    return index_has_accent, index_no_accent, id_list

# Encode văn bản thành vector với BERT
def encode_text(text, tokenizer, model, device):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512).to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state[:, 0, :].cpu().numpy().astype(np.float32)

# Tìm kiếm trong FAISS
def search_faiss(query, index, tokenizer, model, device, top_k):
    query_vector = encode_text(query, tokenizer, model, device)
    distances, indices = index.search(query_vector, top_k)
    return indices[0]

# Load mô hình BERT QA để tạo câu trả lời
qa_tokenizer = BertTokenizer.from_pretrained(modelName)
qa_model = BertForQuestionAnswering.from_pretrained(modelName).to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))

# Sinh câu trả lời từ BERT
def generate_answer(question, context):
    inputs = qa_tokenizer(question, context, return_tensors="pt", padding=True, truncation=True, max_length=512).to(qa_model.device)
    with torch.no_grad():
        outputs = qa_model(**inputs)

    start_scores, end_scores = outputs.start_logits, outputs.end_logits
    start_index = torch.argmax(start_scores)
    end_index = torch.argmax(end_scores) + 1

    answer = qa_tokenizer.convert_tokens_to_string(
        qa_tokenizer.convert_ids_to_tokens(inputs["input_ids"][0][start_index:end_index])
    )

    return answer

# Load BERT model và tokenizer
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tokenizer = BertTokenizer.from_pretrained(modelName)
model = BertModel.from_pretrained(modelName).to(device)

# Kết nối DB và FAISS
engine = connect_db()
session = engine.connect()
index_has_accent, index_no_accent, id_list = load_faiss_index()

@app.route("/chatbot", methods=["POST"])
def chatbot():
    data = request.json
    query = data.get("question")
    
    # Tìm kiếm trong FAISS
    indices = search_faiss(query, index_has_accent, tokenizer, model, device, top_k=5)
    
    # Truy vấn nội dung từ MySQL
    retrieved_texts = []
    for idx in indices:
        if 0 <= idx < len(id_list):
            doc_id = id_list[idx]
            query_db = text("SELECT main_title, content FROM uet_clear WHERE id = :id")
            row = session.execute(query_db, {"id": doc_id}).fetchone()
            if row:
                retrieved_texts.append(f"{row[0]}: {row[1]}")

    # Gộp nội dung lại làm ngữ cảnh
    context = " ".join(retrieved_texts)
    
    if context:
        answer = generate_answer(query, context)
        return jsonify({"answer": answer, "indices": ",".join(map(str, indices.tolist()))})
    else:
        return jsonify({"answer": "Không tìm thấy câu trả lời phù hợp."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
