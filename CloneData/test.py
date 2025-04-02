import faiss
import os
import pickle

def check_faiss_index_size(path_has_accent, path_no_accent, path_ids_pkl):
    # Kiểm tra faiss_has_accent.index
    if os.path.exists(path_has_accent):
        index_ha = faiss.read_index(path_has_accent)
        total_ha = index_ha.ntotal
        print(f"✅ Có dấu (has_accent): {total_ha} vector")
    else:
        total_ha = None
        print(f"❌ Không tìm thấy file: {path_has_accent}")

    # Kiểm tra faiss_no_accent.index
    if os.path.exists(path_no_accent):
        index_na = faiss.read_index(path_no_accent)
        total_na = index_na.ntotal
        print(f"✅ Không dấu (no_accent): {total_na} vector")
    else:
        total_na = None
        print(f"❌ Không tìm thấy file: {path_no_accent}")

    # Kiểm tra faiss_ids.pkl
    if os.path.exists(path_ids_pkl):
        with open(path_ids_pkl, "rb") as f:
            id_list = pickle.load(f)
        total_ids = len(id_list)
        print(f"📦 Số ID trong faiss_ids.pkl: {total_ids}")
    else:
        total_ids = None
        print(f"❌ Không tìm thấy file: {path_ids_pkl}")

    # So sánh kết quả nếu cả 3 file đều tồn tại
    if None not in (total_ha, total_na, total_ids):
        print("\n🔍 Đối chiếu:")
        if total_ha == total_na == total_ids:
            print("✅ Tất cả khớp nhau hoàn hảo!")
        else:
            print("⚠️ KHÔNG khớp:")
            if total_ha != total_ids:
                print(f"  - faiss_has_accent: {total_ha} vs faiss_ids.pkl: {total_ids}")
            if total_na != total_ids:
                print(f"  - faiss_no_accent:  {total_na} vs faiss_ids.pkl: {total_ids}")

# === GỌI HÀM ===
if __name__ == "__main__":
    check_faiss_index_size(
        r"E:\Code\Master\BDT\Test\CloneData\faiss_has_accent.index",
        r"E:\Code\Master\BDT\Test\CloneData\faiss_no_accent.index",
        r"E:\Code\Master\BDT\Test\CloneData\faiss_ids.pkl"
    )
