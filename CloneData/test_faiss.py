import os
import faiss
import pickle

# Đường dẫn đến các file FAISS và danh sách ID
base_path = r"E:\Code\Master\BDT\Test\CloneData"
faiss_has_accent_path = os.path.join(base_path, "faiss_has_accent.index")
faiss_no_accent_path = os.path.join(base_path, "faiss_no_accent.index")
faiss_ids_path = os.path.join(base_path, "faiss_ids.pkl")

# Kiểm tra và load FAISS index
if os.path.exists(faiss_has_accent_path):
    index_ha = faiss.read_index(faiss_has_accent_path)
    print(f"📘 Số vector (có dấu): {index_ha.ntotal}")
else:
    print("❌ Không tìm thấy faiss_has_accent.index")

if os.path.exists(faiss_no_accent_path):
    index_na = faiss.read_index(faiss_no_accent_path)
    print(f"📗 Số vector (không dấu): {index_na.ntotal}")
else:
    print("❌ Không tìm thấy faiss_no_accent.index")

# Kiểm tra và load danh sách ID
if os.path.exists(faiss_ids_path):
    with open(faiss_ids_path, "rb") as f:
        id_list = pickle.load(f)
    print(f"📋 Tổng số ID: {len(id_list)}")
    print("🆔 Danh sách ID đã import:")
    for idx, id_val in enumerate(id_list, 1):
        print(f"  {idx}. ID = {id_val}")
else:
    print("❌ Không tìm thấy faiss_ids.pkl")
