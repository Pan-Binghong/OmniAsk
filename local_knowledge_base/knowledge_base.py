import os
from typing import List, Optional
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from pdf_loader import PDFDocumentProcessor

class LocalKnowledgeBase:
    def __init__(self, persist_directory: str = "./knowledge_base"):
        """
        初始化本地知识库
        :param persist_directory: 知识库持久化存储的目录
        """
        self.persist_directory = persist_directory
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.vector_store = None
        
    def create_knowledge_base(self, pdf_path: str) -> None:
        """
        从PDF文件创建知识库
        :param pdf_path: PDF文件路径
        """
        # 确保存储目录存在
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # 加载和处理PDF文件
        processor = PDFDocumentProcessor()
        documents = processor.load_and_split(pdf_path)
        
        # 创建向量存储
        self.vector_store = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        self.vector_store.persist()
        
    def load_existing_knowledge_base(self) -> None:
        """
        加载已存在的知识库
        """
        if not os.path.exists(self.persist_directory):
            raise FileNotFoundError("知识库目录不存在")
            
        self.vector_store = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )
        
    def search(self, query: str, k: int = 3) -> List[str]:
        """
        搜索知识库
        :param query: 查询文本
        :param k: 返回的相似文档数量
        :return: 相似文档列表
        """
        if not self.vector_store:
            raise ValueError("请先创建或加载知识库")
            
        results = self.vector_store.similarity_search(query, k=k)
        return [doc.page_content for doc in results] 