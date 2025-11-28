from langchain_core.prompts import ChatPromptTemplate


def get_content_extraction_prompt(lang_code: str) -> ChatPromptTemplate:
    """언어별 통합 본문 추출 프롬프트 (본문 추출 + 메타데이터 제거 통합)"""

    prompts = {
        'ko': """당신은 웹페이지에서 핵심 본문만을 추출하는 전문가입니다.

다음 텍스트에서 실제 본문만 추출하고 메타데이터는 제거해주세요:

{raw_content}

**제거할 항목** (네비게이션, 광고, 메타데이터):
1. 네비게이션, 헤더, 푸터, 사이드바, 광고
2. 기자 정보: "서울=연합뉴스 김철수 기자", "뉴스1 박민수 기자" 등
3. 연락처: 이메일, 전화번호만 있는 라인
4. 날짜/시간만 있는 라인 (예: "2024년 1월 15일")
5. 뉴스사명만 있는 라인 (예: "연합뉴스", "YTN")
6. 저작권: "무단전재 금지", "Copyright" 등
7. SNS 공유 유도: "공유하기", "구독" 등
8. 메타 정보: "카테고리:", "출처:", "사진:" 등

**보존할 항목** (실제 본문):
- 제목과 소제목
- 완전한 문장 (동사 포함, 50자 이상)
- 인용문, 대화문
- 실제 뉴스/콘텐츠 내용

**중요 제약**:
- 원문 그대로 유지 (재작성/요약 금지)
- 표현, 어조, 문체 변경 금지
- 마크다운(**텍스트**)은 일반 텍스트로 변환

깨끗한 본문만 반환:
""",

        'en': """You are an expert at extracting main content from web pages.

Extract only the actual content from the following text and remove all metadata:

{raw_content}

**Remove** (navigation, ads, metadata):
1. Navigation, header, footer, sidebar, advertisements
2. Author/journalist info: bylines, author names with titles
3. Contact info: email addresses, phone numbers
4. Date/time stamps
5. News outlet names (standalone)
6. Copyright notices: "All rights reserved", "Copyright" etc.
7. Social sharing prompts: "Share", "Subscribe" etc.
8. Meta information: "Category:", "Source:", "Photo:" etc.

**Keep** (actual content):
- Titles and headings
- Complete sentences (with verbs, 50+ characters)
- Quotes and dialogues
- Actual news/article content

**Important constraints**:
- Keep original text as-is (no rewriting/summarizing)
- Preserve tone, style, and expression
- Convert markdown (**text**) to plain text

Return clean content only:
""",

        'ja': """あなたはウェブページから本文のみを抽出する専門家です。

以下のテキストから実際の本文のみを抽出し、メタデータは削除してください:

{raw_content}

**削除対象** (ナビゲーション、広告、メタデータ):
1. ナビゲーション、ヘッダー、フッター、サイドバー、広告
2. 記者情報: 署名、記者名など
3. 連絡先: メールアドレス、電話番号のみの行
4. 日時のみの行 (例: "2024年1月15日")
5. メディア名のみの行 (例: "朝日新聞")
6. 著作権表示: "無断転載禁止", "Copyright" など
7. SNS共有促進: "シェア", "購読" など
8. メタ情報: "カテゴリ:", "出典:", "写真:" など

**保持対象** (実際の本文):
- タイトルと見出し
- 完全な文章 (動詞を含む、50文字以上)
- 引用、会話文
- 実際のニュース/記事内容

**重要な制約**:
- 原文をそのまま維持 (書き換え/要約禁止)
- 表現、トーン、文体の変更禁止
- マークダウン(**テキスト**)は通常テキストに変換

クリーンな本文のみを返す:
""",

        'zh': """您是从网页中提取核心内容的专家。

从以下文本中提取实际内容，并删除所有元数据:

{raw_content}

**删除项目** (导航、广告、元数据):
1. 导航、页眉、页脚、侧边栏、广告
2. 记者信息: 署名、记者姓名等
3. 联系方式: 仅有电子邮件、电话号码的行
4. 仅有日期/时间的行 (例: "2024年1月15日")
5. 仅有媒体名称的行 (例: "新华社")
6. 版权声明: "未经授权禁止转载", "Copyright" 等
7. 社交分享提示: "分享", "订阅" 等
8. 元信息: "类别:", "来源:", "图片:" 等

**保留项目** (实际内容):
- 标题和副标题
- 完整句子 (包含动词、50字以上)
- 引用、对话
- 实际新闻/文章内容

**重要约束**:
- 保持原文不变 (禁止改写/摘要)
- 保持表达、语气、文体不变
- 将markdown(**文本**)转换为纯文本

仅返回清洁内容:
"""
    }

    # 기본값은 영어
    template = prompts.get(lang_code, prompts['en'])
    return ChatPromptTemplate.from_template(template)
