
import json
import re

from transformers import AutoTokenizer, AutoModel
from rich import print
from rich.console import Console

class_examples = {
    '新闻报道': '今日，股市经历了一轮震荡，受到宏观经济数据和全球贸易紧张局势的影响。投资者密切关注美联储可能的政策调整，以适应市场的不确定性。',
    '财务报告': '本公司年度财务报告显示，去年公司实现了稳步增长的盈利，同时资产负债表呈现强劲的状况。经济环境的稳定和管理层的有效战略执行为公司的健康发展奠定了基础。',
    '公司公告': '本公司高兴地宣布成功完成最新一轮并购交易，收购了一家在人工智能领域领先的公司。这一战略举措将有助于扩大我们的业务领域，提高市场竞争力',
    '分析师报告': '最新的行业分析报告指出，科技公司的创新将成为未来增长的主要推动力。云计算、人工智能和数字化转型被认为是引领行业发展的关键因素，投资者应关注这些趋势'}

schema = {
    '金融': ['日期', '股票名称', '开盘价', '收盘价', '成交量'],
}

IE_PATTERN = "{}\n\n提取上述句子中{}的实体，并按照JSON格式输出，上述句子中不存在的信息用['原文中未提及']来表示，多个值之间用','分隔。"

ie_examples = {
    '金融': [
        {
            'content': '2023-01-10，股市震荡。股票古哥-D[EOOE]美股今日开盘价100美元，一度飙升至105美元，随后回落至98美元，最终以102美元收盘，成交量达到520000。',
            'answers': {
                '日期': ['2023-01-10'],
                '股票名称': ['古哥-D[EOOE]美股'],
                '开盘价': ['100美元'],
                '收盘价': ['102美元'],
                '成交量': ['520000'],
            }
        }
    ]
}

examples = {
    '是': [
        ('公司ABC发布了季度财报，显示盈利增长。', '财报披露，公司ABC利润上升。'),
    ],
    '不是': [
        ('黄金价格下跌，投资者抛售。', '外汇市场交易额创下新高。'),
        ('央行降息，刺激经济增长。', '新能源技术的创新。')
    ]
}


