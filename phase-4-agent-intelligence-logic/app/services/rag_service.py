import openai
from openai import OpenAI
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from typing import List, Dict, Any, Optional
import logging
import numpy as np
from app.models.knowledge_base_article import KnowledgeBaseArticle, Base
from app.config.settings import settings

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        client_kwargs = {"api_key": settings.OPENAI_API_KEY}
        if settings.OPENAI_BASE_URL:
            client_kwargs["base_url"] = settings.OPENAI_BASE_URL
        self.client = OpenAI(**client_kwargs)
        self.embedding_model = settings.EMBEDDING_MODEL

        # Initialize database connection
        self.engine = create_engine(settings.DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for a text using OpenAI's embedding model
        """
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            raise

    def similarity_search(self, query: str, top_k: int = 5, min_similarity: float = 0.7) -> List[Dict[str, Any]]:
        """
        Perform semantic search on the knowledge base using pgvector
        """
        try:
            # Get embedding for the query
            query_embedding = self.get_embedding(query)

            # Convert embedding to string format for SQL
            embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

            # Create a database session
            db = self.SessionLocal()

            try:
                # Raw SQL query to perform vector similarity search
                sql = text("""
                    SELECT
                        id,
                        title,
                        content,
                        summary,
                        category,
                        1 - (embeddings <=> :query_embedding::vector) AS similarity_score
                    FROM knowledge_base_articles
                    WHERE status = 'published'
                    AND 1 - (embeddings <=> :query_embedding::vector) >= :min_similarity
                    ORDER BY 1 - (embeddings <=> :query_embedding::vector) DESC
                    LIMIT :top_k;
                """)

                result = db.execute(sql, {
                    "query_embedding": embedding_str,
                    "min_similarity": min_similarity,
                    "top_k": top_k
                })

                articles = []
                for row in result.fetchall():
                    articles.append({
                        "id": row[0],
                        "title": row[1],
                        "content": row[2],
                        "summary": row[3],
                        "category": row[4],
                        "similarity_score": float(row[5])
                    })

                return articles

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error performing similarity search: {e}")
            raise

    def get_relevant_context(self, query: str, top_k: int = 3, min_similarity: float = 0.6) -> List[Dict[str, Any]]:
        """
        Get relevant context from the knowledge base for a query.
        Returns empty list if KB is not available or search fails.
        """
        try:
            relevant_articles = self.similarity_search(query, top_k=top_k, min_similarity=min_similarity)
            return relevant_articles
        except Exception as e:
            logger.error(f"Error getting relevant context: {e}")
            logger.warning("Returning empty context - KB search unavailable, agent will respond without KB context")
            return []

    def calculate_relevance_score(self, query: str, article_content: str) -> float:
        """
        Calculate a relevance score between a query and an article
        """
        try:
            # Get embeddings for both query and article
            query_embedding = np.array(self.get_embedding(query))
            article_embedding = np.array(self.get_embedding(article_content))

            # Calculate cosine similarity
            dot_product = np.dot(query_embedding, article_embedding)
            norm_query = np.linalg.norm(query_embedding)
            norm_article = np.linalg.norm(article_embedding)

            if norm_query == 0 or norm_article == 0:
                return 0.0

            similarity = dot_product / (norm_query * norm_article)

            # Ensure the similarity is between 0 and 1
            return max(0.0, min(1.0, float(similarity)))
        except Exception as e:
            logger.error(f"Error calculating relevance score: {e}")
            return 0.0

    def index_knowledge_base(self):
        """
        Index all knowledge base articles by generating embeddings
        """
        try:
            db = self.SessionLocal()

            try:
                # Get all published articles
                articles = db.query(KnowledgeBaseArticle).filter(KnowledgeBaseArticle.status == 'published').all()

                for article in articles:
                    # Generate embedding for the content
                    content_to_embed = f"{article.title} {article.content}"
                    embedding = self.get_embedding(content_to_embed)

                    # Update the article with the embedding
                    # Since we're storing embeddings as string representations, convert to string
                    embedding_str = "[" + ",".join(map(str, embedding)) + "]"

                    # Update the database record
                    article.embeddings = embedding_str

                db.commit()
                logger.info(f"Indexed {len(articles)} knowledge base articles")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error indexing knowledge base: {e}")
            raise

rag_service = RAGService()