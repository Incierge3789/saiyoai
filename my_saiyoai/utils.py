
# my_saiyoai/utils.py
import logging
import re
import os
import openai
from .prompts import generate_image_prompt
from django.conf import settings
from .prompts import generate_gpt_prompt

logger = logging.getLogger(__name__)
openai.api_key = os.getenv('OPENAI_KEY')



def generate_improvement_suggestions(job_url, culture_url):
    # この部分にStreamlitアプリケーションのコードを基にした改善案生成のロジックを書きます
    # ここでは仮に空の辞書を返すようにしています
    return {
        "job_ticket": "",
        "scout_text": "",
        "story": "",
    }


def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)  # 連続する空白文字を1つのスペースに置き換える
    text = re.sub(r'\n+', '\n', text)  # 連続する改行を1つの改行に置き換える
    return text.strip()



def extract_and_translate_vision_keywords(story_text):
    """
    ストーリーテキストから企業のビジョンや目指す感情・雰囲気に関連するキーワードを抽出し、
    それらを英語に翻訳する関数。
    """
    try:
        # キーワード抽出のためのメッセージを準備
        extract_messages = [
            {"role": "system", "content": "This is a task to extract keywords related to corporate culture and vision. Extract keywords related to innovation, teamwork, growth opportunities, job satisfaction, and social contribution from the corporate story, and identify keywords that the target talent can perceive."},
            {"role": "user", "content": f"Based on the corporate story '{story_text}', please extract keywords related to vision and the emotions or atmosphere aimed for."}
        ]

        # キーワード抽出
        extract_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0125",
            messages=extract_messages
        )
        vision_keywords_text = extract_response['choices'][0]['message']['content']
        vision_keywords = vision_keywords_text.strip().split(', ')

        # 抽出したキーワードを英語に翻訳するためのメッセージを準備
        translate_messages = [
            {"role": "system", "content": "Translate the following keywords from Japanese to English."},
            {"role": "user", "content": ", ".join(vision_keywords)}
        ]

        # キーワード翻訳
        translate_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0125",
            messages=translate_messages
        )
        translated_keywords_text = translate_response['choices'][0]['message']['content']
        translated_keywords = translated_keywords_text.strip().split(', ')

        return translated_keywords
    except Exception as e:
        print("An error occurred during keyword extraction and translation.", e)
        return []


def generate_image_via_api(story_text):
    try:
        # 英語のキーワードを抽出および翻訳
        vision_keywords = extract_and_translate_vision_keywords(story_text)
        if not vision_keywords:
            logger.error("ビジョンや感情・雰囲気に関連するキーワードが抽出および翻訳できませんでした。")
            return None
        
        # `prompts.py` からプロンプト生成関数を使用
        detailed_prompt = generate_image_prompt(vision_keywords)
        logger.info(f"画像生成のための詳細なプロンプト: {detailed_prompt}")
        
        response = openai.Image.create(
            prompt=detailed_prompt,
            n=1,
            size="1024x1024"
        )
        
        logger.info("OpenAI APIからの画像生成レスポンス: {}".format(response))
        if 'data' in response and len(response['data']) > 0:
            image_url = response['data'][0]['url']
            logger.info(f"生成された画像のURL: {image_url}")
            return image_url
        else:
            logger.error("画像URLがレスポンスデータに含まれていません。")
            return None
    except Exception as e:
        logger.error("画像生成処理中にエラーが発生しました。", exc_info=True)
        return None


def get_gpt_response(material_description, user_question):
    messages = [
        {"role": "system", "content": "You are a helpful assistant that responds in Japanese."},
        {"role": "user", "content": f"教材の説明：{material_description}"},
        {"role": "user", "content": f"質問：{user_question}"}
    ]
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        # APIからのレスポンスをログに記録
        logger.info(f"OpenAI API Response: {response}")
        
        # APIからのレスポンスから回答を抽出
        answer = response['choices'][0]['message']['content'].strip()
        return answer
    except Exception as e:
        # エラーをログに記録
        logger.error(f"Error while calling OpenAI API: {e}")
        return None
