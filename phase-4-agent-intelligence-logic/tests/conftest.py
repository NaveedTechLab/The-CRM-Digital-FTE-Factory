import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

# Enable asyncio support for pytest
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Mock the OpenAI client globally for all tests
@pytest.fixture(autouse=True)
def mock_openai_client():
    with patch('app.services.openai_agent.OpenAI') as mock_client:
        yield mock_client

# Mock the database engine globally
@pytest.fixture(autouse=True)
def mock_db_engine():
    with patch('app.services.agent_orchestrator.create_engine') as mock_engine, \
         patch('app.services.agent_orchestrator.sessionmaker') as mock_sessionmaker:

        # Mock engine and session behavior
        mock_session = Mock()
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.refresh = Mock()
        mock_session.query = Mock()

        # Mock query chain
        mock_query_result = Mock()
        mock_query_result.first = Mock(return_value=None)
        mock_query_result.fetchall = Mock(return_value=[])
        mock_session.query.return_value.filter.return_value = mock_query_result

        mock_sessionmaker.return_value.return_value.__enter__ = Mock(return_value=mock_session)
        mock_sessionmaker.return_value.return_value.__exit__ = Mock(return_value=None)

        yield mock_engine, mock_sessionmaker