# langchain_utils/models.py
from langchain.models import GPT4

def create_gpt4_model(api_key):
    return GPT4(api_key=api_key)
