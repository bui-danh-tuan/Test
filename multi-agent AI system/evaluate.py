import openai

# 🔐 Thay bằng OpenAI API Key của bạn
api_key = ""


client = openai.OpenAI(api_key=api_key)  # ← Thay API key thật

def generate_answer(context, question):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": "Bạn là trợ lý AI hãy tìm nội dung trên mạng về thông tin của trường đại học công nghệ và đại học quốc gia hà nội để đánh giá câu hỏi và câu trả lời sau. Hãy chấm điểm nó trên thang điểm 10"},
            {"role": "user", "content": f"Câu hỏi: {question}\nCâu trả lời: {context}"}
        ],
        temperature=0.2,
        max_tokens=256,
        top_p=0.9
    )

    return response.choices[0].message.content

# 🧪 Test
if __name__ == "__main__":
    context = r"""
Theo tài liệu hướng dẫn đăng ký học từ Trường Đại học Công nghệ - ĐHQGHN, **quy trình đăng ký học lại/học cải thiện** được thực hiện như sau:

1. **Điều kiện đăng ký**:
   - Sinh viên được đăng ký học lại/cải thiện nếu môn học có trong kế hoạch đào tạo của học kỳ đó.
   - Đối với học cải thiện, sinh viên chỉ được đăng ký tối đa **2 môn/học kỳ**.

2. **Các bước thực hiện**:
   - **Bước 1**: Đăng nhập hệ thống **UET-EDU** ([http://uet.vnu.edu.vn](http://uet.vnu.edu.vn)) bằng tài khoản sinh viên.
   - **Bước 2**: Vào mục **Đăng ký học** → Chọn **Đăng ký học lại/cải thiện**.
   - **Bước 3**: Chọn môn học cần đăng ký từ danh sách môn học được mở trong kỳ.
   - **Bước 4**: Xác nhận thông tin và hoàn tất đăng ký.

3. **Lưu ý**:
   - Thời gian đăng ký theo lịch nhà trường (thường công bố trên website).
   - Sinh viên tự kiểm tra lịch thi để tránh trùng lịch giữa các môn.
   - Nếu có vướng mắc, liên hệ **Phòng Đào tạo** để được hỗ trợ.

Chi tiết có thể xem tại [trang 4-5 của tài liệu](https://uet.vnu.edu.vn/wp-content/uploads/2018/11/H%C6%B0%E1%BB%9Bng-d%E1%BA%ABn-%C4%91%C4%83ng-k%C3%BD-h%E1%BB%8Dc.pdf).
"""

    question = " Quy trình đăng ký học lại/học cải thiện như thế nào?"

    answer = generate_answer(context, question)
    print("✅ Câu trả lời:\n", answer)