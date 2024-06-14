from langchain.memory import ConversationBufferMemory
from langchain.vectorstores.chroma import Chroma
from langchain.vectorstores.faiss import FAISS
from langchain.prompts import PromptTemplate
from langchain.chains.llm import LLMChain
from langchain.chains.llm_requests import LLMRequestsChain
from langchain import hub
from langchain.agents import create_react_agent, AgentExecutor

from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_core.documents import Document
from langchain_core.tools import Tool

from utils import *
from prompt import *
from config import *


class Agent():
    def __init__(self):
        self.vdb = Chroma(
            persist_directory='../data/db',
            embedding_function=get_embeddings_model()
        )

    # 定义通用聊天功能
    def generic_func(self, query):
        # prompt
        prompt = PromptTemplate.from_template(GENERIC_PROMPT_TPL)
        # chains
        llm_chain = LLMChain(
            llm=get_llm_model(),
            prompt=prompt,
            verbose=os.getenv('VERBOSE'),
        )
        return llm_chain.invoke(query)['text']

    def retrival_func(self, query):
        # 召回并过滤相似文档
        documents = self.vdb.similarity_search_with_relevance_scores(query, k=5)
        query_result = [doc[0].page_content for doc in documents if doc[1] > 0.7]
        # prompt
        prompt = PromptTemplate.from_template(RETRIVAL_PROMPT_TPL)
        # chain
        retrival_chain = LLMChain(
            llm=get_llm_model(),
            prompt=prompt,
            verbose=os.getenv('VERBOSE')
        )
        inputs = {
            'query': query,
            'query_result': '\n\n'.join(query_result) if len(query_result) else '没有查到'
        }
        return retrival_chain.invoke(inputs)['text']

    def graph_func(self, query):
        response_schemas = [
            ResponseSchema(type='list', name='disease', description='疾病名称实体'),
            ResponseSchema(type='list', name='symptom', description='疾病症状实体'),
            ResponseSchema(type='list', name='drug', description='药物名称实体')
        ]

        output_parser = StructuredOutputParser(response_schemas=response_schemas)
        format_instructions = structured_output_parser(response_schemas)

        ner_prompt = PromptTemplate(
            template=NER_PROMPT_TPL,
            partial_variables={'format_instructions': format_instructions},
            input_variables=['query']
        )

        ner_chain = LLMChain(
            llm=get_llm_model(),
            prompt=ner_prompt,
            verbose=os.getenv('VERBOSE')
        )

        result = ner_chain.invoke({
            'query': query
        })['text']

        print(f"result-->{result}")

        ner_result = output_parser.parse(result)
        graph_templates = []
        for key, template in GRAPH_TEMPLATE.items():
            slot = template['slots'][0]
            slot_values = ner_result[slot]
            for value in slot_values:
                graph_templates.append({
                    'question': replace_token_in_string(template['question'], [[slot, value]]),
                    'cypher': replace_token_in_string(template['cypher'], [[slot, value]]),
                    'answer': replace_token_in_string(template['answer'], [[slot, value]]),
                })
        if not graph_templates:
            return

        graph_documents = [
            Document(page_content=template['question'], metadata=template)
            for template in graph_templates
        ]

        db = FAISS.from_documents(graph_documents, get_embeddings_model())

        graph_documents_filter = db.similarity_search_with_relevance_scores(query, k=3)

        query_result = []
        neo4j_conn = get_neo4j_conn()  # 连接neo4j数据库
        for document in graph_documents_filter:
            question = document[0].page_content
            cypher = document[0].metadata['cypher']
            answer = document[0].metadata['answer']
            try:
                result = neo4j_conn.run(cypher).data()  # neo4j运行cypher，然后拿到其中的结果
                if result and any(value for value in
                                  result[0].values()):
                    answer_str = replace_token_in_string(answer, list(result[0].items()))
                    query_result.append(f'问题：{question}\n答案：{answer_str}')
            except:
                pass

            prompt = PromptTemplate.from_template(GRAPH_PROMPT_TPL)

            graph_chain = LLMChain(
                llm=get_llm_model(),
                prompt=prompt,
                verbose=os.getenv('VERBOSE')
            )
            inputs = {
                'query': query,
                'query_result': '\n\n'.join(query_result) if len(query_result) else '没有查到'
            }
            return graph_chain.invoke(inputs)['text']

    # 用于搜索
    def search_func(self, query):
        # prompt
        prompt = PromptTemplate.from_template(SEARCH_PROMPT_TPL)
        llm_chain = LLMChain(
            llm=get_llm_model(),
            prompt=prompt,
            verbose=os.getenv('VERBOSE')
        )
        llm_request_chain = LLMRequestsChain(
            llm_chain=llm_chain,
            requests_key='query_result'
        )
        inputs = {
            'query': query,
            'url': 'https://www.google.com/search?q=' + query.replace(' ', '+')
        }
        search_result = llm_request_chain.invoke(inputs)['output']
        return search_result

    def query(self, query):
        # 定义tools
        tools = [
            Tool.from_function(
                name='generic_func',
                # func=lambda x: self.generic_func(x, query),
                func=self.generic_func,
                description='可以解答通用领域的知识，例如打招呼，问你是谁等问题',
            ),
            Tool.from_function(
                name='retrival_func',
                # func=lambda x: self.retrival_func(x, query),
                func=self.retrival_func,
                description='用于回答寻医问药网相关问题',
            ),
            Tool(
                name='graph_func',
                # func=lambda x: self.graph_func(x, query),
                func=self.graph_func,
                description='用于回答疾病、症状、药物等医疗相关问题',
            ),
            Tool(
                name='search_func',
                func=self.search_func,
                description='其他工具没有正确答案时，通过搜索引擎，回答通用类问题',
            )
        ]
        # prompt:这个是在langchainhub上用的别人写好的提示词
        prompt = hub.pull('hwchase17/react-chat')
        # 给原来的prompt添加上下面这部分的信息
        prompt.template = '请用中文回答问题！Final Answer 必须尊重 Obversion 的结果，不能改变语义。\n\n' + prompt.template
        # agent
        agent = create_react_agent(llm=get_llm_model(), tools=tools, prompt=prompt)
        # memory
        memory = ConversationBufferMemory(memory_key='chat_history')

        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=tools,
            memory=memory,
            handle_parsing_errors=True,
            verbose=os.getenv('VERBOSE')
        )
        return agent_executor.invoke({"input": query})['output']
