"""
Logging utility for tracking interactions and operations in the Customer Success Digital FTE.
"""
import logging
import sys
from datetime import datetime
from typing import Any, Dict

# Set up basic logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def log_interaction(channel: str, identifier: str, message: str, response: str) -> None:
    """
    Log an interaction between a customer and the agent.

    Args:
        channel: The communication channel (email, whatsapp, webform)
        identifier: The customer identifier (email or phone)
        message: The customer's original message
        response: The agent's response
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "channel": channel,
        "customer_identifier": identifier,
        "customer_message": message,
        "agent_response": response
    }

    logger.info(f"Interaction logged: {log_entry}")

def log_ticket_creation(ticket_id: str, customer_id: str, channel: str) -> None:
    """
    Log the creation of a support ticket.

    Args:
        ticket_id: The ID of the created ticket
        customer_id: The ID of the associated customer
        channel: The channel through which the ticket was created
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "ticket_id": ticket_id,
        "customer_id": customer_id,
        "channel": channel
    }

    logger.info(f"Ticket created: {log_entry}")

def validate_normalized_message(normalized_msg: Dict[str, Any]) -> bool:
    """
    Validate a normalized message to ensure it has all required fields.

    Args:
        normalized_msg: The normalized message dictionary to validate

    Returns:
        True if the message is valid, False otherwise
    """
    required_fields = ['source_channel', 'customer_identifier', 'customer_name', 'normalized_content', 'timestamp']

    for field in required_fields:
        if field not in normalized_msg or normalized_msg[field] is None:
            logger.error(f"Missing required field '{field}' in normalized message")
            return False

    # Validate source channel
    valid_channels = ['email', 'whatsapp', 'webform']
    if normalized_msg['source_channel'] not in valid_channels:
        logger.error(f"Invalid source channel: {normalized_msg['source_channel']}. Must be one of {valid_channels}")
        return False

    # Validate content is not empty
    if not normalized_msg['normalized_content'].strip():
        logger.error("Normalized content is empty")
        return False

    # Validate timestamp is reasonable (not too far in the future or past)
    timestamp = normalized_msg['timestamp']
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            logger.error(f"Invalid timestamp format: {timestamp}")
            return False

    current_time = datetime.now()
    time_diff = abs((current_time - timestamp).total_seconds())
    if time_diff > 86400:  # More than 24 hours difference
        logger.warning(f"Timestamp differs significantly from current time: {time_diff} seconds")

    return True