from sentence_transformers import SentenceTransformer, util

# 1️⃣ Load mô hình SBERT (MiniLM nhẹ, nhanh, chính xác cao)
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# 2️⃣ Danh sách câu hỏi đã lưu (dữ liệu mẫu)
questions = [
    "Làm thế nào để đăng ký học phần?",
    "Học phí của trường là bao nhiêu?",
    "Khi nào bắt đầu kỳ thi cuối kỳ?",
    "Làm thế nào để xin nghỉ học tạm thời?",
    "Thời gian đăng ký học lại là khi nào?"
]

# 3️⃣ Chuyển danh sách câu hỏi thành vector embeddings
question_vectors = model.encode(questions)

# 4️⃣ Người dùng nhập câu hỏi mới
user_question = "Tôi muốn biết cách đăng ký môn học."

# 5️⃣ Chuyển câu hỏi người dùng thành vector
user_vector = model.encode(user_question)

# 6️⃣ Tìm câu hỏi gần nhất trong danh sách bằng cosine similarity
similarities = util.cos_sim(user_vector, question_vectors)

# 7️⃣ Lấy câu hỏi có độ tương đồng cao nhất
best_match_idx = similarities.argmax()
best_match = questions[best_match_idx]

print(f"✅ Câu hỏi gần nhất: {best_match}")
