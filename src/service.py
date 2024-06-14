from langchain.prompts import Prompt
from agent import *


class Service():
    def __init__(self):
        self.agent = Agent()

    # 得到总结性的信息
    def get_summary_message(slef, message, history):
        # 1.model
        llm = get_llm_model()
        # 2.prompt
        prompt = Prompt.from_template(SUMMARY_PROMPT_TPL)
        # 3.chain
        llm_chain = LLMChain(llm=llm, prompt=prompt, verbose=os.getenv('VERBOSE'))
        chat_history = ''
        for q, a in history[-2:]:
            chat_history += f'问题:{q}, 答案:{a}\n'
        return llm_chain.invoke({'query': message, 'chat_history': chat_history})['text']

    def answer(self, message, history):
        if history:
            message = self.get_summary_message(message, history)
        return self.agent.query(message)
