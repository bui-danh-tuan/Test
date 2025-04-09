from transformers import AutoTokenizer

text = """
'th2 18 cập nhật danh sách nộp hồ sơ trợ cấp xã hội học kỳ ii năm học 20242025 theo thông báo ngày 22012025 httpsuetvnueduvnnophonhantrocapxahoihockyiinamhoc20242025 hiện nay đã hết thời gian gian nộp hồ sơ tcxh hkii năm học 20242025 phòng ctsv trường đhcn xin cập nhật danh sách sinh viên đã nộp hồ sơ tính đến hết 8h ngày 18022024 đề nghị các sinh viên có tên trong danh sách kiểm tra thông tin đính kèm bởi tuyết nga chế độ chính sách chi tiết th2 18 cập nhật danh sách nộp hồ sơ hỗ trợ chi phí học tập học kỳ ii năm học 20242025 theo thông báo ngày 22012025 httpsuetvnueduvnnophohuongchinhsachhotrochiphihoctaphockiiinamhoc20242025 hiện nay đã hết thời gian gian nộp hồ sơ hỗ trợ chi phí học tập học kỳ ii năm học 20242025 phòng ctsv trường đhcn xin cập nhật danh sách sinh viên đính kèm đã nộp hồ sơ tính đến hết 8h ngày 18022024 đề nghị các sinh viên có bởi tuyết nga chế độ chính sách chi tiết th2 17 cập nhật danh sách nộp hồ sơ miễn giảm học phí học kỳ ii năm học 20242025'

"""
tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-large")

# Đếm số token
tokens = tokenizer.tokenize(text)
print(f"Số token: {len(tokens)}")
