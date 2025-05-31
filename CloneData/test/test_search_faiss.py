import faiss
import pickle

faiss_index_path = r"E:\Code\Master\BDT\Test\CloneData\faiss_has_accent.index"
faiss_pkl_path = r"E:\Code\Master\BDT\Test\CloneData\faiss_ids.pkl"

index = faiss.read_index(faiss_index_path)
num_vectors = index.ntotal
print(f"Total number of vectors: {num_vectors}")

with open(faiss_pkl_path, "rb") as f:
    data = pickle.load(f)

# In ra kiểu dữ liệu
# print(data)
