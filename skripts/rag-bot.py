import os
from typing import List

import chromadb
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import requests
import re

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
VECTOR_STORE_PATH = "./vector_store"
COLLECTION_NAME = "star_wars_knowledge_base"

client = chromadb.PersistentClient(path=VECTOR_STORE_PATH)
collection = client.get_or_create_collection(COLLECTION_NAME)
model = SentenceTransformer(EMBEDDING_MODEL)

FEW_SHOT_EXAMPLES = """
Q: Как называется столица планеты Ти’лора?
A: Столица планеты Ти’лора называется Сайрон.
"""

SYSTEM_PROMPT = (
    "Ты помощник, который сначала размышляет, а потом отвечает. "
    "Всегда показывай шаги рассуждений в формате: REASONING -> ANSWER -> SOURCES."
)

YANDEX_API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
YANDEX_FOLDER_ID = os.environ.get('FOLDER_ID')
YANDEX_IAM_TOKEN = os.environ.get('IAM_TOKEN')

class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    reasoning: str
    answer: str
    sources: str


def search_similar_chunks(query, k=3):
    embedding = model.encode([query])
    results = collection.query(
        query_embeddings=embedding.tolist(),
        n_results=k
    )
    return results


def build_prompt(query, context_chunks):
    context_text = "\n\n".join(context_chunks)
    prompt = f"""{SYSTEM_PROMPT}

Контекст:
{context_text}

Примеры:
{FEW_SHOT_EXAMPLES}

Q: {query}
A:"""
    return prompt


def call_llm(prompt):
    headers = {
        "Authorization": f"Bearer {YANDEX_IAM_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.3,
            "maxTokens": 500
        },
        "messages": [
            {"role": "system", "text": SYSTEM_PROMPT},
            {"role": "user", "text": prompt}
        ]
    }
    response = requests.post(YANDEX_API_URL, headers=headers, json=body)
    response.raise_for_status()
    result = response.json()
    return result["result"]["alternatives"][0]["message"]["text"]


def parse_response(text):
    matches = re.split(r'REASONING:|ANSWER:|SOURCES:', text)
    reasoning, answer, sources = [m.strip() for m in matches[1:]]
    return QueryResponse(reasoning=reasoning, answer=answer, sources=sources)


app = FastAPI(title="RAG Bot API")


@app.post("/ask")
def ask(request: QueryRequest):
    results = search_similar_chunks(request.query, k=3)
    docs = results["documents"][0]
    prompt = build_prompt(request.query, docs)
    text = call_llm(prompt)
    return parse_response(text)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
