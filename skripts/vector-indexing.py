# Модель: all-MiniLM-L6-v2
# Репозиторий: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
# Размер эмбеддингов: 384

import os
import json
import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import numpy as np
import time

class KnowledgeBaseVectorizer:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.embedding_size = self.model.get_sentence_embedding_dimension()

        self.client = chromadb.PersistentClient(path="./vector_store")

        self.collection = self.client.get_or_create_collection(
            name="star_wars_knowledge_base",
            metadata={"hnsw:space": "cosine"}
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

    def load_documents(self, knowledge_base_dir: str) -> List[Dict[str, Any]]:
        documents = []
        for filename in os.listdir(knowledge_base_dir):
            if filename.endswith('.txt'):
                file_path = os.path.join(knowledge_base_dir, filename)
                character_name = filename.replace('.txt', '')

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    documents.append({
                        'content': content,
                        'metadata': {
                            'file_path': file_path,
                            'character_name': character_name,
                            'source': f"starwars.fandom.com/wiki/{character_name}"
                        }
                    })

                except Exception as e:
                    print(f"Ошибка при чтении файла {filename}: {e}")
        return documents

    def chunk_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        all_chunks = []
        for doc in documents:
            # Разбиваем текст на чанки
            chunks = self.text_splitter.split_text(doc['content'])

            for i, chunk in enumerate(chunks):
                chunk_metadata = doc['metadata'].copy()
                chunk_metadata.update({
                    'chunk_id': i,
                    'chunk_index': i,
                    'total_chunks': len(chunks)
                })

                all_chunks.append({
                    'text': chunk,
                    'metadata': chunk_metadata
                })
        return all_chunks

    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        return self.model.encode(texts, show_progress_bar=True)

    def create_vector_index(self, chunks: List[Dict[str, Any]], batch_size: int = 5000):
        texts = [chunk['text'] for chunk in chunks]
        metadatas = [chunk['metadata'] for chunk in chunks]

        # Генерация эмбеддингов
        print("Генерация эмбеддингов...")
        embeddings = self.generate_embeddings(texts)

        # Создание ID
        ids = [f"doc_{i}" for i in range(len(texts))]

        print("Добавление в векторную базу по батчам...")
        for i in range(0, len(texts), batch_size):
            self.collection.add(
                embeddings=embeddings[i:i+batch_size].tolist(),
                documents=texts[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size],
                ids=ids[i:i+batch_size]
            )

    def search_similar_chunks(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        query_embedding = self.model.encode([query])[0].tolist()

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        return results



if __name__ == "__main__":
    start = time.time()
    print("Инициализация векторного индекса...")
    vectorizer = KnowledgeBaseVectorizer(model_name="all-MiniLM-L6-v2")

    print("Загрузка документов...")
    documents = vectorizer.load_documents("knowledge_base")
    print(f"Загружено документов: {len(documents)}")

    print("Разбивка на чанки...")
    chunks = vectorizer.chunk_documents(documents)
    print(f"Создано чанков: {len(chunks)}")

    print("Создание векторного индекса...")
    vectorizer.create_vector_index(chunks)

    print("Векторный индекс успешно создан!")
    print(f"Модель: all-MiniLM-L6-v2")
    print(f"Размер эмбеддингов: {vectorizer.embedding_size}")
    print(f"Количество чанков: {len(chunks)}")
    print(f"Затраченное время, {time.time() - start} с")

    print("\nТестовый поиск:")
    results = vectorizer.search_similar_chunks("сила джедай", n_results=3)
    print(f"Найдено результатов: {len(results['documents'][0])}")