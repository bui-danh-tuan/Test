from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

tokenizer = AutoTokenizer.from_pretrained("valhalla/t5-base-qg-hl")
model = AutoModelForSeq2SeqLM.from_pretrained("valhalla/t5-base-qg-hl")

text = "Hà Nội là thủ đô của Việt Nam."
highlighted_text = "generate question: <hl>Hà Nội<hl> là thủ đô của Việt Nam."

input_ids = tokenizer.encode(highlighted_text, return_tensors="pt")
output = model.generate(input_ids)
question = tokenizer.decode(output[0], skip_special_tokens=True)

print("Câu hỏi:", question)


# engine = create_engine("mysql+pymysql://root:root@localhost/chatbot")
# select_sql = text("SELECT * FROM uet_clear WHERE LENGTH(content_raw) > 5000 ORDER BY RAND() LIMIT 20")
# with engine.connect() as conn:
#     result = conn.execute(select_sql).fetchall()

# for row in result:
#     context = row.content_raw
#     result = generate_qas(context)
#     print(f"{row.id_url}|{result}")
