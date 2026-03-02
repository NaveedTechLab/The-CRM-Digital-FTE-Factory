from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from typing import Dict, Any, Optional
import logging
from app.models.customer_interaction_history import CustomerInteractionHistory, Base
from app.config.settings import settings

logger = logging.getLogger(__name__)

class CustomerHistoryService:
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    async def get_customer_history(self, customer_id: str) -> Dict[str, Any]:
        """
        Retrieve customer interaction history from Phase 2 DatabaseManager
        """
        try:
            db = self.SessionLocal()

            try:
                # Get customer interaction history
                history = db.query(CustomerInteractionHistory).filter(
                    CustomerInteractionHistory.customer_id == customer_id
                ).first()

                if history:
                    return {
                        "customer_id": history.customer_id,
                        "conversation_id": history.conversation_id,
                        "first_contact_date": history.first_contact_date.isoformat() if history.first_contact_date else None,
                        "last_interaction_date": history.last_interaction_date.isoformat() if history.last_interaction_date else None,
                        "total_interactions": history.total_interactions,
                        "successful_resolutions": history.successful_resolutions,
                        "escalation_count": history.escalation_count,
                        "preferred_channels": history.preferred_channels or [],
                        "communication_preferences": history.communication_preferences or {},
                        "issue_categories": history.issue_categories or [],
                        "sentiment_trend": history.sentiment_trend,
                        "support_tier": history.support_tier,
                        "notes": history.notes,
                        "summary": f"This customer has had {history.total_interactions} interactions, with {history.successful_resolutions} successful resolutions and {history.escalation_count} escalations."
                    }
                else:
                    # Return default history if not found
                    return {
                        "customer_id": customer_id,
                        "conversation_id": None,
                        "first_contact_date": None,
                        "last_interaction_date": None,
                        "total_interactions": 0,
                        "successful_resolutions": 0,
                        "escalation_count": 0,
                        "preferred_channels": [],
                        "communication_preferences": {},
                        "issue_categories": [],
                        "sentiment_trend": "neutral",
                        "support_tier": "standard",
                        "notes": "",
                        "summary": f"This is a new customer with no previous interaction history."
                    }

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error getting customer history: {e}")
            raise

    async def update_customer_history(
        self,
        customer_id: str,
        conversation_id: Optional[str] = None,
        interaction_type: str = "query",
        resolved: bool = False,
        escalated: bool = False
    ) -> Dict[str, Any]:
        """
        Update customer interaction history after processing a message
        """
        try:
            db = self.SessionLocal()

            try:
                # Get existing history or create new one
                history = db.query(CustomerInteractionHistory).filter(
                    CustomerInteractionHistory.customer_id == customer_id
                ).first()

                if not history:
                    # Create new history record
                    history = CustomerInteractionHistory(
                        customer_id=customer_id,
                        conversation_id=conversation_id,
                        total_interactions=1,
                        successful_resolutions=0 if escalated else (1 if resolved else 0),
                        escalation_count=1 if escalated else 0
                    )
                    db.add(history)
                else:
                    # Update existing history
                    history.conversation_id = conversation_id or history.conversation_id
                    history.total_interactions += 1
                    if resolved and not escalated:
                        history.successful_resolutions += 1
                    if escalated:
                        history.escalation_count += 1
                    history.last_interaction_date = None  # Will be updated by SQLAlchemy's onupdate

                db.commit()
                db.refresh(history)

                return {
                    "customer_id": history.customer_id,
                    "total_interactions": history.total_interactions,
                    "successful_resolutions": history.successful_resolutions,
                    "escalation_count": history.escalation_count
                }

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error updating customer history: {e}")
            raise

# Global instance
customer_history_service = CustomerHistoryService()