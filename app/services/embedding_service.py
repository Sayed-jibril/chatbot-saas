import json
from app.database import db
from app.services.openai_service import openai_service
from app.services.document_processor import document_processor


class EmbeddingService:

    def process_document(self, bot_id, document_id, file_data, file_type):
        """Process document: extract text, chunk, generate embeddings"""
        text = document_processor.extract_text(file_data, file_type)
        chunks = document_processor.chunk_text(text)
        embeddings = openai_service.generate_embeddings_batch(chunks)

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            if embedding:
                query = """
                    INSERT INTO embeddings (id, bot_id, document_id, chunk_text, embedding, chunk_index)
                    VALUES (UUID(), %s, %s, %s, %s, %s)
                """
                db.execute(query, (bot_id, document_id,
                           chunk, json.dumps(embedding), i))

        db.execute(
            "UPDATE documents SET processed = TRUE WHERE id = %s",
            (document_id,)
        )

        return len(chunks)

    def find_similar_chunks(self, bot_id, query_text, top_k=5):
        """Find most similar chunks for a query"""
        query_embedding = openai_service.generate_embedding(query_text)

        if not query_embedding:
            return []

        embeddings = db.execute(
            "SELECT chunk_text, embedding FROM embeddings WHERE bot_id = %s",
            (bot_id,),
            fetch_all=True
        )

        if not embeddings:
            return []

        similarities = []
        for emb in embeddings:
            emb_vector = json.loads(emb['embedding'])
            similarity = openai_service.cosine_similarity(
                query_embedding, emb_vector)
            similarities.append((similarity, emb['chunk_text']))

        similarities.sort(reverse=True, key=lambda x: x[0])
        return [chunk for _, chunk in similarities[:top_k]]


embedding_service = EmbeddingService()
