import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for pytest-asyncio."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def setup_logging():
    """Set up logging for tests."""
    import logging
    logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def mock_kafka_producer():
    """Mock Kafka producer for testing."""
    mock_producer = AsyncMock()
    mock_producer.start = AsyncMock()
    mock_producer.stop = AsyncMock()
    mock_producer.send_and_wait = AsyncMock()

    return mock_producer


@pytest.fixture
def mock_database_manager():
    """Mock DatabaseManager for testing."""
    mock_db = MagicMock()
    mock_db.get_customer_by_identifier = AsyncMock(return_value=None)
    mock_db.create_customer = AsyncMock()

    return mock_db