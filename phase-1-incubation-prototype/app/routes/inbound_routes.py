"""
API routes for inbound messages from different channels:
- Email
- WhatsApp
- Web Form
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
import asyncio

from ..models.customer import CustomerCreateRequest
from ..models.ticket import TicketCreateRequest, SupportTicket
from ..models.message_format import UnifiedMessage
from ..services.customer_service import customer_service
from ..services.ticket_service import ticket_service
from ..agents.customer_success_agent import customer_success_agent
from ..database.mock_db import mock_db_instance
from ..utils.logger import log_interaction
from ..utils.message_normalizer import message_normalizer

router = APIRouter(prefix="/inbound", tags=["inbound"])

class EmailRequest:
    def __init__(self, email: str, name: str, message: str):
        self.email = email
        self.name = name
        self.message = message

class WhatsAppRequest:
    def __init__(self, phone: str, name: str, message: str):
        self.phone = phone
        self.name = name
        self.message = message

class WebFormRequest:
    def __init__(self, email: str, name: str, message: str):
        self.email = email
        self.name = name
        self.message = message

@router.post("/email")
async def handle_email_inbound(
    email: str,
    name: str,
    message: str,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Handle inbound email messages from customers.

    Args:
        email: Customer's email address
        name: Customer's name
        message: The message content

    Returns:
        Response dictionary with agent reply and ticket information
    """
    try:
        # Normalize the message before further processing
        normalized_message = message_normalizer.normalize_email_message(
            email=email,
            name=name,
            message=message
        )

        # Check if customer exists
        customer_exists = await customer_service.check_customer_exists(email=email)

        if not customer_exists:
            # Create new customer if they don't exist
            new_customer_req = CustomerCreateRequest(
                name=name,
                email=email,
                contact_preferences={"preferred_channel": "email"}
            )
            new_customer = await customer_service.create_customer(new_customer_req)
            customer_id = new_customer.id
        else:
            # Get existing customer
            existing_customer = await customer_service.get_customer_by_email(email)
            customer_id = existing_customer.id

            # Update last interaction timestamp
            await customer_service.update_customer(
                customer_id,
                {"last_interaction": asyncio.get_event_loop().time()}
            )

        # Create a ticket for the inquiry
        ticket_request = TicketCreateRequest(
            customer_id=customer_id,
            subject=f"Inquiry: {normalized_message['normalized_content'][:50]}..." if len(normalized_message['normalized_content']) > 50 else normalized_message['normalized_content'],
            description=normalized_message['normalized_content'],
            channel="gmail",
            priority="medium"
        )
        created_ticket = await ticket_service.create_ticket(ticket_request)

        # Process the inquiry with the agent using normalized content
        customer_context = await customer_service.get_customer_context(email=email)
        agent_response = await customer_success_agent.process_inquiry(
            customer_query=normalized_message["normalized_content"],
            customer_context=customer_context
        )

        # Log the interaction
        interaction_data = {
            "ticket_id": created_ticket.id,
            "sender_type": "customer",
            "content": normalized_message["normalized_content"],
            "channel_metadata": normalized_message["metadata"]["channel_specific"]
        }
        await mock_db_instance.add_interaction(interaction_data)

        # Add agent response as interaction
        agent_interaction_data = {
            "ticket_id": created_ticket.id,
            "sender_type": "agent",
            "content": agent_response["response"],
            "channel_metadata": {"source": "agent_response", "needs_triage": agent_response["needs_triage"]}
        }
        await mock_db_instance.add_interaction(agent_interaction_data)

        # Log to background tasks
        background_tasks.add_task(
            log_interaction,
            "email",
            email,
            normalized_message["normalized_content"],
            agent_response["response"]
        )

        return {
            "success": True,
            "message_id": created_ticket.id,
            "response": agent_response["response"],
            "ticket_created": True,
            "ticket_id": created_ticket.id,
            "needs_triage": agent_response["needs_triage"],
            "customer_exists": customer_exists,
            "normalized": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing email inbound: {str(e)}")


@router.post("/whatsapp")
async def handle_whatsapp_inbound(
    phone: str,
    name: str,
    message: str,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Handle inbound WhatsApp messages from customers.

    Args:
        phone: Customer's phone number
        name: Customer's name
        message: The message content

    Returns:
        Response dictionary with agent reply and ticket information
    """
    try:
        # Normalize the message before further processing
        normalized_message = message_normalizer.normalize_whatsapp_message(
            phone=phone,
            name=name,
            message=message
        )

        # Check if customer exists
        customer_exists = await customer_service.check_customer_exists(phone=phone)

        if not customer_exists:
            # Create new customer if they don't exist
            new_customer_req = CustomerCreateRequest(
                name=name,
                email=f"{name.replace(' ', '.')}@temp-email.com",  # Temporary email for WhatsApp users
                phone=phone,
                contact_preferences={"preferred_channel": "whatsapp"}
            )
            new_customer = await customer_service.create_customer(new_customer_req)
            customer_id = new_customer.id
        else:
            # Get existing customer
            existing_customer = await customer_service.get_customer_by_phone(phone)
            customer_id = existing_customer.id

            # Update last interaction timestamp
            await customer_service.update_customer(
                customer_id,
                {"last_interaction": asyncio.get_event_loop().time()}
            )

        # Create a ticket for the inquiry
        ticket_request = TicketCreateRequest(
            customer_id=customer_id,
            subject=f"WhatsApp Inquiry: {normalized_message['normalized_content'][:50]}..." if len(normalized_message['normalized_content']) > 50 else normalized_message['normalized_content'],
            description=normalized_message['normalized_content'],
            channel="whatsapp",
            priority="medium"
        )
        created_ticket = await ticket_service.create_ticket(ticket_request)

        # Process the inquiry with the agent using normalized content
        customer_context = await customer_service.get_customer_context(phone=phone)
        agent_response = await customer_success_agent.process_inquiry(
            customer_query=normalized_message["normalized_content"],
            customer_context=customer_context
        )

        # Log the interaction
        interaction_data = {
            "ticket_id": created_ticket.id,
            "sender_type": "customer",
            "content": normalized_message["normalized_content"],
            "channel_metadata": normalized_message["metadata"]["channel_specific"]
        }
        await mock_db_instance.add_interaction(interaction_data)

        # Add agent response as interaction
        agent_interaction_data = {
            "ticket_id": created_ticket.id,
            "sender_type": "agent",
            "content": agent_response["response"],
            "channel_metadata": {"source": "agent_response", "needs_triage": agent_response["needs_triage"]}
        }
        await mock_db_instance.add_interaction(agent_interaction_data)

        # Log to background tasks
        background_tasks.add_task(
            log_interaction,
            "whatsapp",
            phone,
            normalized_message["normalized_content"],
            agent_response["response"]
        )

        return {
            "success": True,
            "message_id": created_ticket.id,
            "response": agent_response["response"],
            "ticket_created": True,
            "ticket_id": created_ticket.id,
            "needs_triage": agent_response["needs_triage"],
            "customer_exists": customer_exists,
            "normalized": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing WhatsApp inbound: {str(e)}")


@router.post("/webform")
async def handle_webform_inbound(
    email: str,
    name: str,
    message: str,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Handle inbound messages from web form submissions.

    Args:
        email: Customer's email address
        name: Customer's name
        message: The message content

    Returns:
        Response dictionary with agent reply and ticket information
    """
    try:
        # Normalize the message before further processing
        normalized_message = message_normalizer.normalize_webform_message(
            email=email,
            name=name,
            message=message
        )

        # Check if customer exists
        customer_exists = await customer_service.check_customer_exists(email=email)

        if not customer_exists:
            # Create new customer if they don't exist
            new_customer_req = CustomerCreateRequest(
                name=name,
                email=email,
                contact_preferences={"preferred_channel": "webform"}
            )
            new_customer = await customer_service.create_customer(new_customer_req)
            customer_id = new_customer.id
        else:
            # Get existing customer
            existing_customer = await customer_service.get_customer_by_email(email)
            customer_id = existing_customer.id

            # Update last interaction timestamp
            await customer_service.update_customer(
                customer_id,
                {"last_interaction": asyncio.get_event_loop().time()}
            )

        # Create a ticket for the inquiry
        ticket_request = TicketCreateRequest(
            customer_id=customer_id,
            subject=f"Web Form Inquiry: {normalized_message['normalized_content'][:50]}..." if len(normalized_message['normalized_content']) > 50 else normalized_message['normalized_content'],
            description=normalized_message['normalized_content'],
            channel="webform",
            priority="medium"
        )
        created_ticket = await ticket_service.create_ticket(ticket_request)

        # Process the inquiry with the agent using normalized content
        customer_context = await customer_service.get_customer_context(email=email)
        agent_response = await customer_success_agent.process_inquiry(
            customer_query=normalized_message["normalized_content"],
            customer_context=customer_context
        )

        # Log the interaction
        interaction_data = {
            "ticket_id": created_ticket.id,
            "sender_type": "customer",
            "content": normalized_message["normalized_content"],
            "channel_metadata": normalized_message["metadata"]["channel_specific"]
        }
        await mock_db_instance.add_interaction(interaction_data)

        # Add agent response as interaction
        agent_interaction_data = {
            "ticket_id": created_ticket.id,
            "sender_type": "agent",
            "content": agent_response["response"],
            "channel_metadata": {"source": "agent_response", "needs_triage": agent_response["needs_triage"]}
        }
        await mock_db_instance.add_interaction(agent_interaction_data)

        # Log to background tasks
        background_tasks.add_task(
            log_interaction,
            "webform",
            email,
            normalized_message["normalized_content"],
            agent_response["response"]
        )

        return {
            "success": True,
            "message_id": created_ticket.id,
            "response": agent_response["response"],
            "ticket_created": True,
            "ticket_id": created_ticket.id,
            "needs_triage": agent_response["needs_triage"],
            "customer_exists": customer_exists,
            "normalized": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing webform inbound: {str(e)}")