"""
Ticket service for handling ticket-related operations in the Customer Success Digital FTE.
"""
from typing import List, Optional
from datetime import datetime

from ..models.ticket import SupportTicket, TicketCreateRequest, TicketUpdateRequest
from ..database.mock_db import mock_db_instance


class TicketService:
    """
    Service class for handling ticket-related operations including
    creation, lookup, and management.
    """

    async def get_ticket_by_id(self, ticket_id: str) -> Optional[SupportTicket]:
        """
        Find a ticket by its ID.

        Args:
            ticket_id: The unique identifier for the ticket

        Returns:
            SupportTicket object if found, None otherwise
        """
        return await mock_db_instance.get_ticket_by_id(ticket_id)

    async def get_tickets_by_customer_id(self, customer_id: str) -> List[SupportTicket]:
        """
        Get all tickets associated with a specific customer.

        Args:
            customer_id: The ID of the customer

        Returns:
            List of SupportTicket objects
        """
        return await mock_db_instance.get_tickets_by_customer_id(customer_id)

    async def create_ticket(self, ticket_request: TicketCreateRequest) -> SupportTicket:
        """
        Create a new ticket in the database.

        Args:
            ticket_request: The ticket data to create

        Returns:
            The created SupportTicket object
        """
        # Create a SupportTicket object from the request
        ticket = SupportTicket(
            customer_id=ticket_request.customer_id,
            subject=ticket_request.subject,
            description=ticket_request.description,
            priority=ticket_request.priority,
            channel=ticket_request.channel
        )

        # Save to mock database
        created_ticket = await mock_db_instance.create_ticket(ticket)
        return created_ticket

    async def update_ticket(self, ticket_id: str, ticket_request: TicketUpdateRequest) -> Optional[SupportTicket]:
        """
        Update an existing ticket's information.

        Args:
            ticket_id: The ID of the ticket to update
            ticket_request: The updated ticket data

        Returns:
            Updated SupportTicket object if successful, None otherwise
        """
        # Prepare update data from the request
        update_data = {}
        if ticket_request.status is not None:
            update_data['status'] = ticket_request.status
        if ticket_request.assigned_to is not None:
            update_data['assigned_to'] = ticket_request.assigned_to
        if ticket_request.resolved_at is not None:
            update_data['resolved_at'] = ticket_request.resolved_at

        # Update in mock database
        updated_ticket = await mock_db_instance.update_ticket(ticket_id, update_data)
        return updated_ticket

    async def get_all_tickets(self) -> List[SupportTicket]:
        """
        Get all tickets in the system.

        Returns:
            List of all SupportTicket objects
        """
        return await mock_db_instance.get_all_tickets()


# Global instance of the ticket service
ticket_service = TicketService()