from typing import List, Union
from pathlib import Path
from langchain.document_loaders import (
    PyPDFLoader,
    UnstructuredMarkdownLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredWordDocumentLoader
)
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    TokenTextSplitter
)
from langchain.schema import Document

class DocumentProcessor:
    """文档处理器：支持多种格式的文档加载和切分"""
    
    def __init__(self):
        self.loaders = {
            '.pdf': PyPDFLoader,
            '.md': UnstructuredMarkdownLoader,
            '.docx': Docx2txtLoader,
            '.doc': UnstructuredWordDocumentLoader,
            '.txt': TextLoader
        }
        
    def get_splitter(self, splitter_type: str = "recursive", **kwargs):
        """
        获取文本分割器
        :param splitter_type: 分割器类型 ("recursive", "character", "token")
        :param kwargs: 分割器参数
        """
        splitters = {
            "recursive": RecursiveCharacterTextSplitter(
                chunk_size=kwargs.get("chunk_size", 1000),
                chunk_overlap=kwargs.get("chunk_overlap", 200),
                length_function=len,
            ),
            "character": CharacterTextSplitter(
                separator=kwargs.get("separator", "\n\n"),
                chunk_size=kwargs.get("chunk_size", 1000),
                chunk_overlap=kwargs.get("chunk_overlap", 200),
            ),
            "token": TokenTextSplitter(
                chunk_size=kwargs.get("chunk_size", 500),
                chunk_overlap=kwargs.get("chunk_overlap", 50),
            )
        }
        return splitters.get(splitter_type, splitters["recursive"])

    def load_document(self, file_path: Union[str, Path]) -> List[Document]:
        """
        加载文档
        :param file_path: 文档路径
        :return: 文档对象列表
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在：{file_path}")
            
        loader_class = self.loaders.get(file_path.suffix.lower())
        if not loader_class:
            raise ValueError(f"不支持的文件格式：{file_path.suffix}")
            
        loader = loader_class(str(file_path))
        return loader.load()
        
    def process_document(self, 
                        file_path: Union[str, Path],
                        splitter_type: str = "recursive",
                        **kwargs) -> List[Document]:
        """
        处理文档：加载并分割
        :param file_path: 文档路径
        :param splitter_type: 分割器类型
        :param kwargs: 分割器参数
        :return: 分割后的文档片段列表
        """
        # 加载文档
        documents = self.load_document(file_path)
        
        # 获取分割器
        splitter = self.get_splitter(splitter_type, **kwargs)
        
        # 分割文档
        splits = splitter.split_documents(documents)
        
        return splits

    def process_documents(self,
                         file_paths: List[Union[str, Path]],
                         splitter_type: str = "recursive",
                         **kwargs) -> List[Document]:
        """
        批量处理多个文档
        :param file_paths: 文档路径列表
        :param splitter_type: 分割器类型
        :param kwargs: 分割器参数
        :return: 所有文档的分割片段列表
        """
        all_splits = []
        for file_path in file_paths:
            splits = self.process_document(file_path, splitter_type, **kwargs)
            all_splits.extend(splits)
        return all_splits 
 