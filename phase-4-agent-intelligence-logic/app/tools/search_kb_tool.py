from typing import Dict, Any
import logging
from pydantic import BaseModel, Field
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)

class SearchKBInput(BaseModel):
    query: str = Field(..., description="Search query for relevant knowledge base articles")
    top_k: int = Field(5, description="Maximum number of results to return")
    min_similarity: float = Field(0.6, description="Minimum similarity threshold for results")

async def search_kb_tool(input_data: SearchKBInput) -> Dict[str, Any]:
    """
    Tool for searching the knowledge base
    """
    try:
        results = rag_service.get_relevant_context(
            query=input_data.query,
            top_k=input_data.top_k,
            min_similarity=input_data.min_similarity
        )

        return {
            "success": True,
            "results": results
        }
    except Exception as e:
        logger.error(f"Error in search_kb_tool: {e}")
        return {
            "success": False,
            "error": str(e)
        }