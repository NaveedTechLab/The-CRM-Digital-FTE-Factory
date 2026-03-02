"""
DatabaseManager class for PostgreSQL operations using SQLAlchemy.
Handles connection pooling and CRUD operations for the Customer Success Digital FTE.
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, Index, func, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.pool import QueuePool
from sqlalchemy.sql import expression
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class Customer(Base):
    __tablename__ = 'customers'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String(255), unique=True, nullable=True)
    name = Column(String(255), nullable=False)
    email = Column(String(320), unique=True, nullable=False)
    phone = Column(String(20), nullable=True)
    contact_preferences = Column(JSONB, default=lambda: {})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_interaction = Column(DateTime(timezone=True), nullable=True)

    # Relationship to tickets
    tickets = relationship("Ticket", back_populates="customer")

    def to_dict(self):
        return {
            'id': str(self.id),
            'external_id': self.external_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'contact_preferences': self.contact_preferences,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_interaction': self.last_interaction.isoformat() if self.last_interaction else None
        }

class Ticket(Base):
    __tablename__ = 'tickets'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id'), nullable=False)
    external_reference = Column(String(255), unique=True, nullable=True)
    subject = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), default='open', server_default='open')
    priority = Column(String(50), default='medium', server_default='medium')
    channel = Column(String(50), default='webform', server_default='webform')
    assigned_agent = Column(String(255), nullable=True)
    sla_deadline = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship to customer
    customer = relationship("Customer", back_populates="tickets")
    # Relationship to messages
    messages = relationship("Message", back_populates="ticket")

    def to_dict(self):
        return {
            'id': str(self.id),
            'customer_id': str(self.customer_id),
            'external_reference': self.external_reference,
            'subject': self.subject,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'channel': self.channel,
            'assigned_agent': self.assigned_agent,
            'sla_deadline': self.sla_deadline.isoformat() if self.sla_deadline else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }

class Message(Base):
    __tablename__ = 'messages'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey('tickets.id'), nullable=False)
    sender_type = Column(String(50), nullable=False)  # 'customer', 'agent', 'system'
    sender_id = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    content_type = Column(String(50), default='text', server_default='text')
    direction = Column(String(50), nullable=False)  # 'inbound', 'outbound'
    channel_metadata = Column(JSONB, default=lambda: {})
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    received_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship to ticket
    ticket = relationship("Ticket", back_populates="messages")

    def to_dict(self):
        return {
            'id': str(self.id),
            'ticket_id': str(self.ticket_id),
            'sender_type': self.sender_type,
            'sender_id': self.sender_id,
            'content': self.content,
            'content_type': self.content_type,
            'direction': self.direction,
            'channel_metadata': self.channel_metadata,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'received_at': self.received_at.isoformat() if self.received_at else None
        }

class CustomerIdentifier(Base):
    __tablename__ = 'customer_identifiers'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id'), nullable=False)
    channel = Column(String(50), nullable=False)
    identifier_value = Column(String(320), nullable=False)
    identifier_type = Column(String(50), nullable=False)
    is_primary = Column(String(5), default='false')
    verified = Column(String(5), default='false')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customer = relationship("Customer", backref="identifiers")

    def to_dict(self):
        return {
            'id': str(self.id),
            'customer_id': str(self.customer_id),
            'channel': self.channel,
            'identifier_value': self.identifier_value,
            'identifier_type': self.identifier_type,
            'is_primary': self.is_primary,
            'verified': self.verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Conversation(Base):
    __tablename__ = 'conversations'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id'), nullable=False)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey('tickets.id'), nullable=True)
    channel = Column(String(50), nullable=False)
    status = Column(String(50), default='active', server_default='active')
    subject = Column(String(500), nullable=True)
    thread_id = Column(String(255), nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_message_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    metadata = Column(JSONB, default=lambda: {})

    customer = relationship("Customer", backref="conversations")
    ticket = relationship("Ticket", backref="conversations")

    def to_dict(self):
        return {
            'id': str(self.id),
            'customer_id': str(self.customer_id),
            'ticket_id': str(self.ticket_id) if self.ticket_id else None,
            'channel': self.channel,
            'status': self.status,
            'subject': self.subject,
            'thread_id': self.thread_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'last_message_at': self.last_message_at.isoformat() if self.last_message_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None
        }


class KnowledgeBase(Base):
    __tablename__ = 'knowledge_base'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    status = Column(String(50), default='published', server_default='published')
    version = Column(Integer, default=1)
    author = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            'id': str(self.id),
            'title': self.title,
            'content': self.content,
            'category': self.category,
            'status': self.status,
            'version': self.version,
            'author': self.author,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ChannelConfig(Base):
    __tablename__ = 'channel_configs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    channel = Column(String(50), unique=True, nullable=False)
    is_active = Column(String(5), default='true')
    config = Column(JSONB, default=lambda: {})
    rate_limit_per_minute = Column(Integer, default=100)
    webhook_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            'id': str(self.id),
            'channel': self.channel,
            'is_active': self.is_active,
            'config': self.config,
            'rate_limit_per_minute': self.rate_limit_per_minute,
            'webhook_url': self.webhook_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AgentMetric(Base):
    __tablename__ = 'agent_metrics'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_type = Column(String(100), nullable=False)
    metric_value = Column(String(50), nullable=False)
    channel = Column(String(50), nullable=True)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey('tickets.id'), nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    metadata = Column(JSONB, default=lambda: {})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            'id': str(self.id),
            'metric_type': self.metric_type,
            'metric_value': self.metric_value,
            'channel': self.channel,
            'ticket_id': str(self.ticket_id) if self.ticket_id else None,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class VectorEmbedding(Base):
    __tablename__ = 'vector_embeddings'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(100), nullable=False)  # 'customer', 'ticket', 'message', 'knowledge_base'
    entity_id = Column(String(255), nullable=False)
    # Using Text for embedding since we'll handle the vector operations via raw SQL
    embedding = Column(Text, nullable=True)  # Will be stored as a string representation
    content_preview = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            'id': str(self.id),
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'embedding': self.embedding,
            'content_preview': self.content_preview,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class DatabaseManager:
    """
    Database Manager class using SQLAlchemy for PostgreSQL operations.
    Handles connection pooling and CRUD operations.
    """

    def __init__(self, database_url: str = "postgresql://postgres:postgres@localhost:5432/internal_crm"):
        """
        Initialize the DatabaseManager with connection parameters.

        Args:
            database_url: PostgreSQL connection string
        """
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600
        )

        # Create tables
        Base.metadata.create_all(self.engine)

        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        logger.info("DatabaseManager initialized with connection pooling")

    def get_session(self):
        """
        Get a database session.

        Yields:
            Database session
        """
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()

    # Customer CRUD operations
    def create_customer(self, customer_data: Dict[str, Any]) -> Customer:
        """
        Create a new customer in the database.

        Args:
            customer_data: Dictionary with customer information

        Returns:
            Created Customer object
        """
        session = self.SessionLocal()
        try:
            customer = Customer(**customer_data)
            session.add(customer)
            session.commit()
            session.refresh(customer)
            logger.info(f"Created customer with ID: {customer.id}")
            return customer
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating customer: {e}")
            raise
        finally:
            session.close()

    def get_customer_by_id(self, customer_id: str) -> Optional[Customer]:
        """
        Retrieve a customer by ID.

        Args:
            customer_id: UUID string of the customer

        Returns:
            Customer object or None if not found
        """
        session = self.SessionLocal()
        try:
            customer = session.query(Customer).filter(Customer.id == customer_id).first()
            return customer
        finally:
            session.close()

    def get_customer_by_email(self, email: str) -> Optional[Customer]:
        """
        Retrieve a customer by email.

        Args:
            email: Email address of the customer

        Returns:
            Customer object or None if not found
        """
        session = self.SessionLocal()
        try:
            customer = session.query(Customer).filter(Customer.email == email).first()
            return customer
        finally:
            session.close()

    def get_customer_by_phone(self, phone: str) -> Optional[Customer]:
        """
        Retrieve a customer by phone number.

        Args:
            phone: Phone number of the customer

        Returns:
            Customer object or None if not found
        """
        session = self.SessionLocal()
        try:
            customer = session.query(Customer).filter(Customer.phone == phone).first()
            return customer
        finally:
            session.close()

    def update_customer(self, customer_id: str, update_data: Dict[str, Any]) -> Optional[Customer]:
        """
        Update an existing customer.

        Args:
            customer_id: UUID string of the customer to update
            update_data: Dictionary with fields to update

        Returns:
            Updated Customer object or None if not found
        """
        session = self.SessionLocal()
        try:
            customer = session.query(Customer).filter(Customer.id == customer_id).first()
            if customer:
                for key, value in update_data.items():
                    if hasattr(customer, key):
                        setattr(customer, key, value)
                session.commit()
                session.refresh(customer)
                logger.info(f"Updated customer with ID: {customer.id}")
            return customer
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating customer: {e}")
            raise
        finally:
            session.close()

    def delete_customer(self, customer_id: str) -> bool:
        """
        Delete a customer by ID.

        Args:
            customer_id: UUID string of the customer to delete

        Returns:
            True if deleted, False if not found
        """
        session = self.SessionLocal()
        try:
            customer = session.query(Customer).filter(Customer.id == customer_id).first()
            if customer:
                session.delete(customer)
                session.commit()
                logger.info(f"Deleted customer with ID: {customer.id}")
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting customer: {e}")
            raise
        finally:
            session.close()

    # Ticket CRUD operations
    def create_ticket(self, ticket_data: Dict[str, Any]) -> Ticket:
        """
        Create a new ticket in the database.

        Args:
            ticket_data: Dictionary with ticket information

        Returns:
            Created Ticket object
        """
        session = self.SessionLocal()
        try:
            ticket = Ticket(**ticket_data)
            session.add(ticket)
            session.commit()
            session.refresh(ticket)
            logger.info(f"Created ticket with ID: {ticket.id}")
            return ticket
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating ticket: {e}")
            raise
        finally:
            session.close()

    def get_ticket_by_id(self, ticket_id: str) -> Optional[Ticket]:
        """
        Retrieve a ticket by ID.

        Args:
            ticket_id: UUID string of the ticket

        Returns:
            Ticket object or None if not found
        """
        session = self.SessionLocal()
        try:
            ticket = session.query(Ticket).filter(Ticket.id == ticket_id).first()
            return ticket
        finally:
            session.close()

    def get_tickets_by_customer_id(self, customer_id: str) -> List[Ticket]:
        """
        Retrieve all tickets for a customer.

        Args:
            customer_id: UUID string of the customer

        Returns:
            List of Ticket objects
        """
        session = self.SessionLocal()
        try:
            tickets = session.query(Ticket).filter(Ticket.customer_id == customer_id).all()
            return tickets
        finally:
            session.close()

    def update_ticket(self, ticket_id: str, update_data: Dict[str, Any]) -> Optional[Ticket]:
        """
        Update an existing ticket.

        Args:
            ticket_id: UUID string of the ticket to update
            update_data: Dictionary with fields to update

        Returns:
            Updated Ticket object or None if not found
        """
        session = self.SessionLocal()
        try:
            ticket = session.query(Ticket).filter(Ticket.id == ticket_id).first()
            if ticket:
                for key, value in update_data.items():
                    if hasattr(ticket, key):
                        setattr(ticket, key, value)
                session.commit()
                session.refresh(ticket)
                logger.info(f"Updated ticket with ID: {ticket.id}")
            return ticket
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating ticket: {e}")
            raise
        finally:
            session.close()

    # Message/Interaction CRUD operations
    def create_message(self, message_data: Dict[str, Any]) -> Message:
        """
        Create a new message in the database.

        Args:
            message_data: Dictionary with message information

        Returns:
            Created Message object
        """
        session = self.SessionLocal()
        try:
            message = Message(**message_data)
            session.add(message)
            session.commit()
            session.refresh(message)
            logger.info(f"Created message with ID: {message.id}")
            return message
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating message: {e}")
            raise
        finally:
            session.close()

    def get_messages_by_ticket_id(self, ticket_id: str) -> List[Message]:
        """
        Retrieve all messages for a ticket.

        Args:
            ticket_id: UUID string of the ticket

        Returns:
            List of Message objects
        """
        session = self.SessionLocal()
        try:
            messages = session.query(Message).filter(Message.ticket_id == ticket_id).all()
            return messages
        finally:
            session.close()

    # Vector Embedding operations
    def create_vector_embedding(self, embedding_data: Dict[str, Any]) -> VectorEmbedding:
        """
        Create a new vector embedding in the database.

        Args:
            embedding_data: Dictionary with embedding information

        Returns:
            Created VectorEmbedding object
        """
        session = self.SessionLocal()
        try:
            embedding = VectorEmbedding(**embedding_data)
            session.add(embedding)
            session.commit()
            session.refresh(embedding)
            logger.info(f"Created vector embedding with ID: {embedding.id}")
            return embedding
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating vector embedding: {e}")
            raise
        finally:
            session.close()

    def get_vector_embeddings_by_entity(self, entity_type: str, entity_id: str) -> List[VectorEmbedding]:
        """
        Retrieve vector embeddings for a specific entity.

        Args:
            entity_type: Type of entity ('customer', 'ticket', 'message', 'knowledge_base')
            entity_id: ID of the entity

        Returns:
            List of VectorEmbedding objects
        """
        session = self.SessionLocal()
        try:
            embeddings = session.query(VectorEmbedding)\
                               .filter(VectorEmbedding.entity_type == entity_type)\
                               .filter(VectorEmbedding.entity_id == entity_id)\
                               .all()
            return embeddings
        finally:
            session.close()

    def similarity_search(self, query_embedding: List[float], entity_type: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform a similarity search using vector embeddings.
        This requires raw SQL since SQLAlchemy doesn't have native pgvector support.

        Args:
            query_embedding: List of floats representing the query embedding
            entity_type: Optional entity type to filter results
            top_k: Number of top results to return

        Returns:
            List of dictionaries with search results
        """
        # Convert query embedding to string format for SQL
        query_str = "[" + ",".join(map(str, query_embedding)) + "]"

        sql = """
        SELECT id, entity_type, entity_id, content_preview,
               embedding <-> %s AS distance
        FROM vector_embeddings
        """

        params = [query_str]

        if entity_type:
            sql += "WHERE entity_type = %s "
            params.append(entity_type)

        sql += "ORDER BY embedding <-> %s LIMIT %s;"
        params.extend([query_str, top_k])

        session = self.SessionLocal()
        try:
            result = session.execute(text(sql), params)
            rows = result.fetchall()

            results = []
            for row in rows:
                results.append({
                    'id': str(row[0]),
                    'entity_type': row[1],
                    'entity_id': row[2],
                    'content_preview': row[3],
                    'distance': float(row[4])  # Distance in vector space (lower is more similar)
                })

            return results
        except Exception as e:
            logger.error(f"Error performing similarity search: {e}")
            raise
        finally:
            session.close()

    def health_check(self) -> bool:
        """
        Perform a health check on the database connection.

        Returns:
            True if database is accessible and tables exist, False otherwise
        """
        session = self.SessionLocal()
        try:
            # Test connection by querying the database version
            result = session.execute(text("SELECT version();"))
            version = result.fetchone()
            if version:
                logger.info("Database connection is healthy")
                return True
            return False
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
        finally:
            session.close()