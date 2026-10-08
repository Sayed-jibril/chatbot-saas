import openai
from openai import OpenAI
from app.config import Config
import numpy as np


class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.chat_model = Config.CHAT_MODEL
        self.embedding_model = Config.EMBEDDING_MODEL

    def generate_embedding(self, text):
        """Generate embedding for a single text"""
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None

    def generate_embeddings_batch(self, texts):
        """Generate embeddings for multiple texts"""
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            return []

    def cosine_similarity(self, embedding1, embedding2):
        """Calculate cosine similarity between two embeddings"""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0

        return dot_product / (norm1 * norm2)

    def generate_chat_response(self, messages, context_chunks=None, system_prompt=None):
        """Generate chat response with context"""

        if system_prompt is None:
            system_prompt = """You are a helpful customer support assistant for a website.
            Answer questions based on the provided context. If the context doesn't contain
            relevant information, say so politely. Be concise and friendly."""

        full_messages = []

        if context_chunks:
            context_text = "\n\n".join(context_chunks)
            system_with_context = f"""{system_prompt}

Here is the knowledge base information to use:

{context_text}

Remember: Only use this information to answer questions. If asked something not in the context, say you don't have that information."""
            full_messages.append(
                {"role": "system", "content": system_with_context})
        else:
            full_messages.append({"role": "system", "content": system_prompt})

        full_messages.extend(messages)

        try:
            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=full_messages,
                temperature=0.7,
                max_tokens=500
            )

            return {
                'content': response.choices[0].message.content,
                'tokens': response.usage.total_tokens
            }
        except Exception as e:
            print(f"Error generating chat: {e}")
            return {
                'content': "I'm having trouble responding right now. Please try again.",
                'tokens': 0
            }


openai_service = OpenAIService()
