import logging
from typing import Optional, Dict, Any
from datetime import datetime

from app.models.inbound_message import InboundMessage
from app.config.settings import settings


class IdentityResolver:
    """Service to resolve customer identity using Phase 2 DatabaseManager"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Import the DatabaseManager from Phase 2
        try:
            import sys
            import os
            sys.path.append('/mnt/e/hacksthon 5/The-CRM-Digital-FTE-Factory/phase-2-core-infrastructure-database')
            from app.database_manager import DatabaseManager
            self.db_manager = DatabaseManager()
        except ImportError:
            self.logger.warning("Phase 2 DatabaseManager not available, using mock implementation")
            self.db_manager = None

    async def resolve_identity(self, sender_id: str, channel: str, customer_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Resolve customer identity by looking up sender_id in the database.

        Args:
            sender_id: The sender identifier (email, phone number, etc.)
            channel: The channel through which the message came
            customer_name: Optional customer name from the message

        Returns:
            Dictionary with customer information including ID, name, and whether it was newly created
        """
        if self.db_manager:
            try:
                # Look up customer by email or phone
                customer = await self.db_manager.get_customer_by_identifier(sender_id)

                if customer:
                    # Customer exists
                    return {
                        "customer_id": customer.id,
                        "customer_name": customer.name or customer_name,
                        "created_new": False,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    # Customer doesn't exist, create a placeholder record
                    new_customer_data = {
                        "identifier": sender_id,
                        "name": customer_name,
                        "channel": channel,
                        "created_at": datetime.utcnow()
                    }

                    new_customer = await self.db_manager.create_customer(new_customer_data)

                    return {
                        "customer_id": new_customer.id,
                        "customer_name": customer_name,
                        "created_new": True,
                        "timestamp": datetime.utcnow().isoformat()
                    }
            except Exception as e:
                self.logger.error(f"Error resolving identity for {sender_id}: {str(e)}")
                # Return a default structure in case of error
                return {
                    "customer_id": None,
                    "customer_name": customer_name,
                    "created_new": False,
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": str(e)
                }
        else:
            # Mock implementation for when Phase 2 DatabaseManager is not available
            self.logger.warning(f"Using mock identity resolver for {sender_id}")
            return {
                "customer_id": f"mock-{sender_id}",
                "customer_name": customer_name,
                "created_new": True,
                "timestamp": datetime.utcnow().isoformat()
            }

    async def get_or_create_customer(self, sender_id: str, channel: str, customer_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get existing customer or create a new one if they don't exist.

        Args:
            sender_id: The sender identifier (email, phone number, etc.)
            channel: The channel through which the message came
            customer_name: Optional customer name from the message

        Returns:
            Dictionary with customer information
        """
        return await self.resolve_identity(sender_id, channel, customer_name)


# Global identity resolver instance
identity_resolver = IdentityResolver()