import os

from transformers import GPT2LMHeadModel
from transformers import BertTokenizerFast
import torch.nn.functional as F
from parameter_config import *

PAD = '[PAD]'
pad_id = 0

pconf = ParameterConfig()

device = 'cuda' if torch.cuda.is_available() else 'cpu'
print('using device:{}'.format(device))
os.environ["CUDA_VISIBLE_DEVICES"] = '0'
tokenizer = BertTokenizerFast(vocab_file=pconf.vocab_path,
                              sep_token="[SEP]",
                              pad_token="[PAD]",
                              cls_token="[CLS]")
model = GPT2LMHeadModel.from_pretrained('../save_model/epoch97')
model = model.to(device)
model.eval()


def top_k_top_p_filtering(logits, top_k=0, filter_value=-float('Inf')):
    assert logits.dim() == 1
    top_k = min(top_k, logits.size(-1))

    if top_k > 0:
        indices_to_remove = logits < torch.topk(logits, top_k)[0][..., -1, None]
        logits[indices_to_remove] = filter_value
    return logits


def model_predict(text):
    history = []
    text_ids = tokenizer.encode(text, add_special_tokens=False)
    history.append(text_ids)
    input_ids = [tokenizer.cls_token_id]
    for history_id, history_utr in enumerate(history[-pconf.max_history_len:]):
        input_ids.extend(history_utr)
        input_ids.append(tokenizer.sep_token_id)
    input_ids = torch.tensor(input_ids).long().to(device)
    input_ids = input_ids.unsqueeze(0)
    response = []
    for _ in range(pconf.max_len):
        outputs = model(input_ids=input_ids)
        logits = outputs.logits
        next_token_logits = logits[0, -1, :]
        for id in set(response):
            next_token_logits[id] /= pconf.repetition_penalty
        next_token_logits[tokenizer.convert_tokens_to_ids('[UNK]')] = -float('Inf')
        filtered_logits = top_k_top_p_filtering(next_token_logits, top_k=pconf.topk)
        next_token = torch.multinomial(F.softmax(filtered_logits, dim=-1), num_samples=1)
        if next_token == tokenizer.sep_token_id:
            break
        response.append(next_token.item())
        input_ids = torch.cat((input_ids, next_token.unsqueeze(0)), dim=1)
    history.append(response)
    text = tokenizer.convert_ids_to_tokens(response)
    return "".join(text)
