"""
qa_deepseek.py – Hỏi/đáp sử dụng FAISS (title / subtitle / content) + DeepSeek API

Cách dùng nhanh:
    python qa_deepseek.py "Câu hỏi của bạn?"
    (hoặc chạy rồi nhập câu hỏi trên stdin)

Yêu cầu:
• Đã có 3 index:  faiss_clear_title.index, faiss_clear_subtitle.index, faiss_clear_content.index
• Bảng MySQL:  uet_clear(id, main_title, sub_title, content, …)
• Cài đặt transformers, faiss‑cpu (hoặc faiss‑gpu), requests, pandas, SQLAlchemy.
• Thay API_KEY = "<YOUR_KEY>" bên dưới.
"""

from __future__ import annotations
import os, sys, numpy as np, torch, requests, pandas as pd
import faiss
from transformers import AutoTokenizer, AutoModel
from sqlalchemy import create_engine, text, bindparam
from pathlib import Path
from typing import Optional
import os


# ───────────────────────────────────────────────────────────────
# 1) Model PhoBERT‑large  → vector hoá 1 câu hỏi
# ───────────────────────────────────────────────────────────────
DEVICE      = torch.device("cuda" if torch.cuda.is_available() else "cpu")
PHOBERT_NAME = "vinai/phobert-large"
_tokenizer   = AutoTokenizer.from_pretrained(PHOBERT_NAME)
_model       = AutoModel.from_pretrained(PHOBERT_NAME).to(DEVICE).eval()

@torch.inference_mode()
def embed(text: str) -> np.ndarray:
    tok = _tokenizer(text, truncation=True, padding=True, max_length=512, return_tensors="pt").to(DEVICE)
    hid = _model(**tok).last_hidden_state           # (1, L, 1024)
    mask = tok["attention_mask"].unsqueeze(-1)      # (1, L, 1)
    vec  = (hid * mask).sum(1) / mask.sum(1).clamp(min=1e-9)  # mean pooling
    vec  = torch.nn.functional.normalize(vec, p=2, dim=1)
    return vec.cpu().numpy().astype("float32")[0]               # (1024,)

# ───────────────────────────────────────────────────────────────
# 2) FAISS – load 3 index (title / subtitle / content)
# ───────────────────────────────────────────────────────────────
def get_env(key: str, default: Optional[str] = None, *, required: bool = False) -> Optional[str]:

    from dotenv import load_dotenv

    ENV_PATH: Path = Path(r"E:\Code\Master\BDT\Test\key.env")

    load_dotenv(dotenv_path=ENV_PATH, override=False)
    value = os.getenv(key, default)
    
    if required and (value is None or value == ""):
        raise RuntimeError(f"Biến môi trường '{key}' không tồn tại hoặc rỗng.")
    
    return value
BASE_PATH = r"E:\Code\Master\BDT\Test\CloneData\word2vec"
INDEX_PATHS = {
    "title"   : os.path.join(BASE_PATH, "faiss_clear_title.index"),
    "subtitle": os.path.join(BASE_PATH, "faiss_clear_subtitle.index"),
    "content" : os.path.join(BASE_PATH, "faiss_clear_content.index"),
}

indexes: dict[str, faiss.Index] = {k: faiss.read_index(p) for k, p in INDEX_PATHS.items()}
DIM = 1024  # Phobert large dim

# ───────────────────────────────────────────────────────────────
# 3) MySQL engine
# ───────────────────────────────────────────────────────────────
ENGINE = create_engine("mysql+pymysql://root:root@localhost/chatbot", pool_pre_ping=True, pool_recycle=3600)
SQL_GET_CONTENT = text("""
    SELECT id, main_title, sub_title, content
      FROM uet_clear
     WHERE id IN :ids
""").bindparams(bindparam("ids", expanding=True))

# ───────────────────────────────────────────────────────────────
# 4) DeepSeek API
# ───────────────────────────────────────────────────────────────
def get_env(key: str, default: Optional[str] = None, *, required: bool = False) -> Optional[str]:

    from dotenv import load_dotenv

    ENV_PATH: Path = Path(r"E:\Code\Master\BDT\Test\key.env")

    load_dotenv(dotenv_path=ENV_PATH, override=False)
    value = os.getenv(key, default)
    
    if required and (value is None or value == ""):
        raise RuntimeError(f"Biến môi trường '{key}' không tồn tại hoặc rỗng.")
    
    return value

API_KEY  = get_env("DEEPSEEK", required=True)
API_URL  = "https://api.deepseek.com/v1/chat/completions"
SYSTEM_PROMPT = (
    "Bạn là trợ lý AI thông minh. Trả lời ngắn gọn, đúng trọng tâm theo văn bản tham khảo. "
    "Nếu thông tin chưa xuất hiện, trả lời 'Xin lỗi, tôi không tìm thấy câu trả lời phù hợp.'"
)

# ───────────────────────────────────────────────────────────────
# 5) Hàm search
# ───────────────────────────────────────────────────────────────

def search_ids(question: str, top_k: int = 5):
    qvec = embed(question).reshape(1, DIM)
    out = {}
    for field, idx in indexes.items():
        dists, inds = idx.search(qvec, top_k)
        # Lọc kết quả = -1 (khi index nhỏ hơn top_k)
        ids = [int(i) for i in inds[0] if i != -1]
        out[field] = ids
    return out  # dict với 3 mảng id

# ───────────────────────────────────────────────────────────────
# 6) Hàm gọi DeepSeek
# ───────────────────────────────────────────────────────────────

def call_deepseek(question: str, context: str) -> str:
    if not API_KEY:
        return "[CHƯA ĐẶT API_KEY]"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Văn bản tham khảo:\n{context}"},
        {"role": "user", "content": f"Câu hỏi: {question}"}
    ]
    payload = {"model": "deepseek-chat", "messages": messages, "temperature": 0.5}
    resp = requests.post(API_URL, headers=headers, json=payload, timeout=60)
    if resp.status_code == 200:
        return resp.json()["choices"][0]["message"]["content"].strip()
    return f"[API LỖI {resp.status_code}] {resp.text}"

# ───────────────────────────────────────────────────────────────
# 7) Hàm chính
# ───────────────────────────────────────────────────────────────

def answer_question(question: str, top_k: int = 5):
    id_dict = search_ids(question, top_k=top_k)
    print("\nID tìm được:")
    for f in ("title", "subtitle", "content"):
        print(f"  {f:<8}:", id_dict[f])

    # Gộp tất cả id duy nhất để lấy nội dung
    unique_ids = sorted({i for ids in id_dict.values() for i in ids})
    if not unique_ids:
        print("Không tìm thấy vector gần nhất.")
        return

    with ENGINE.begin() as conn:
        rows = conn.execute(SQL_GET_CONTENT, {"ids": unique_ids}).fetchall()

    # Nối context: chỉ lấy content, nếu rỗng thì bỏ
    context_parts = [r.content for r in rows if r.content]
    context = "\n\n".join(context_parts[:1000])  # giới hạn cực lớn

    print("\nĐang gọi DeepSeek…")
    answer = call_deepseek(question, context)
    print("\n— Trả lời —\n", answer)

# ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) >= 2:
        q = " ".join(sys.argv[1:])
    else:
        q = input("Nhập câu hỏi: ").strip()
    answer_question(q, top_k=5)
