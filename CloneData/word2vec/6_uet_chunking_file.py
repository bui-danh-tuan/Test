# =====================================================================
# 0) KHỞI TẠO & HÀM CHUNG
# =====================================================================
import re, nltk, torch, os
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, text
from transformers import AutoTokenizer
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

# --- NLTK -----------------------------------------------------------------
# Dùng cả punkt lẫn punkt_tab để tránh lỗi trên mọi bản NLTK
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)

# --- PhoBERT --------------------------------------------------------------
TOKENIZER_NAME = "vinai/phobert-base"
MAX_SEQ_LEN    = 510  # 510 + [CLS] + [SEP] = 512

tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME)
device    = "cuda" if torch.cuda.is_available() else "cpu"

embed_model = HuggingFaceEmbeddings(
    model_name   = TOKENIZER_NAME,
    model_kwargs = {"device": device},
    encode_kwargs = {"normalize_embeddings": True},
)

def token_len(text: str) -> int:
    return len(tokenizer(text)["input_ids"])

# -------------------------------------------------------------------------
# 1) TÁCH HEADING GIẢ ➜ MỤC LỚN
# -------------------------------------------------------------------------
RE_ROMAN = re.compile(r"^[IVXLCDM]+\.", re.I)
RE_NUM   = re.compile(r"^\d+[.)]")

def split_coarse(html_text: str):
    HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

    def is_heading(node) -> bool:
        """True nếu node (hoặc con trực tiếp) được xem là heading."""
        # Heading HTML thật
        if node.name in HEADING_TAGS:
            return True

        # Node có chữ đậm?
        bold_parts = node.find_all(["strong", "b"], recursive=False) or \
                    node.find_all(["strong", "b"])
        if not bold_parts:
            return False

        bold_text = " ".join(t.get_text(" ", strip=True) for t in bold_parts)
        all_text  = node.get_text(" ", strip=True)
        # ≥ 60 % văn bản ở dạng đậm → heading
        return len(bold_text) / max(1, len(all_text)) >= 0.6


    def table_to_text(tbl) -> str:
        # 1) Lấy tiêu đề cột (headers)
        headers = [th.get_text(" ", strip=True)
                for th in tbl.select("thead tr th, thead tr td")]
        body_rows = tbl.select("tbody tr")

        if not headers:                           # bảng không có <thead>
            first_tr, *rest = tbl.find_all("tr")
            headers = [td.get_text(" ", strip=True)
                    for td in first_tr.find_all(["td", "th"])]
            body_rows = rest                      # bỏ hàng đầu vì đã lấy làm header

        # 2) Gom mỗi hàng dữ liệu thành “header: value”
        out_lines = []
        for tr in body_rows:
            cells = [td.get_text(" ", strip=True)
                    for td in tr.find_all(["td", "th"])]

            if not any(cells):                    # hàng rỗng → bỏ qua
                continue

            # ghép “<header>: <value>”
            pairs = [f"{headers[i]} là {cells[i]}" 
                    for i in range(min(len(headers), len(cells)))]
            out_lines.append("\t".join(pairs))    # TAB phân tách cột

        return ". ".join(out_lines)


    def extract_text(node) -> str:
        """Trích text của node, đồng thời gom bảng, danh sách, ảnh."""
        out_chunks = []

        if node.name == "table":
            return table_to_text(node)

        # 1) Bảng (mọi độ sâu) – lấy text rồi gỡ khỏi DOM
        for tbl in node.select("table"):
            out_chunks.append(table_to_text(tbl))
            tbl.decompose()

        # 2) Xử lý theo loại thẻ
        if node.name in {"ul", "ol"}:
            for li in node.find_all("li", recursive=False):
                # li đậm ⇒ heading con; ngược lại bullet
                if is_heading(li):
                    out_chunks.append(li.get_text(" ", strip=True))
                else:
                    out_chunks.append("• " + li.get_text(" ", strip=True))

        elif node.name == "img":
            alt = node.get("alt", "").strip()
            if alt:
                out_chunks.append(f"[Hình: {alt}]")

        else:  # p, div, span…
            txt = node.get_text(" ", strip=True)
            if txt:
                out_chunks.append(txt)

        return "\n".join(out_chunks)
    """
    Trả về:
        main_title (str)  – tiêu đề bài viết
        sections   (list) – [(heading, body_text), ...]
    """
    soup = BeautifulSoup(html_text, "html.parser")
    root = soup.select_one("div.single-post-content-text.content-pad")
    if not root:
        return "", []

    # Tiêu đề bài
    h = (
        soup.select_one("h2.single-content-title")  # ưu tiên h2 trong phần nội dung
        or soup.h1                                  # tiếp theo là h1
        or soup.title                               # cuối cùng: <title> trong <head>
    )
    main_title = h.get_text(" ", strip=True) if h else ""

    sections, cur_head, cur_body = [], "", []

    def flush():
        """Đưa section hiện tại vào danh sách, không bỏ sót phần mở đầu."""
        if not cur_body:                     # chẳng có nội dung → thôi
            return
        head = cur_head or main_title or "[Intro]"
        sections.append((head, " ".join(cur_body).strip()))

    for node in root.children:                      # CHỈ con trực tiếp
        if not getattr(node, "name", None):         # node chỉ là '\n'
            continue

        if is_heading(node):                        # ─ heading mới ─
            flush()
            cur_head, cur_body = node.get_text(" ", strip=True), []
        else:
            txt = extract_text(node)
            if txt:
                cur_body.append(txt)
    flush()
    return main_title, sections
