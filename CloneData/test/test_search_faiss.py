import faiss
import torch
import pickle
from transformers import BertTokenizer, BertModel

# Bước 1: Load tokenizer và model
tokenizer = BertTokenizer.from_pretrained("bert-base-multilingual-cased")
model = BertModel.from_pretrained("bert-base-multilingual-cased")
model.eval()

# Bước 2: Load FAISS index và danh sách id
index = faiss.read_index(r"E:\Code\Master\BDT\Test\CloneData\faiss_has_accent.index")
with open(r"E:\Code\Master\BDT\Test\CloneData\faiss_ids.pkl", "rb") as f:
    id_list = pickle.load(f)  # list các id tương ứng với từng vector trong index

# Bước 3: Nhập đoạn văn bản truy vấn
query = "vietcombank"

# Tokenize và tạo embedding
inputs = tokenizer(query, return_tensors="pt", truncation=True, max_length=512)
with torch.no_grad():
    outputs = model(**inputs)
    last_hidden_state = outputs.last_hidden_state  # (batch_size, seq_len, hidden_size)
    attention_mask = inputs['attention_mask']
    mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
    summed = torch.sum(last_hidden_state * mask_expanded, dim=1)
    summed_mask = torch.clamp(mask_expanded.sum(dim=1), min=1e-9)
    mean_pooled = summed / summed_mask  # mean pooling

# Chuyển sang numpy
query_vector = mean_pooled.numpy()

# Bước 4: Tìm top 5 vector gần nhất
k = 5
distances, indices = index.search(query_vector, k)

# Bước 5: In ra ID tương ứng
print("Top 5 ID gần nhất:")
for idx in indices[0]:
    print(id_list[idx])
