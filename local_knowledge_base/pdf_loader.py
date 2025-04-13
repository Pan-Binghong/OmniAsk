from typing import List
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

class PDFDocumentProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
        )

    def load_and_split(self, pdf_path: str) -> List:
        """
        加载PDF文件并将其分割成小块
        :param pdf_path: PDF文件的路径
        :return: 分割后的文档块列表
        """
        # 加载PDF文件
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        
        # 分割文档
        splits = self.text_splitter.split_documents(pages)
        
        return splits 