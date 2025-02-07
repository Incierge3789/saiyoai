import random

def generate_job_ticket_prompt(text, word_limit):
    return f"""
以下の情報をもとに、完結する形で企業が欲しい人材または優秀な人材が魅力を感じ、応募を検討するような求人票を作成してください。
情報が足りない場合は、想像力を働かせて補足し、全ての必要情報を含めてください。
求人票は要点を簡潔にまとめ、完結するようにしてください。
{text}

求人票:
企業名:
・企業名: 
会社概要:
・会社のビジョン: 
募集職種:
・職種: 
仕事内容:
・業務内容: 
募集要項:
・雇用形態: 
・勤務地: 
・給与: 
・勤務時間: 
応募資格:
・資格: 
福利厚生:
・福利厚生の詳細: 
応募方法:
・応募方法の詳細: 
会社情報:
・住所: 
・代表者名: 
・ホームページ: 
選考プロセス:
・選考の流れ: 
"""

def generate_scout_text_prompt(text,  word_limit):
    return f"""
以下の情報をもとに、題名を除いた本文部分が{word_limit}文字以内で完結し、ポイントを簡潔にまとめたスカウト文面を作成してください。
情報が不足している場合は、想像力を働かせて補足し、スカウト文面が{word_limit}文字以内で完結するようにしてください。
目指すは、優秀な人材が魅力を感じ、応募を検討するような内容です。

{text}

スカウト文面:
題名:
{{scout_title}}

本文:
{{scout_body}}
"""

def generate_story_prompt(text,  word_limit):
    return f"""
以下の情報をもと、題名を除いた本文部分が{word_limit}文字以内で完結し、ポイントを簡潔にまとめたストーリーを作成してください。
情報が不足している場合は、想像力を働かせて補足し、ストーリーが{word_limit}文字以内で完結するようにしてください。
目的は、優秀な人材が魅力を感じるような、企業のビジョンやミッションを伝えるストーリーです。

{text}

ストーリー:
題名:
{{story_title}}

本文:
{{story_body}}
"""

def generate_chatbot_prompt(user_query):
    """
    ユーザーからの質問に基づいてチャットボットのプロンプトを生成します。
    プロンプトは、「Saiyo AI」のビジョン、使命、および特徴を反映したものです。
    
    :param user_query: ユーザーからの質問またはコメント
    :return: チャットボットのプロンプト
    """

    prompt = f"""
    あなたは「Saiyo AI」、革新的な人材採用のアシスタントです。以下の領域に関するユーザーの質問に、友好的かつプロフェッショナルな方法で回答してください。回答は一般的な情報に限定し、機密情報は含めないでください:
    - データ駆動型人材採用戦略の基本
    - ユーザーエクスペリエンスを重視したアプリの利用方法
    - エシカルなAIの利用とプライバシー保護
    - 採用プロセスの透明性と候補者体験の向上
    - 連続的な学習と進化を支えるフィードバックの収集と活用

    ユーザーの質問: '{user_query}'

    以下に、適切な回答を示してください。ユーザーのニーズと質問に対して、具体的で役立つアドバイスを提供することが重要です。個々の質問には直接的かつ対話的な方法で応答し、Saiyo AIのビジョンと使命を反映させてください。
    """

    return prompt


def generate_styled_job_ticket_prompt(text, style):
    return f"""
以下のテキストをもとに、{style}スタイルで求人票を再構成してください。結果は優秀な人材が魅力を感じ、応募を検討するような内容にして、日本語で返してください。

{text}

求人票:
企業名:
・企業名: 
会社概要:
・会社のビジョン: 
募集職種:
・職種: 
仕事内容:
・業務内容: 
募集要項:
・雇用形態: 
・勤務地: 
・給与: 
・勤務時間: 
応募資格:
・資格: 
福利厚生:
・福利厚生の詳細: 
応募方法:
・応募方法の詳細: 
会社情報:
・住所: 
・代表者名: 
・ホームページ: 
選考プロセス:
・選考の流れ: 

"""

def generate_styled_scout_text_prompt(text, style):
    return f"""
以下のテキストをもとに、{style}スタイルでスカウト文面を再構成してください。結果は優秀な人材が魅力を感じ、応募を検討するような内容にして、日本語で返してください。

{text}

スカウト文面:
題名: 
{scout_title}
本文: 
{scout_body}
"""

def generate_styled_story_prompt(text, style):
    return f"""
以下のテキストをもとに、{style}スタイルでストーリーを再構成してください。結果は優秀な人材が魅力を感じるような、企業のビジョンやミッションを伝える内容にして、日本語で返してください。

{text}

ストーリー:
題名:
{story_title}
本文:
{story_body}
"""





hidden_elements = {
    "Corporate Values": ["Innovation", "Sustainability", "Diversity", "Transparency", "Collaboration", "Customer-Centric"],
    "Team Spirit": ["Collaboration", "Mutual Support", "Trust", "Respect", "Empathy", "Empowerment"],
    "Innovation": ["Creativity", "Problem Solving", "Improvement", "Technological Progress", "Research and Development", "Entrepreneurship"],
    "Working Environment": ["Safety", "Health", "Comfort", "Accessibility", "Natural Light", "Greenery"],
    "Social Contribution": ["Community Engagement", "Environmental Protection", "Educational Support", "Health Promotion", "Equality Advancement", "Cultural Preservation"],
    "Natural Symbols": ["Ocean", "Mountain", "Forest", "River", "Desert", "Flower", "Sun", "Moon", "Stars", "Cloud"],
    "Growth and Development": ["New Leaves", "Bud", "Climbing", "Voyaging", "Path", "Bridge", "Stairs", "Light"],
    "Communication": ["Conversation", "Sharing", "Listening", "Explaining", "Negotiating", "Agreement"],
    "Creation and Discovery": ["Invention", "Exploration", "Idea", "Inspiration", "Art", "Music"],
    "Well-being": ["Health", "Balance", "Relaxation", "Exercise", "Nutrition", "Sleep"],
    "Problem Solving": ["Puzzle", "Maze", "Key and Lock", "Equation", "Strategy", "Plan"],
}

def generate_image_prompt(vision_keywords):
    # Randomly select categories from the dictionary and select a random element from those categories
    categories_and_elements = [(category, random.choice(elements)) for category, elements in random.sample(hidden_elements.items(), 4)]

    prompt = f"Based on the following keywords: {' '.join(vision_keywords)}, create an image that embodies our unique corporate culture and values.\n"
    for category, element in categories_and_elements:
        prompt += f"- {category}: {element}\n"
    prompt += "The desired atmosphere is 'an open and positive workplace'.\n"
    prompt += "Through this image, we want to attract future-oriented talent passionate about creating a future with us and bringing meaningful change to society."

    return prompt.strip()


def generate_gpt_prompt(material_description, user_question):
    # 日本語での回答を指示し、質問者が生成AIについての初心者であることを考慮するプロンプトのテンプレートを提供
    prompt_template = """
    あなたは世界一有能なアシスタントです。以下の教材の説明を読んで、質問に対して非常にわかりやすい日本語で回答してください。質問者は生成AIについての初心者であり、基本的な概念から丁寧に説明する必要があります。

    教材の説明:
    "{description}"

    質問:
    "{question}"
    
    回答は、初心者でも理解できるように、専門用語を避けるか、使用する場合は簡単に説明を加えてください。また、可能であれば具体的な例や比喩を用いて説明することで、理解を深めてください。
    """
    return prompt_template.format(description=material_description, question=user_question)
