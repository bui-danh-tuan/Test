import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Lời nhắc hệ thống cho chatbot
system_prompt = (
    "Bạn là một trợ lí Tiếng Việt nhiệt tình và trung thực. Hãy luôn trả lời một cách hữu ích nhất có thể, đồng thời giữ an toàn.\n"
    "Câu trả lời của bạn không nên chứa bất kỳ nội dung gây hại, phân biệt chủng tộc, phân biệt giới tính, độc hại, nguy hiểm hoặc bất hợp pháp nào. "
    "Hãy đảm bảo rằng các câu trả lời của bạn không có thiên kiến xã hội và mang tính tích cực.\n"
    "Nếu một câu hỏi không có ý nghĩa hoặc không hợp lý về mặt thông tin, hãy giải thích tại sao thay vì trả lời một điều gì đó không chính xác. "
    "Nếu bạn không biết câu trả lời cho một câu hỏi, hãy trả lời là bạn không biết và vui lòng không chia sẻ thông tin sai lệch."
)

# Tải tokenizer và model
tokenizer = AutoTokenizer.from_pretrained('Viet-Mistral/Vistral-7B-Chat')
tokenizer.pad_token_id = tokenizer.eos_token_id  # Khắc phục cảnh báo pad_token_id


model = AutoModelForCausalLM.from_pretrained(
    'Viet-Mistral/Vistral-7B-Chat',
    torch_dtype=torch.bfloat16,  # Sử dụng float16 nếu dùng GPU V100
    device_map="auto",
    use_cache=True,
)
model.generation_config.pad_token_id = tokenizer.pad_token_id

# Bắt đầu hội thoại
conversation = [{"role": "system", "content": system_prompt}]

while True:
    human = input("Human: ")
    if human.lower() == "reset":
        conversation = [{"role": "system", "content": system_prompt}]
        print("Lịch sử cuộc trò chuyện đã được đặt lại.")
        continue

    conversation.append({"role": "user", "content": human})
    input_ids = tokenizer.apply_chat_template(conversation, return_tensors="pt").to(model.device)

    # attention_mask giúp mô hình nhận biết phần nào là input thực, phần nào là padding
    attention_mask = input_ids.ne(tokenizer.pad_token_id).to(model.device)

    # Sinh phản hồi
    out_ids = model.generate(
        input_ids=input_ids,
        attention_mask=attention_mask,
        max_new_tokens=768,
        do_sample=True,
        top_p=0.95,
        top_k=40,
        temperature=0.1,
        repetition_penalty=1.05,
    )

    assistant = tokenizer.batch_decode(out_ids[:, input_ids.size(1):], skip_special_tokens=True)[0].strip()
    print("Assistant:", assistant)
    conversation.append({"role": "assistant", "content": assistant})
