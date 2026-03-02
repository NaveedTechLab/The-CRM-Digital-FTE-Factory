"""
Mock database layer with in-memory storage for the Customer Success Digital FTE prototype.
This simulates PostgreSQL interaction for the prototype.
"""
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from ..models.customer import Customer
from ..models.ticket import SupportTicket

class MockDB:
    """
    In-memory mock database to simulate PostgreSQL interaction for the prototype.
    """

    def __init__(self):
        self.customers: Dict[str, Customer] = {}
        self.tickets: Dict[str, SupportTicket] = {}
        self.interactions: List[Dict[str, Any]] = []

    async def get_customer_by_email(self, email: str) -> Optional[Customer]:
        """Find a customer by email address."""
        for customer in self.customers.values():
            if customer.email.lower() == email.lower():
                return customer
        return None

    async def get_customer_by_phone(self, phone: str) -> Optional[Customer]:
        """Find a customer by phone number."""
        for customer in self.customers.values():
            if customer.phone and customer.phone == phone:
                return customer
        return None

    async def get_customer_by_id(self, customer_id: str) -> Optional[Customer]:
        """Find a customer by ID."""
        return self.customers.get(customer_id)

    async def create_customer(self, customer_data: Customer) -> Customer:
        """Create a new customer in the mock database."""
        customer_data.id = str(uuid.uuid4())
        customer_data.created_at = datetime.now()
        customer_data.updated_at = datetime.now()

        self.customers[customer_data.id] = customer_data
        return customer_data

    async def update_customer(self, customer_id: str, customer_data: dict) -> Optional[Customer]:
        """Update an existing customer."""
        if customer_id in self.customers:
            customer = self.customers[customer_id]

            # Update fields if provided
            for key, value in customer_data.items():
                if hasattr(customer, key) and value is not None:
                    setattr(customer, key, value)

            customer.updated_at = datetime.now()
            return customer

        return None

    async def get_ticket_by_id(self, ticket_id: str) -> Optional[SupportTicket]:
        """Find a ticket by ID."""
        return self.tickets.get(ticket_id)

    async def get_tickets_by_customer_id(self, customer_id: str) -> List[SupportTicket]:
        """Get all tickets associated with a customer."""
        return [
            ticket for ticket in self.tickets.values()
            if ticket.customer_id == customer_id
        ]

    async def create_ticket(self, ticket_data: SupportTicket) -> SupportTicket:
        """Create a new ticket in the mock database."""
        ticket_data.id = str(uuid.uuid4())
        ticket_data.created_at = datetime.now()
        ticket_data.updated_at = datetime.now()

        self.tickets[ticket_data.id] = ticket_data
        return ticket_data

    async def update_ticket(self, ticket_id: str, ticket_data: dict) -> Optional[SupportTicket]:
        """Update an existing ticket."""
        if ticket_id in self.tickets:
            ticket = self.tickets[ticket_id]

            # Update fields if provided
            for key, value in ticket_data.items():
                if hasattr(ticket, key) and value is not None:
                    setattr(ticket, key, value)

            ticket.updated_at = datetime.now()
            return ticket

        return None

    async def get_all_customers(self) -> List[Customer]:
        """Get all customers."""
        return list(self.customers.values())

    async def get_all_tickets(self) -> List[SupportTicket]:
        """Get all tickets."""
        return list(self.tickets.values())

    async def add_interaction(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add an interaction record to the mock database."""
        interaction_data['id'] = str(uuid.uuid4())
        interaction_data['timestamp'] = datetime.now()

        self.interactions.append(interaction_data)
        return interaction_data

    async def get_interactions_by_ticket_id(self, ticket_id: str) -> List[Dict[str, Any]]:
        """Get all interactions for a specific ticket."""
        return [
            interaction for interaction in self.interactions
            if interaction.get('ticket_id') == ticket_id
        ]


# Global instance of the mock database
mock_db_instance = MockDB()