# -------------------------------------------------------------------------
# 2) SEMANTIC SPLIT (AN TOÀN)
# -------------------------------------------------------------------------
sem_splitter = SemanticChunker(embeddings=embed_model)

SENT_SPLIT_REGEX = r"(?<=[\.!?;–])\s+|\n+"
CHAR_SPLITTER    = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=60)

def _truncate(sentence: str) -> str:
    ids = tokenizer(sentence)["input_ids"][:MAX_SEQ_LEN]
    return tokenizer.decode(ids, skip_special_tokens=True)

def safe_semantic_split(text: str):
    sentences = [_truncate(s) for s in re.split(SENT_SPLIT_REGEX, text) if s.strip()]
    prepared  = " ".join(sentences)
    try:
        return sem_splitter.split_text(prepared)
    except Exception:
        return CHAR_SPLITTER.split_text(prepared)

# -------------------------------------------------------------------------
# 3) CHIA LEAF ≤ 512 TOKEN
# -------------------------------------------------------------------------

def split_recursive(text: str, max_tok: int = 512, overlap: int = 60):
    sents = nltk.sent_tokenize(text)
    chunks, buf, buflen = [], [], 0

    for sent in sents:
        l = token_len(sent)
        if buflen + l > max_tok:
            chunks.append(" ".join(buf))
            ov = []
            while buf and token_len(" ".join(ov)) < overlap:
                ov.insert(0, buf.pop())
            buf, buflen = ov + [sent], token_len(" ".join(buf + [sent]))
        else:
            buf.append(sent)
            buflen += l
    if buf:
        chunks.append(" ".join(buf))
    return chunks

# -------------------------------------------------------------------------
# 4) DB
# -------------------------------------------------------------------------
engine = create_engine("mysql+pymysql://root:root@localhost/chatbot", future=True)

SQL_HTML = text("""
    SELECT id, paragraph
      FROM uet_content
     WHERE chunking = 0 AND id_url = '10450'
       AND paragraph LIKE '%<article class="single-post-content single-content">%';
""")

SQL_INSERT = text("""
    INSERT INTO uet_chunking (id_content, main_title, sub_title, content)
    VALUES (:id_content, :main_title, :sub_title, :content);
""")

SQL_UPDATE = text("""
    UPDATE uet_content SET chunking = 1 WHERE id = :id_content;
""")

# -------------------------------------------------------------------------
# 5) PIPELINE – COMMIT RIÊNG TỪNG URL
# -------------------------------------------------------------------------
with engine.connect() as conn:
    rows = conn.execute(SQL_HTML).all()  # lấy trước vì conn sẽ tái sử dụng

for id_content, html in rows:
    with engine.begin() as tx:  # mỗi URL 1 transaction riêng, commit ngay khi ra khỏi block

        main_title, sections = split_coarse(html)

        total_leaf = 0
        for idx_sec, (sub_title, body) in enumerate(sections, 1):

            sem_chunks = safe_semantic_split(body)

            for idx_par, sem_chunk in enumerate(sem_chunks, 1):
                tokens_par = token_len(sem_chunk)

                leaf_chunks = split_recursive(sem_chunk)
                for idx_leaf, leaf in enumerate(leaf_chunks, 1):
                    tokens_leaf = token_len(leaf)
                    preview = (leaf[:110] + "…") if len(leaf) > 113 else leaf

                    tx.execute(
                        SQL_INSERT,
                        {
                            "id_content": id_content,
                            "main_title": main_title,
                            "sub_title": sub_title,
                            "content": leaf,
                        },
                    )
                    total_leaf += 1

        tx.execute(SQL_UPDATE, {"id_content": id_content})
        tx.commit()

