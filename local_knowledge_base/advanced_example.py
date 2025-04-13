from pathlib import Path
from document_loaders import DocumentProcessor
from vector_stores import VectorStoreManager

def demonstrate_document_loading():
    """演示不同类型文档的加载"""
    print("1. 演示文档加载功能")
    print("-" * 50)
    
    processor = DocumentProcessor()
    
    # 加载不同类型的文档
    documents = {
        "PDF文档": "docs/sample.pdf",
        "Markdown文档": "docs/sample.md",
        "Word文档": "docs/sample.docx",
        "文本文档": "docs/sample.txt"
    }
    
    for doc_type, path in documents.items():
        try:
            print(f"\n尝试加载{doc_type}...")
            docs = processor.load_document(path)
            print(f"成功！加载了 {len(docs)} 页/块内容")
        except FileNotFoundError:
            print(f"文件不存在：{path}")
        except Exception as e:
            print(f"加载失败：{str(e)}")

def demonstrate_text_splitting():
    """演示不同的文本分割方法"""
    print("\n2. 演示文本分割功能")
    print("-" * 50)
    
    processor = DocumentProcessor()
    
    # 使用不同的分割器
    splitter_configs = {
        "recursive": {
            "chunk_size": 1000,
            "chunk_overlap": 200
        },
        "character": {
            "separator": "\n\n",
            "chunk_size": 1000,
            "chunk_overlap": 200
        },
        "token": {
            "chunk_size": 500,
            "chunk_overlap": 50
        }
    }
    
    for splitter_type, config in splitter_configs.items():
        print(f"\n使用 {splitter_type} 分割器:")
        try:
            # 这里假设有一个示例PDF文件
            splits = processor.process_document(
                "docs/sample.pdf",
                splitter_type=splitter_type,
                **config
            )
            print(f"分割结果：{len(splits)} 个文档块")
        except FileNotFoundError:
            print("示例文件不存在")
        except Exception as e:
            print(f"分割失败：{str(e)}")

def demonstrate_vector_stores():
    """演示不同的向量存储和搜索方法"""
    print("\n3. 演示向量存储功能")
    print("-" * 50)
    
    processor = DocumentProcessor()
    vector_store = VectorStoreManager("./vector_stores")
    
    # 准备示例文档
    try:
        documents = processor.process_document(
            "docs/sample.pdf",
            splitter_type="recursive"
        )
        
        # 使用不同的向量存储
        store_types = ["chroma", "faiss"]
        for store_type in store_types:
            print(f"\n使用 {store_type} 向量存储:")
            try:
                # 创建向量存储
                vector_store.create_vector_store(
                    documents,
                    store_type=store_type
                )
                
                # 演示不同的搜索方法
                query = "这是一个示例查询"
                
                print("\n普通相似度搜索:")
                results = vector_store.similarity_search(query, k=2)
                print(f"找到 {len(results)} 个相关文档")
                
                print("\nMMR搜索（最大边际相关性）:")
                results = vector_store.similarity_search(
                    query,
                    k=2,
                    search_type="mmr"
                )
                print(f"找到 {len(results)} 个相关文档")
                
            except Exception as e:
                print(f"处理失败：{str(e)}")
                
    except FileNotFoundError:
        print("示例文件不存在")
    except Exception as e:
        print(f"处理失败：{str(e)}")

def main():
    """主函数"""
    print("LangChain 文档处理演示程序")
    print("=" * 50)
    
    # 创建示例文档目录
    Path("docs").mkdir(exist_ok=True)
    
    # 运行演示
    demonstrate_document_loading()
    demonstrate_text_splitting()
    demonstrate_vector_stores()

if __name__ == "__main__":
    main() 