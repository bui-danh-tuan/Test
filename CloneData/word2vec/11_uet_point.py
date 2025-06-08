from sqlalchemy import create_engine, text
import requests
import json

def ask_questions_from_db():
    try:
        # Kết nối đến MySQL
        engine = create_engine("mysql+pymysql://root:root@localhost/chatbot")

        with engine.connect() as conn:
            result = conn.execute(text("SELECT question, id FROM uet_qa"))

            for row in result:
                question = row[0]
                question_id = row[1]
                print(f"\n📤 Question ({question_id}): {question}")

                # Gửi request tới API Flask
                response = requests.post(
                    "http://127.0.0.1:5000/chatbot",
                    headers={"Content-Type": "application/json"},
                    data=json.dumps({"question": question})
                )

                if response.status_code == 200:
                    res_json = response.json()

                    actual_answer = res_json.get("answer", "")
                    actual_context = str(res_json.get("top_k_ids", ""))
                    point_data = res_json.get("point", {})

                    # Lấy điểm đánh giá
                    bleu = point_data.get("BLEU", 0)
                    rouge = point_data.get("ROUGE-L", 0)
                    bert = point_data.get("BERTScore", 0)
                    cosine = point_data.get("CosineSimilarity", 0)
                    recall = point_data.get("Recall@k", 0)
                    map_k = point_data.get("MAP@k", 0)

                    # Cập nhật dữ liệu vào bảng uet_qa
                    update_sql = text("""
                        UPDATE uet_qa
                        SET
                            actual_answer = :actual_answer,
                            actual_context = :actual_context,
                            generation_bleu = :bleu,
                            generation_rouge = :rouge,
                            generation_bertscore = :bert,
                            generation_cosine = :cosine,
                            retrieval_recall_at_k = :recall,
                            retrieval_map_at_k = :map_k
                        WHERE id = :id
                    """)

                    conn.execute(update_sql, {
                        "actual_answer": actual_answer,
                        "actual_context": actual_context,
                        "bleu": float(bleu),
                        "rouge": float(rouge),
                        "bert": float(bert),
                        "cosine": float(cosine),
                        "recall": int(recall),
                        "map_k": float(map_k),
                        "id": question_id
                    })
                    conn.commit()

                    print(f"✅ Updated: ID {question_id}")
                else:
                    print(f"❌ API Error {response.status_code}: {response.text}")

    except Exception as e:
        print(f"⚠️ Lỗi: {e}")

ask_questions_from_db()
