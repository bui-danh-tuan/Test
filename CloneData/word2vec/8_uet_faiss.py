# vectorize_uet_clear_split.py
import os, numpy as np, torch
import faiss, pandas as pd
from transformers import AutoTokenizer, AutoModel
from sqlalchemy import create_engine, text, bindparam
from sqlalchemy.orm import sessionmaker

# ───────────────────────────────────────────────────────────────
# 1) PhoBERT-large → batch-encode & L2-normalize
# ───────────────────────────────────────────────────────────────
device      = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_name  = "vinai/phobert-large"
tokenizer   = AutoTokenizer.from_pretrained(model_name)
model       = AutoModel.from_pretrained(model_name).to(device).eval()

def encode_batch(texts: list[str]) -> np.ndarray:
    """Encode ≤64 câu → ndarray (B, 1024) đã chuẩn hoá."""
    if not texts:
        return np.empty((0, 1024), dtype="float32")

    tok = tokenizer(
        texts, padding=True, truncation=True, max_length=512,
        return_tensors="pt"
    ).to(device)

    with torch.no_grad():
        hid  = model(**tok).last_hidden_state            # (B, L, D)
        mask = tok["attention_mask"].unsqueeze(-1)       # (B, L, 1)
        vec  = (hid * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
        vec  = torch.nn.functional.normalize(vec, p=2, dim=1)

    return vec.cpu().numpy().astype("float32")

# ───────────────────────────────────────────────────────────────
# 2) FAISS helpers – 3 index riêng
# ───────────────────────────────────────────────────────────────
base_path = r"E:\Code\Master\BDT\Test\CloneData\word2vec"
idx_paths = {
    "title"   : os.path.join(base_path, "faiss_clear_title.index"),
    "subtitle": os.path.join(base_path, "faiss_clear_subtitle.index"),
    "content" : os.path.join(base_path, "faiss_clear_content.index"),
}

def load_or_create(path: str, dim: int = 1024):
    return faiss.read_index(path) if os.path.exists(path) \
           else faiss.IndexIDMap2(faiss.IndexFlatIP(dim))

indexes = {k: load_or_create(p) for k, p in idx_paths.items()}

# ───────────────────────────────────────────────────────────────
# 3) DB & cấu hình batch
# ───────────────────────────────────────────────────────────────
engine  = create_engine(
    "mysql+pymysql://root:root@localhost/chatbot",
    pool_pre_ping=True, pool_recycle=3600
)
Session = sessionmaker(bind=engine)

BATCH_DB  = 4000   # đọc 4k dòng/lần
BATCH_EMB = 64     # encode ≤64 câu/GPU batch

# câu UPDATE đã khai báo bindparam(expanding=True)
SQL_UPD = text("""
    UPDATE uet_clear
       SET vector = 1
     WHERE id IN :ids
""").bindparams(bindparam("ids", expanding=True))

# ───────────────────────────────────────────────────────────────
# 4) Pipeline
# ───────────────────────────────────────────────────────────────
def vectorize():
    sess  = Session()
    added = {"title": 0, "subtitle": 0, "content": 0}

    while True:
        # Lấy một lô dòng chưa vector-hóa
        sql_sel = f"""
            SELECT id, main_title, sub_title, content
              FROM uet_clear
             WHERE vector = 0
             LIMIT {BATCH_DB}
        """
        df = pd.read_sql(sql_sel, engine)
        if df.empty:
            break

        # Gom văn bản cho 3 trường
        buckets = {"title": ([], []), "subtitle": ([], []), "content": ([], [])}
        for _, r in df.iterrows():
            _id = int(r.id)
            if r.main_title:
                buckets["title"][0].append(_id)
                buckets["title"][1].append(r.main_title)
            if r.sub_title:
                buckets["subtitle"][0].append(_id)
                buckets["subtitle"][1].append(r.sub_title)
            if r.content:
                buckets["content"][0].append(_id)
                buckets["content"][1].append(r.content)

        # Encode & add vào index
        for field, (ids, texts) in buckets.items():
            if not ids:
                continue
            for i in range(0, len(texts), BATCH_EMB):
                vecs   = encode_batch(texts[i:i + BATCH_EMB])
                id_arr = np.asarray(ids[i:i + BATCH_EMB], dtype="int64")
                indexes[field].add_with_ids(vecs, id_arr)
            added[field] += len(ids)
            print(f"➕ {field:<8} +{len(ids):>5} → total {indexes[field].ntotal:,}")

        # Cập nhật cờ vector
        sess.execute(SQL_UPD, {"ids": list(df.id)})
        sess.commit()

    # Lưu index
    for k, idx in indexes.items():
        faiss.write_index(idx, idx_paths[k])

    print("✅ FINISHED – added:",
          ", ".join(f"{k}:{v}" for k, v in added.items()))

# ───────────────────────────────────────────────────────────────
# 5) Main
# ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    vectorize()
