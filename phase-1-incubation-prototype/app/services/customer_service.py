"""
Customer service for handling customer-related operations in the Customer Success Digital FTE.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..models.customer import Customer, CustomerCreateRequest, CustomerUpdateRequest
from ..database.mock_db import mock_db_instance
from ..models.ticket import SupportTicket


class CustomerService:
    """
    Service class for handling customer-related operations including
    creation, lookup, and management.
    """

    async def get_customer_by_email(self, email: str) -> Optional[Customer]:
        """
        Find a customer by their email address.

        Args:
            email: The email address to search for

        Returns:
            Customer object if found, None otherwise
        """
        return await mock_db_instance.get_customer_by_email(email)

    async def get_customer_by_phone(self, phone: str) -> Optional[Customer]:
        """
        Find a customer by their phone number.

        Args:
            phone: The phone number to search for

        Returns:
            Customer object if found, None otherwise
        """
        return await mock_db_instance.get_customer_by_phone(phone)

    async def get_customer_by_id(self, customer_id: str) -> Optional[Customer]:
        """
        Find a customer by their ID.

        Args:
            customer_id: The unique identifier for the customer

        Returns:
            Customer object if found, None otherwise
        """
        return await mock_db_instance.get_customer_by_id(customer_id)

    async def create_customer(self, customer_request: CustomerCreateRequest) -> Customer:
        """
        Create a new customer in the database.

        Args:
            customer_request: The customer data to create

        Returns:
            The created Customer object
        """
        # Create a Customer object from the request
        customer = Customer(
            name=customer_request.name,
            email=customer_request.email,
            phone=customer_request.phone,
            contact_preferences=customer_request.contact_preferences
        )

        # Save to mock database
        created_customer = await mock_db_instance.create_customer(customer)
        return created_customer

    async def update_customer(self, customer_id: str, customer_request: CustomerUpdateRequest) -> Optional[Customer]:
        """
        Update an existing customer's information.

        Args:
            customer_id: The ID of the customer to update
            customer_request: The updated customer data

        Returns:
            Updated Customer object if successful, None otherwise
        """
        # Prepare update data from the request
        update_data = {}
        if customer_request.name is not None:
            update_data['name'] = customer_request.name
        if customer_request.phone is not None:
            update_data['phone'] = customer_request.phone
        if customer_request.contact_preferences is not None:
            update_data['contact_preferences'] = customer_request.contact_preferences

        # Update in mock database
        updated_customer = await mock_db_instance.update_customer(customer_id, update_data)
        return updated_customer

    async def get_customer_context(self, email: Optional[str] = None, phone: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive customer context including history and tickets.

        Args:
            email: Customer's email address
            phone: Customer's phone number

        Returns:
            Dictionary with customer context information, or None if not found
        """
        customer = None

        # Look up customer by email or phone
        if email:
            customer = await self.get_customer_by_email(email)
        elif phone:
            customer = await self.get_customer_by_phone(phone)

        if not customer:
            return None

        # Get customer's tickets
        tickets = await mock_db_instance.get_tickets_by_customer_id(customer.id)

        # Prepare context dictionary
        context = {
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "contact_preferences": customer.contact_preferences,
            "created_at": customer.created_at,
            "last_interaction": customer.last_interaction,
            "tickets": [ticket.dict() for ticket in tickets],
            "interaction_history": await self.get_interaction_history(customer.id)
        }

        return context

    async def get_interaction_history(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Get the interaction history for a customer.

        Args:
            customer_id: The ID of the customer

        Returns:
            List of interaction records
        """
        # For now, return empty list - this would connect to interaction storage in a real implementation
        return []

    async def check_customer_exists(self, email: Optional[str] = None, phone: Optional[str] = None) -> bool:
        """
        Check if a customer exists in the database based on email or phone number.

        Args:
            email: Customer's email address to check
            phone: Customer's phone number to check

        Returns:
            True if customer exists, False otherwise
        """
        if email:
            customer = await self.get_customer_by_email(email)
            if customer:
                return True

        if phone:
            customer = await self.get_customer_by_phone(phone)
            if customer:
                return True

        return False


# Global instance of the customer service
customer_service = CustomerService()