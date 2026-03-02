from typing import Dict, Any, List, Optional
import logging
from pydantic import BaseModel, Field
from app.services.customer_history import customer_history_service
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)

class ToolInterface:
    def __init__(self):
        self.tools = {
            "get_customer_history": self.get_customer_history,
            "create_ticket": self.create_ticket,
            "search_kb": self.search_kb,
            "escalate": self.escalate
        }

    async def get_customer_history(self, customer_id: str) -> Dict[str, Any]:
        """
        Tool to retrieve customer history from Phase 2 DatabaseManager
        """
        try:
            history = await customer_history_service.get_customer_history(customer_id)
            return {
                "success": True,
                "result": history
            }
        except Exception as e:
            logger.error(f"Error getting customer history: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def create_ticket(self, customer_id: str, title: str, description: str, priority: str = "medium") -> Dict[str, Any]:
        """
        Tool to create a support ticket in the Phase 2 database
        """
        try:
            # This would integrate with Phase 2 ticket functionality
            # For now, returning a mock response
            ticket_data = {
                "customer_id": customer_id,
                "title": title,
                "description": description,
                "priority": priority,
                "status": "open",
                "created_at": "2023-01-01T00:00:00Z"
            }

            # In a real implementation, this would call the Phase 2 DatabaseManager
            # to create the actual ticket in the database

            return {
                "success": True,
                "ticket_id": f"ticket_{customer_id}_{hash(title)}",
                "result": ticket_data
            }
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def search_kb(self, query: str, top_k: int = 5, min_similarity: float = 0.6) -> Dict[str, Any]:
        """
        Tool to search the knowledge base using RAG service
        """
        try:
            results = rag_service.get_relevant_context(query, top_k=top_k, min_similarity=min_similarity)
            return {
                "success": True,
                "results": results
            }
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def escalate(self, customer_id: str, reason: str, message_content: str) -> Dict[str, Any]:
        """
        Tool to initiate human escalation process
        """
        try:
            # Create escalation record data
            escalation_data = {
                "customer_id": customer_id,
                "reason": reason,
                "message_content": message_content,
                "timestamp": "2023-01-01T00:00:00Z",
                "status": "pending_assignment"
            }

            # In a real implementation, this would create an escalation record
            # in the database and notify human agents

            return {
                "success": True,
                "escalation_id": f"esc_{customer_id}_{hash(reason)}",
                "result": escalation_data
            }
        except Exception as e:
            logger.error(f"Error initiating escalation: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the schema for a specific tool
        """
        schemas = {
            "get_customer_history": {
                "name": "get_customer_history",
                "description": "Retrieve customer interaction history",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "Unique identifier for the customer"
                        }
                    },
                    "required": ["customer_id"]
                }
            },
            "create_ticket": {
                "name": "create_ticket",
                "description": "Create a support ticket in the system",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "Unique identifier for the customer"
                        },
                        "title": {
                            "type": "string",
                            "description": "Brief title of the ticket"
                        },
                        "description": {
                            "type": "string",
                            "description": "Detailed description of the issue"
                        },
                        "priority": {
                            "type": "string",
                            "description": "Priority level of the ticket",
                            "enum": ["low", "medium", "high", "critical"],
                            "default": "medium"
                        }
                    },
                    "required": ["customer_id", "title", "description"]
                }
            },
            "search_kb": {
                "name": "search_kb",
                "description": "Search the knowledge base for relevant articles",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for relevant knowledge base articles"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 5
                        },
                        "min_similarity": {
                            "type": "number",
                            "description": "Minimum similarity threshold for results",
                            "default": 0.6
                        }
                    },
                    "required": ["query"]
                }
            },
            "escalate": {
                "name": "escalate",
                "description": "Initiate escalation to human support agent",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "Unique identifier for the customer"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for escalation"
                        },
                        "message_content": {
                            "type": "string",
                            "description": "Original message content that triggered escalation"
                        }
                    },
                    "required": ["customer_id", "reason", "message_content"]
                }
            }
        }

        return schemas.get(tool_name)

    def get_all_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Get schemas for all available tools
        """
        schemas = []
        for tool_name in self.tools.keys():
            schema = self.get_tool_schema(tool_name)
            if schema:
                schemas.append(schema)
        return schemas

# Global instance
tool_interface = ToolInterface()