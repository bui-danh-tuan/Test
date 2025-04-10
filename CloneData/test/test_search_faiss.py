import faiss

# Define the path to the FAISS index
faiss_index_path = r"E:\Code\Master\BDT\Test\CloneData\faiss_has_accent.index"

# Load the FAISS index
index = faiss.read_index(faiss_index_path)

# Get the total number of vectors in the index
num_vectors = index.ntotal
print(f"Total number of vectors: {num_vectors}")
