from typing import Dict, Any
import logging
from pydantic import BaseModel, Field
from app.services.customer_history import customer_history_service

logger = logging.getLogger(__name__)

class GetCustomerHistoryInput(BaseModel):
    customer_id: str = Field(..., description="Unique identifier for the customer")

async def get_customer_history_tool(input_data: GetCustomerHistoryInput) -> Dict[str, Any]:
    """
    Tool for retrieving customer history
    """
    try:
        result = await customer_history_service.get_customer_history(input_data.customer_id)
        return {
            "success": True,
            "customer_history": result
        }
    except Exception as e:
        logger.error(f"Error in get_customer_history_tool: {e}")
        return {
            "success": False,
            "error": str(e)
        }