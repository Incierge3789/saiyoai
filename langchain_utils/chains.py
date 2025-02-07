# langchain_utils/chains.py
from langchain.chains import SequentialChain
from langchain.models import GPT4, BERT

def create_chain(api_key):
    gpt4_model = GPT4(api_key=api_key)
    bert_model = BERT()

    chain = SequentialChain(
        steps=[
            gpt4_model.generate_text,
            bert_model.classify_text,
            gpt4_model.refine_text
        ]
    )
    return chain
