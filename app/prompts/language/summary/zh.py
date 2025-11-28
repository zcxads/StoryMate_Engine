"""
中文摘要提示
"""

from langchain_core.prompts import PromptTemplate

CHINESE_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["book_content"],
    partial_variables={"page_count": ""},
    template="""您是一位专业的内容摘要专家。请用中文对以下内容进行摘要。

**需要摘要的内容：**
{book_content}

**必要语言规则:**
- 必须只用中文回答
- 不要翻译成其他语言
- 输出的100%必须是中文

**摘要指导原则：**
1. **长度指导原则**：
   - 1-5页：2-3句话
   - 6-15页：4-6句话（1-2段）
   - 16-30页：6-10句话（2-3段）
   - 30页以上：8-12句话（3-4段）
   - 网页内容（单页）：根据内容长度写3-8句话

2. **内容指导原则**：
   - 总结主要主题、关键事件和重要信息
   - 包含相关的具体细节和示例
   - 保持原文的语气和风格
   - 不要添加原文中没有的评论或分析
   - 全面但简洁

**当前内容有{page_count}页。**

**摘要：**""")