class ServiceFinance:
    def __init__(self):

        self.console = Console()

        self.device = 'cuda:0'

        self.tokenizer = AutoTokenizer.from_pretrained("../model/ChatGLM-6B/THUDM/chatglm-6b-int4",
                                                       trust_remote_code=True)
        # tokenizer = AutoTokenizer.from_pretrained("../ChatGLM-6B/THUDM/chatglm-6b",
        #                                           trust_remote_code=True)
        # 加载预训练模型
        self.model = AutoModel.from_pretrained("../model/ChatGLM-6B/THUDM/chatglm-6b",
                                               trust_remote_code=True).half().cuda()
        # self.model = AutoModel.from_pretrained("../model/ChatGLM-6B/THUDM/chatglm-6b-int4",
        #                                        trust_remote_code=True).float()
        # 把模型送到gpu上
        self.model.to(self.device)

    """
    文本分类
    """

    def init_classify_prompts(self):

        class_list = list(class_examples.keys())

        pre_history = [
            (f'现在你是一个文本分类器，你需要按照要求将我给你的句子分类到：{class_list}类别中。',
             f'好的。')
        ]

        for _type, example in class_examples.items():
            pre_history.append((f'"{example}"是{class_list}里的什么类别', _type))

        return {"class_list": class_list, "pre_history": pre_history}

    def classify_inference(self, sentences: list,
                           custom_settings: dict):

        for sentence in sentences:
            with self.console.status("[bold bright_green] Model Inference..."):
                sentence_prompt = f'"{sentence}"是{custom_settings["class_list"]}里的什么类别？'

                response, history = self.model.chat(self.tokenizer, sentence_prompt,
                                                    history=custom_settings['pre_history'])
            print(f'>>>[bold bright_red]sentence:{sentence}')
            print(f'>>>[bold bright_green]inference answer:{response}')
            return response

    def answer_classify(self, message, history):
        print("message=", message)
        custom_settings = self.init_classify_prompts()
        response = self.classify_inference([message], custom_settings)
        return response

    """
        实体关系抽取
    """

    def init_ie_prompts(self):

        ie_pre_history = [
            (
                "现在你需要帮助我完成信息抽取任务，当我给你一个句子时，你需要帮我抽取出句子中实体信息，并按照JSON的格式输出，上述句子中没有的信息用['原文中未提及']来表示，多个值之间用','分隔。注意：请严格遵守规则，不要推理。",
                '好的，请输入您的句子。'
            )
        ]

        for _type, example_list in ie_examples.items():
            for example in example_list:
                sentence = example['content']

                properties_str = ', '.join(schema[_type])

                schema_str_list = f'"{_type}"({properties_str})'

                sentence_with_prompt = IE_PATTERN.format(sentence, schema_str_list)

                ie_pre_history.append(
                    (f"{sentence_with_prompt}", f"{json.dumps(example['answers'], ensure_ascii=False)}"))

        return {"ie_pre_history": ie_pre_history}

    def clean_response(self, response: str):

        if '```json' in response:
            res = re.findall(r'```json(.*?)```', response)
            if len(res) and res[0]:
                response = res[0]
            response = response.replace('、', ',')
        try:

            return json.loads(response)
        except:
            return response

    def ie_inference(self, sentences: list, custom_settings: dict):

        for sentence in sentences:
            cls_res = '金融'
            if cls_res not in schema:
                print(f'The type model inferenced {cls_res} which is not in schema dict, exited.')
                exit()
            properties_str = ', '.join(schema[cls_res])

            schema_str_list = f'"{cls_res}"({properties_str})'

            sentence_with_ie_prompt = IE_PATTERN.format(sentence, schema_str_list)

            ie_res, history = self.model.chat(self.tokenizer,
                                              sentence_with_ie_prompt,
                                              history=custom_settings["ie_pre_history"])

            ie_res = self.clean_response(ie_res)

            print(f'>>> [bold bright_red]sentence: {sentence}')
            print(f'>>> [bold bright_green]inference answer:{ie_res} ')

            ie_str = str(ie_res)
            return ie_str

    def answer_ie(self, message, history):
        print("message=", message)
        custom_settings = self.init_ie_prompts()
        response = self.ie_inference([message], custom_settings)
        return response

    """
       文本匹配
    """

    def init_text_matching_prompts(self):

        pre_history = [
            (
                '现在你需要帮助我完成文本匹配任务，当我给你两个句子时，你需要回答我这两句话语义是否相似。只需要回答是否相似，不要做多余的回答。',
                '好的，我将只回答”是“或”不是“。'
            )
        ]

        for key, sentence_pairs in examples.items():
            for sentence_pair in sentence_pairs:
                sentence1, sentence2 = sentence_pair
                pre_history.append((f'句子一:{sentence1}\n句子二:{sentence2}\n上面两句话是相似的语义吗？', key))
        return {"pre_history": pre_history}

    def text_matching_inference(self, sentence_pairs: list, custom_settings: dict):

        for sentence_pair in sentence_pairs:
            sentence1, sentence2 = sentence_pair
            sentence_with_prompt = f'句子一: {sentence1}\n句子二: {sentence2}\n上面两句话是相似的语义吗？'
            response, history = self.model.chat(self.tokenizer, sentence_with_prompt,
                                                history=custom_settings['pre_history'])
            print(f'>>> [bold bright_red]sentence: {sentence_pair}')
            print(f'>>> [bold bright_green]inference answer: {response}')
            return response

    def answer_text_matching(self, message, history):
        print("message=", message)
        custom_settings = self.init_text_matching_prompts()
        message = message.split('|')
        message = tuple(message)
        response = self.text_matching_inference([message], custom_settings)
        return response
