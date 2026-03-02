"""
Migration script to transition Phase 1 mock data structures to PostgreSQL schema.
This script migrates data from the Phase 1 in-memory mock database to the Phase 2 PostgreSQL database.
"""
import asyncio
import json
from typing import Dict, List, Any
from datetime import datetime
from app.database_manager import DatabaseManager, Customer, Ticket, Message
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MigrationScript:
    """
    Migration script to transition Phase 1 mock data structures to PostgreSQL schema.
    """

    def __init__(self, db_url: str = "postgresql://postgres:postgres@localhost:5432/internal_crm"):
        """
        Initialize the migration script with database connection.

        Args:
            db_url: PostgreSQL connection string
        """
        self.db_manager = DatabaseManager(db_url)
        self.migrated_records = {
            'customers': 0,
            'tickets': 0,
            'messages': 0
        }

    def load_phase1_mock_data(self) -> Dict[str, Any]:
        """
        Load mock data from Phase 1 structure.
        In a real scenario, this would load from the Phase 1 data structures/files.
        For this prototype, we'll simulate the data structure.

        Returns:
            Dictionary containing mock data from Phase 1
        """
        # This is a simulation - in reality, this would load from Phase 1's mock database
        # For now, we'll create some sample data that mimics what would be in Phase 1
        mock_data = {
            "customers": [
                {
                    "id": "1",
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "phone": "+1234567890",
                    "contact_preferences": {"preferred_channel": "email"},
                    "created_at": "2023-01-15T10:30:00Z",
                    "last_interaction": "2023-02-20T14:45:00Z"
                },
                {
                    "id": "2",
                    "name": "Jane Smith",
                    "email": "jane.smith@example.com",
                    "phone": "+0987654321",
                    "contact_preferences": {"preferred_channel": "whatsapp"},
                    "created_at": "2023-02-10T09:15:00Z",
                    "last_interaction": "2023-02-18T11:20:00Z"
                }
            ],
            "tickets": [
                {
                    "id": "101",
                    "customer_id": "1",
                    "subject": "Issue with product setup",
                    "description": "Customer is having trouble setting up the product",
                    "status": "open",
                    "priority": "medium",
                    "channel": "email",
                    "created_at": "2023-02-20T14:45:00Z"
                },
                {
                    "id": "102",
                    "customer_id": "2",
                    "subject": "Payment processing error",
                    "description": "Customer reported an error during payment processing",
                    "status": "in-progress",
                    "priority": "high",
                    "channel": "webform",
                    "created_at": "2023-02-18T11:20:00Z"
                }
            ],
            "messages": [
                {
                    "id": "1001",
                    "ticket_id": "101",
                    "sender_type": "customer",
                    "content": "I'm having trouble setting up the product according to the instructions",
                    "direction": "inbound",
                    "timestamp": "2023-02-20T14:45:00Z"
                },
                {
                    "id": "1002",
                    "ticket_id": "101",
                    "sender_type": "agent",
                    "content": "Thank you for reaching out. I'll help you with the setup process.",
                    "direction": "outbound",
                    "timestamp": "2023-02-20T15:00:00Z"
                }
            ]
        }

        logger.info(f"Loaded {len(mock_data['customers'])} customers, {len(mock_data['tickets'])} tickets, {len(mock_data['messages'])} messages from Phase 1 mock data")
        return mock_data

    def migrate_customers(self, mock_customers: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Migrate customers from Phase 1 structure to Phase 2 PostgreSQL schema.

        Args:
            mock_customers: List of customer data from Phase 1

        Returns:
            List of mappings between old and new customer IDs
        """
        customer_id_mapping = []

        for mock_customer in mock_customers:
            # Transform Phase 1 customer data to Phase 2 format
            customer_data = {
                "external_id": mock_customer["id"],  # Store Phase 1 ID as external_id
                "name": mock_customer["name"],
                "email": mock_customer["email"],
                "phone": mock_customer.get("phone"),
                "contact_preferences": mock_customer.get("contact_preferences", {}),
                "last_interaction": mock_customer.get("last_interaction")
            }

            # Check if customer already exists (based on email)
            existing_customer = self.db_manager.get_customer_by_email(mock_customer["email"])

            if existing_customer:
                logger.info(f"Customer with email {mock_customer['email']} already exists, updating...")
                updated_customer = self.db_manager.update_customer(
                    existing_customer.id,
                    customer_data
                )
                customer_id_mapping.append({
                    "old_id": mock_customer["id"],
                    "new_id": str(updated_customer.id)
                })
            else:
                # Create new customer
                new_customer = self.db_manager.create_customer(customer_data)
                customer_id_mapping.append({
                    "old_id": mock_customer["id"],
                    "new_id": str(new_customer.id)
                })
                self.migrated_records['customers'] += 1
                logger.info(f"Migrated customer: {mock_customer['name']}")

        return customer_id_mapping

    def migrate_tickets(self, mock_tickets: List[Dict[str, Any]], customer_id_mapping: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Migrate tickets from Phase 1 structure to Phase 2 PostgreSQL schema.

        Args:
            mock_tickets: List of ticket data from Phase 1
            customer_id_mapping: Mapping between old and new customer IDs

        Returns:
            List of mappings between old and new ticket IDs
        """
        ticket_id_mapping = []

        for mock_ticket in mock_tickets:
            # Map old customer ID to new customer ID
            old_customer_id = mock_ticket["customer_id"]
            new_customer_id = None

            for mapping in customer_id_mapping:
                if mapping["old_id"] == old_customer_id:
                    new_customer_id = mapping["new_id"]
                    break

            if not new_customer_id:
                logger.error(f"Could not find customer ID mapping for {old_customer_id}")
                continue

            # Transform Phase 1 ticket data to Phase 2 format
            ticket_data = {
                "customer_id": new_customer_id,
                "external_reference": mock_ticket["id"],  # Store Phase 1 ID as external_reference
                "subject": mock_ticket["subject"],
                "description": mock_ticket["description"],
                "status": mock_ticket.get("status", "open"),
                "priority": mock_ticket.get("priority", "medium"),
                "channel": mock_ticket.get("channel", "webform"),
                "created_at": mock_ticket.get("created_at")
            }

            # Check if ticket already exists (based on external_reference)
            # For now, we'll create new tickets assuming they don't exist
            new_ticket = self.db_manager.create_ticket(ticket_data)
            ticket_id_mapping.append({
                "old_id": mock_ticket["id"],
                "new_id": str(new_ticket.id)
            })
            self.migrated_records['tickets'] += 1
            logger.info(f"Migrated ticket: {mock_ticket['subject']}")

        return ticket_id_mapping

    def migrate_messages(self, mock_messages: List[Dict[str, Any]], ticket_id_mapping: List[Dict[str, str]]):
        """
        Migrate messages from Phase 1 structure to Phase 2 PostgreSQL schema.

        Args:
            mock_messages: List of message data from Phase 1
            ticket_id_mapping: Mapping between old and new ticket IDs
        """
        for mock_message in mock_messages:
            # Map old ticket ID to new ticket ID
            old_ticket_id = mock_message["ticket_id"]
            new_ticket_id = None

            for mapping in ticket_id_mapping:
                if mapping["old_id"] == old_ticket_id:
                    new_ticket_id = mapping["new_id"]
                    break

            if not new_ticket_id:
                logger.error(f"Could not find ticket ID mapping for {old_ticket_id}")
                continue

            # Transform Phase 1 message data to Phase 2 format
            message_data = {
                "ticket_id": new_ticket_id,
                "sender_type": mock_message["sender_type"],
                "content": mock_message["content"],
                "direction": mock_message["direction"],
                "sent_at": mock_message.get("timestamp")
            }

            # Create new message
            new_message = self.db_manager.create_message(message_data)
            self.migrated_records['messages'] += 1
            logger.info(f"Migrated message for ticket {new_ticket_id}")

    def run_migration(self):
        """
        Execute the migration from Phase 1 mock data to Phase 2 PostgreSQL schema.
        """
        logger.info("Starting migration from Phase 1 to Phase 2 schema...")

        # Load Phase 1 mock data
        phase1_data = self.load_phase1_mock_data()

        # Migrate customers first (since tickets depend on customers)
        customer_mapping = self.migrate_customers(phase1_data["customers"])

        # Migrate tickets next (since messages depend on tickets)
        ticket_mapping = self.migrate_tickets(phase1_data["tickets"], customer_mapping)

        # Finally migrate messages
        self.migrate_messages(phase1_data["messages"], ticket_mapping)

        logger.info(f"Migration completed successfully!")
        logger.info(f"Records migrated: {self.migrated_records}")

        # Print summary
        print("\nMigration Summary:")
        print(f"- Customers migrated: {self.migrated_records['customers']}")
        print(f"- Tickets migrated: {self.migrated_records['tickets']}")
        print(f"- Messages migrated: {self.migrated_records['messages']}")
        print("\nMigration process completed!")

    def validate_migration(self) -> bool:
        """
        Validate that the migration was successful by checking record counts.

        Returns:
            True if migration appears successful, False otherwise
        """
        logger.info("Validating migration...")

        # Count records in the database
        session = self.db_manager.SessionLocal()
        try:
            customer_count = session.query(Customer).count()
            ticket_count = session.query(Ticket).count()
            message_count = session.query(Message).count()

            logger.info(f"Database contains: {customer_count} customers, {ticket_count} tickets, {message_count} messages")

            # Validate that we have the expected number of records
            expected_customers = self.migrated_records['customers']
            expected_tickets = self.migrated_records['tickets']
            expected_messages = self.migrated_records['messages']

            if (customer_count >= expected_customers and
                ticket_count >= expected_tickets and
                message_count >= expected_messages):

                logger.info("Migration validation PASSED")
                return True
            else:
                logger.error("Migration validation FAILED - unexpected record counts")
                return False

        except Exception as e:
            logger.error(f"Error during migration validation: {e}")
            return False
        finally:
            session.close()


if __name__ == "__main__":
    # Create migration script instance
    migration_script = MigrationScript()

    # Run the migration
    migration_script.run_migration()

    # Validate the migration
    validation_result = migration_script.validate_migration()

    if validation_result:
        print("\n✓ Migration completed and validated successfully!")
    else:
        print("\n✗ Migration validation failed!")