import torch
from transformers import AutoModelForQuestionAnswering, AutoTokenizer, pipeline

if __name__ == '__main__':
    # Tải mô hình và tokenizer PhoBERT
    model_name = "vinai/phobert-large"  # Thay vì vi-mrc-base
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForQuestionAnswering.from_pretrained(model_name)

    # Tạo pipeline để trả lời câu hỏi
    qa_pipeline = pipeline("question-answering", model=model, tokenizer=tokenizer)

    # Định nghĩa đoạn văn và câu hỏi
    context = """học bổng deloitte năm học 20232024 trường đại học công nghệ đhqghn univeristy of engineering and technology: 2 số lượng tổng giátrị và cơ cấu học bổng học bổng vietcombank năm học 20242025 trường đại học công nghệ đhqghn univeristy of engineering and technology: 4 hồsơ đăng ký học bổng học bổng vietcombank năm học 20232024 trường đại học công nghệ đhqghn univeristy of engineering and technology: 4 hồsơ đăng ký học bổng học bổng vietcombank năm học 20222023 trường đại học công nghệ đhqghn univeristy of engineering and technology: 4 hồsơ đăng ký học bổng học bổng bidv năm học 20242025 trường đại học công nghệ đhqghn univeristy of engineering and technology: 4 hồ sơ đăng ký học bổng."""

    question = "học bổng vietcombank"

    # Dự đoán câu trả lời
    result = qa_pipeline(question=question, context=context)

    # Hiển thị kết quả
    print(f"Câu trả lời: {result['answer']}")
    print(f"Độ tin cậy: {result['score']:.2f}")
