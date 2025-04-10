from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer
from bert_score import score

def bleu_score(pred, ref):
    return sentence_bleu(
        [ref.split()],
        pred.split(),
        smoothing_function=SmoothingFunction().method1
    )

def rouge_l(pred, ref):
    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    score_ = scorer.score(ref, pred)
    return score_['rougeL'].fmeasure

def bertscore_f1(pred, ref):
    _, _, f1 = score([pred], [ref], lang="vi", model_type="vinai/phobert-large")
    return f1[0].item()

def evaluate_text_generation(prediction, ground_truth):
    return {
        "BLEU": round(bleu_score(prediction, ground_truth), 4),
        "ROUGE-L": round(rouge_l(prediction, ground_truth), 4),
        "BERTScore": round(bertscore_f1(prediction, ground_truth), 4)
    }

pred = "Trường bắt đầu nhận hồ sơ xét tuyển từ 1/6 đến 15/7."
truth = "Thời gian nhận hồ sơ là từ ngày 1/6 đến hết ngày 15/7."

result = evaluate_text_generation(pred, truth)
print(result)
