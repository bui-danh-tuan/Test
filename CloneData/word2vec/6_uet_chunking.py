from sqlalchemy import create_engine, text
import torch
from transformers import AutoTokenizer, AutoModel

# Kết nối database bằng SQLAlchemy
username = "root"
password = "root"
host = "localhost"
database = "chatbot"
engine = create_engine(f"mysql+pymysql://{username}:{password}@{host}/{database}")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_name = "vinai/phobert-large"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name).to(device)

# Hàm chia văn bản thành các đoạn nhỏ (chunk) có độ dài tối đa 256 token, chồng lấn 30 token
def split_text_overlap(text, max_len=256, overlap=30):
    tokens = tokenizer.tokenize(text)
    chunks = []

    if len(tokens) <= overlap:
        return []

    start = 0
    while start < len(tokens):
        end = min(start + max_len, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = tokenizer.convert_tokens_to_string(chunk_tokens)
        chunks.append(chunk_text)

        if end == len(tokens):
            break
        start = end - overlap  # chồng lấn 30 token với đoạn trước

    return chunks

def process_and_insert_chunks():
    with engine.connect() as conn:
        results = conn.execute(text("SELECT id, title, content_raw FROM uet_clear")).fetchall()
        len_result = len(results)
        count = 0
        for row in results:
            id_clear = row[0]
            title = row[1]
            content_raw = row[2]

            chunks = split_text_overlap(content_raw)

            for chunk in chunks:
                insert_sql = text("""
                    INSERT INTO uet_chunking (id_clear, title, content)
                    VALUES (:id_clear, :title, :content)
                """)
                conn.execute(insert_sql, {
                    "id_clear": id_clear,
                    "title": title,
                    "content": chunk
                })

            update_sql = text("UPDATE uet_clear SET chunking = 1 WHERE id = :id_clear")
            conn.execute(update_sql, {"id_clear": id_clear})
            conn.commit()

            count += 1
            print(f"{count}/{len_result}")

# process_and_insert_chunks()
# Gọi hàm xử lý
chunks = split_text_overlap("""
Kỹ thuật MEMS và NEMS (các hệ thống vi cơ điện tử) là một trong những học phần nằm trong chương trình thạc sĩ Kỹ thuật điện tử chuyên ngành bán dẫn và vi mạch, triển khai cho lớp học viên trong chương trình VNU-Samsung Technology Track (V-STT) hợp tác Giáo sư Đại học California giảng dạy về Kỹ thuật MEMS và NEMS cho học viên chương trình VNU-Samsung Technology Track Bắt đầu End Kỹ thuật MEMS và NEMS (các hệ thống vi cơ điện tử) là một trong những học phần nằm trong chương trình thạc sĩ Kỹ thuật điện tử chuyên ngành bán dẫn và vi mạch, triển khai cho lớp học viên trong chương trình VNU-Samsung Technology Track (V-STT) hợp tác giữa Trường Đại học Công nghệ, Đại học Quốc gia Hà Nội (VNU-UET) và Samsung Electronics Hàn Quốc được giảng dạy bởi GS. Cao Việt Hùng đến từ Trường Kỹ thuật Samueli, Đại học California (Hoa Kỳ) từ ngày 6/1-17/1/2025. Môn học Kỹ thuật MEMS và NEMS cung cấp các kiến thức cơ bản về các hệ thống vi cơ điện tử (MEMS), bao gồm các hệ vi chấp hành, vi cảm biến và vi động cơ, nguyên lý hoạt động, các kỹ thuật chế tạo hệ vi cơ khác nhau (vi gia công bề mặt và vi gia công khối), các kỹ thuật chế tạo vi mạch, công nghệ màng mỏng áp dụng cho MEMS. Công nghệ nano cũng sẽ được đề cập trong môn học này. Các ví dụ sẽ được trình bày, tập trung vào các thiết bị và hệ thống y sinh. Học viên sẽ học được các khái niệm cũng như có khả năng thiết kế các thiết bị và hệ thống vi cơ điện tử. Chia sẻ về chi tiết nội dung môn học này, GS. Cao Việt Hùng cho biết, môn học này bao gồm kiến thức ở nhiều lĩnh vực, đầu tiên các học viên sẽ học được chu trình về sản xuất các hệ thống bán dẫn, việc thiết kế và thiết lập các hệ thống MEMS có thể làm cảm biến và hệ thống vi cơ khí. Cuối cùng học viên được học thêm các ứng dụng hệ thống NEMS trong thiết bị y tế, viễn thông và các lĩnh vực khác. PGS.TS Bùi Thanh Tùng – Phó Chủ nhiệm khoa Điện tử viễn thông, Trường ĐH Công nghệ (bên trái ảnh) đón tiếp GS. Cao Việt Hùng Sau hai tuần giảng dạy về môn học, bên cạnh bài tập và thuyết trình học viên sẽ phải thực hiện báo cáo dự án chiếm 50% trong kế hoạch đánh giá môn học. Đây là phần được GS. Cao Việt Hùng đánh giá như một bài thi cuối kỳ và là phần thú vị nhất của môn học, bởi vì học viên sẽ chủ động nghiên cứu các vấn đề bản thân quan tâm trong lĩnh vực bán dẫn và đưa ra giải pháp giải quyết vấn đề. “ Phương pháp học tập này giúp học viên chủ động trong việc nghiên cứu và học tập, từ đó thay đổi nhận thức để học viên có những phát kiến đột phá mới. Và trong buổi báo cáo dự án này, tôi ngạc nhiên khi thấy học viên đưa ra những quan điểm về các vấn đề mà hiện nay cũng đang là thách thức của thế giới trong lĩnh vực bán dẫn. Điều đó cho thấy các em đã có những ý tưởng và có những tư duy giải quyết vấn đề thực tiễn. Dựa vào kết quả báo cáo này, tôi mong rằng những kết quả này sẽ trở thành những bài báo chất lượng và được ứng dụng vào thực tiễn trong thời gian tới ” – GS. Cao Việt Hùng chia sẻ. Trong quá trình giảng dạy, Giáo sư đánh giá cao sự ham học hỏi, tinh thần cởi mở và tích cực từ các học viên. Điều này đã khiến cho Giáo sư có thêm động lực và niềm vui khi “truyền lửa” thêm các kiến thức mới cho học viên về các công nghệ tiên tiến trên thế giới. Học viên khóa I chương trình V-STT thực hiện báo cáo dự án sau khi tham gia môn học Kỹ thuật MEMS và NEMS Nhận định về những lợi ích của chương trình V-STT, Giáo sư khẳng định, chương trình là cơ hội vàng cho các sinh viên ưu tú theo đuổi về lĩnh vực bán dẫn với cơ hội làm việc trong Tập đoàn Samsung Hàn Quốc và xa hơn nữa là những người dẫn dắt con đường bán dẫn của Việt Nam trong tương lai. Hiếm có chương trình đào tạo nào trên thế giới mà học viên sau khi tốt nghiệp được tuyển dụng vào làm việc ngay cho một tập đoàn điện tử lớn như Samsung. Hơn nữa, lĩnh vực bán dẫn ngày nay đang được đầu tư và quan tâm trên thế giới và ở Việt Nam lĩnh vực này cũng được đẩy mạnh, nên chương trình V-STT có đủ yếu tố để phát triển lâu dài và góp phần thổi bùng “ngọn lửa to” tham gia đóng góp vào việc xây dựng lĩnh vực bán dẫn của nước nhà. Ngoài ra, những học viên của chương trình được lựa chọn kỹ càng bởi từ những sinh viên xuất sắc, tương lai không xa sẽ trở thành những nhân tài tham gia nghiên cứu, đầu tư tài nguyên hơn nữa. Vì thế, các em nên tiếp tục nâng cao và trau dồi ngoại ngữ, là những chuyên gia công nghệ nên có thái độ mở và lấy mục tiêu học tập suốt đời để trở thành những người dẫn dắt các chương trình lớn hơn ở Việt Nam. Sau khi tham gia môn học Kỹ thuật MEMS và NEMS cùng một số bài giảng được trình bày bởi các giáo sư và kỹ sư quốc tế, học viên Trần Ngọc Vinh – khóa I chương trình V-STT đã có thêm động lực nghiên cứu và kiến thức chuyên môn về bán dẫn. Ngọc Vinh cho biết, chúng em được cung cấp kiến thức liên quan đến gia công, chế tạo cấp độ micro&nano để hiểu biết thêm về nền tảng công nghệ mà ngành bán dẫn đang sử dụng. Đồng thời, phương pháp giảng dạy của Giáo sư giúp chúng em mở rộng suy nghĩ, nhận thức về nghiên cứu, học tập. Những kiến thức thầy truyền thụ gắn liền với những thí nghiệm thực tế đời thường giúp chúng em thấy thú vị và nhận ra khoa học là những thứ gần gũi, bình dị trong cuộc sống và mở ra những góc nhìn mới cho chúng em. Học viên Trần Ngọc Vinh – khóa I chương trình V-STT, báo cáo dự án sau khi tham gia môn học Kỹ thuật MEMS và NEMS Với những lợi thế về môi trường quốc tế, chương trình V-STT khóa II đã khởi động với kế hoạch tuyển sinh khóa 2025 với thời gian mở đơn đến 31/3/2025, dành cho sinh viên đã tốt nghiệp (trong vòng 3 năm), sinh viên năm cuối các chương trình liên quan đến lĩnh vực bán dẫn và vi mạch; thành tích học tập: GPA ≥3.3/4.0; phỏng vấn (bằng tiếng Anh) bởi đại diện Samsung Electronics. Thông tin liên hệ tuyển sinh hotline: 0984789794 và email: Link nộp hồ sơ ứng tuyển: Giáo sư Cao Việt Hùng (Hung Cao) nhận bằng Kỹ sư ngành điện tử và viễn thông Trường Đại học Bách khoa Hà Nội, Việt Nam vào năm 2003. Sau đó, ông giảng dạy tại Trường Đại học Hàng hải Việt Nam từ năm 2003 đến 2005. Ông tiếp tục nhận bằng Thạc sĩ và Tiến sĩ ngành kỹ thuật điện tại Đại học Texas ở Arlington lần lượt vào các năm 2007 và 2012. Sau nghiên cứu tiến sĩ về cảm biến sinh học và điện tử sinh học, ông Cao đã được đào tạo về kỹ thuật sinh học và y học tại Đại học Nam California (2012-2013) và Đại học California, Los Angeles (2013-2014). Trong giai đoạn 2014-2015, ông làm việc tại ETS, Montreal, QC, Canada với vai trò giảng viên nghiên cứu. Vào mùa thu năm 2015, ông Cao trở thành trợ lý giáo sư ngành kỹ thuật điện/điện tử y sinh tại Đại học Washington (UW). Đến tháng 9/2018, ông gia nhập Khoa Kỹ thuật Điện và Khoa học Máy tính của Đại học California, Irvine. Phòng thí nghiệm HERO của ông tập trung vào các ứng dụng của vi cảm biến sinh học và điện tử sinh học trong giám sát sức khỏe con người cũng như nghiên cứu sinh học trên các mô hình động vật. Ông Cao là một trong những người tiên phong sử dụng vi điện tử linh hoạt để nghiên cứu bệnh tim trên cá ngựa vằn. Ông đã nhận được Giải thưởng RRF của Đại học Washington (2016), Giải thưởng NSF CAREER (2017) và là một trong hai ứng viên duy nhất của UW tranh giải Moore’s Inventor Fellowship danh giá (2017). Các hướng nghiên cứu: MEMS, sensors, implants, heart disease, neurological disease, wireless biomedical systems.
""")

[print(c, end="\n---------\n") for c in chunks]
