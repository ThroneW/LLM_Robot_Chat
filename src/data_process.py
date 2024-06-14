from utils import *
import os

from glob import glob
from langchain.vectorstores.chroma import Chroma
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.document_loaders.pdf import PyMuPDFLoader
from langchain_community.document_loaders.text import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter


def doc2vec():
    # 定义文档分割器
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50
    )
    dir_path = '../data/inputs/'

    documents = []

    for file_path in glob(dir_path + '*.*'):
        loader = None
        if '.csv' in file_path:
            loader = CSVLoader(file_path, encoding='utf-8')
        if '.pdf' in file_path:
            loader = PyMuPDFLoader(file_path)
        if '.txt' in file_path:
            loader = TextLoader(file_path, encoding='utf-8')
        if loader:
            documents += loader.load_and_split(text_splitter)

    # 文本进行向量化并存储
    if documents:
        vdb = Chroma.from_documents(
            documents=documents,
            embedding=get_embeddings_model(),
            persist_directory='../data/db/'
        )
        vdb.persist()


if __name__ == '__main__':
    doc2vec()
