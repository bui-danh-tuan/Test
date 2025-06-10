import os, numpy as np, torch
import faiss, pandas as pd
from transformers import AutoTokenizer, AutoModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# PhoBERT-large setup
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_name = "vinai/phobert-large"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name).to(device).eval()

def encode_single(txt: str) -> np.ndarray:
    if not isinstance(txt, str) or not txt.strip():
        return None
    try:
        tok = tokenizer(txt.strip(), return_tensors="pt", padding=True, truncation=True, max_length=512).to(device)
        with torch.no_grad():
            hid = model(**tok).last_hidden_state
            mask = tok["attention_mask"].unsqueeze(-1)
            vec = (hid * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
            vec = torch.nn.functional.normalize(vec, p=2, dim=1)
            return vec.cpu().numpy()[0].astype("float32")
    except Exception as e:
        print(f"[ERROR] Failed to encode: {e}")
        return None

# FAISS setup
base_path = r"E:\Code\Master\BDT\Test\CloneData\word2vec"
idx_paths = {
    "title":    os.path.join(base_path, "faiss_clear_title.index"),
    "subtitle": os.path.join(base_path, "faiss_clear_subtitle.index"),
    "content":  os.path.join(base_path, "faiss_clear_content.index"),
}

def load_or_create(path: str, dim: int = 1024):
    return faiss.read_index(path) if os.path.exists(path) else faiss.IndexIDMap2(faiss.IndexFlatIP(dim))

indexes = {k: load_or_create(p) for k, p in idx_paths.items()}

# DB setup
engine = create_engine("mysql+pymysql://root:root@localhost/chatbot", pool_pre_ping=True, pool_recycle=3600)
Session = sessionmaker(bind=engine)
sess = Session()

def vectorize():
    df = pd.read_sql("SELECT id, main_title, sub_title, content FROM uet_clear WHERE vector = 0 and LENGTH(content) > 0", engine)
    if df.empty:
        print("✅ No data to process.")
        return

    for _, row in df.iterrows():
        _id = int(row.id)
        for field, txt in {
            "title": row.main_title,
            "subtitle": row.sub_title,
            "content": row.content
        }.items():
            if not isinstance(txt, str) or not txt.strip():
                continue

            vec = encode_single(txt)
            if vec is not None:
                try:
                    indexes[field].add_with_ids(np.expand_dims(vec, axis=0), np.array([_id], dtype="int64"))
                    print(f"➕ Added {_id} to {field}")
                except Exception as e:
                    print(f"[ERROR] Failed to add {_id} to {field}: {e}")

        sess.execute(text("UPDATE uet_clear SET vector = 1 WHERE id = :id"), {"id": _id})
        sess.commit()

        # Ghi FAISS sau mỗi dòng để đảm bảo không mất dữ liệu nếu dừng đột ngột
        for k, idx in indexes.items():
            faiss.write_index(idx, idx_paths[k])

    print("✅ FINISHED")

if __name__ == "__main__":
    vectorize()
