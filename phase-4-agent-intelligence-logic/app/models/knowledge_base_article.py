from sqlalchemy import Column, String, Text, DateTime, Float, Integer, Boolean, ForeignKey, ARRAY, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class KnowledgeBaseArticle(Base):
    __tablename__ = "knowledge_base_articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)  # Title of the knowledge base article
    content = Column(Text, nullable=False)  # Full content of the article
    summary = Column(String, nullable=True)  # Brief summary of the article
    category = Column(String, nullable=True)  # Category or topic classification
    tags = Column(ARRAY(String), nullable=True)  # Keywords/tags for the article
    embeddings = Column(String, nullable=True)  # Vector embeddings for semantic search (stored as string representation)
    version = Column(String, nullable=True)  # Version number of the article
    author = Column(String, nullable=True)  # Author of the article
    last_updated = Column(DateTime, nullable=False, default=func.now())  # When the article was last updated
    status = Column(String, default='published')  # Enum: 'draft', 'published', 'archived'
    relevance_score = Column(Float, nullable=True)  # Average relevance score based on usage, 0.0-1.0
    usage_count = Column(Integer, default=0)  # Number of times article has been referenced

    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())