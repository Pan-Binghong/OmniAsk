from knowledge_base import LocalKnowledgeBase

def main():
    # 初始化知识库
    kb = LocalKnowledgeBase()
    
    # 创建新的知识库
    pdf_path = "your_pdf_file.pdf"  # 替换为实际的PDF文件路径
    kb.create_knowledge_base(pdf_path)
    
    # 进行搜索
    query = "在这里输入您的问题"
    results = kb.search(query)
    
    # 打印结果
    print("搜索结果：")
    for i, result in enumerate(results, 1):
        print(f"\n--- 结果 {i} ---")
        print(result)

if __name__ == "__main__":
    main() 