from typing import List, Optional, Dict, Any
import os
from pathlib import Path
from langchain.vectorstores import Chroma, FAISS
from langchain.embeddings.base import Embeddings
from langchain.embeddings import (
    HuggingFaceEmbeddings,
    OpenAIEmbeddings,
    CohereEmbeddings
)
from langchain.schema import Document

class VectorStoreManager:
    """向量存储管理器：支持多种向量存储和嵌入模型"""
    
    def __init__(self, persist_directory: str = "./vector_store"):
        self.persist_directory = persist_directory
        self._embeddings = None
        self._vector_store = None
        
    def get_embeddings(self, embedding_type: str = "huggingface", **kwargs) -> Embeddings:
        """
        获取嵌入模型
        :param embedding_type: 嵌入模型类型 ("huggingface", "openai", "cohere")
        :param kwargs: 模型参数
        """
        embeddings = {
            "huggingface": HuggingFaceEmbeddings(
                model_name=kwargs.get("model_name", "sentence-transformers/all-MiniLM-L6-v2")
            ),
            "openai": OpenAIEmbeddings(
                api_key=kwargs.get("api_key"),
            ),
            "cohere": CohereEmbeddings(
                api_key=kwargs.get("api_key"),
            )
        }
        return embeddings.get(embedding_type, embeddings["huggingface"])
        
    def create_vector_store(self,
                          documents: List[Document],
                          store_type: str = "chroma",
                          embedding_type: str = "huggingface",
                          **kwargs) -> None:
        """
        创建向量存储
        :param documents: 文档列表
        :param store_type: 存储类型 ("chroma", "faiss")
        :param embedding_type: 嵌入模型类型
        :param kwargs: 额外参数
        """
        # 获取嵌入模型
        self._embeddings = self.get_embeddings(embedding_type, **kwargs)
        
        # 确保存储目录存在
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # 创建向量存储
        if store_type == "chroma":
            self._vector_store = Chroma.from_documents(
                documents=documents,
                embedding=self._embeddings,
                persist_directory=self.persist_directory
            )
            self._vector_store.persist()
        elif store_type == "faiss":
            self._vector_store = FAISS.from_documents(
                documents=documents,
                embedding=self._embeddings
            )
            # 保存FAISS索引
            self._vector_store.save_local(self.persist_directory)
            
    def load_vector_store(self,
                         store_type: str = "chroma",
                         embedding_type: str = "huggingface",
                         **kwargs) -> None:
        """
        加载已存在的向量存储
        :param store_type: 存储类型
        :param embedding_type: 嵌入模型类型
        :param kwargs: 额外参数
        """
        if not os.path.exists(self.persist_directory):
            raise FileNotFoundError(f"向量存储目录不存在：{self.persist_directory}")
            
        # 获取嵌入模型
        self._embeddings = self.get_embeddings(embedding_type, **kwargs)
        
        # 加载向量存储
        if store_type == "chroma":
            self._vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self._embeddings
            )
        elif store_type == "faiss":
            self._vector_store = FAISS.load_local(
                self.persist_directory,
                self._embeddings
            )
            
    def similarity_search(self,
                         query: str,
                         k: int = 3,
                         search_type: str = "similarity",
                         **kwargs) -> List[Document]:
        """
        执行相似度搜索
        :param query: 查询文本
        :param k: 返回结果数量
        :param search_type: 搜索类型 ("similarity", "mmr")
        :param kwargs: 搜索参数
        :return: 相关文档列表
        """
        if not self._vector_store:
            raise ValueError("请先创建或加载向量存储")
            
        if search_type == "similarity":
            return self._vector_store.similarity_search(query, k=k)
        elif search_type == "mmr":
            return self._vector_store.max_marginal_relevance_search(
                query,
                k=k,
                fetch_k=kwargs.get("fetch_k", 10),
                lambda_mult=kwargs.get("lambda_mult", 0.5)
            )
        else:
            raise ValueError(f"不支持的搜索类型：{search_type}")
            
    def get_relevant_documents(self, query: str, **kwargs) -> List[Document]:
        """
        获取相关文档（别名方法）
        """
        return self.similarity_search(query, **kwargs) 