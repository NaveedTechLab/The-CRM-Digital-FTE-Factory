import pytest
from unittest.mock import Mock, patch, MagicMock


class TestRAGService:

    @pytest.fixture
    def rag_service(self):
        with patch('app.services.rag_service.OpenAI') as mock_openai, \
             patch('app.services.rag_service.create_engine') as mock_engine, \
             patch('app.services.rag_service.sessionmaker') as mock_session:
            from app.services.rag_service import RAGService
            service = RAGService()
            service.client = mock_openai.return_value
            return service

    def test_get_embedding(self, rag_service):
        """Test getting embedding from OpenAI"""
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3]

        rag_service.client.embeddings.create.return_value = mock_response

        result = rag_service.get_embedding("test text")

        assert result == [0.1, 0.2, 0.3]
        rag_service.client.embeddings.create.assert_called_once()

    def test_similarity_search(self, rag_service):
        """Test similarity search"""
        # Mock the embedding response
        mock_emb_response = Mock()
        mock_emb_response.data = [Mock()]
        mock_emb_response.data[0].embedding = [0.1, 0.2, 0.3]
        rag_service.client.embeddings.create.return_value = mock_emb_response

        # Mock the database session and query results
        mock_session = Mock()
        mock_query_result = Mock()
        mock_query_result.fetchall.return_value = [
            ('id1', 'title1', 'content1', 'summary1', 'category1', 0.8)
        ]
        mock_session.execute.return_value = mock_query_result
        rag_service.SessionLocal = Mock(return_value=mock_session)

        results = rag_service.similarity_search("test query", top_k=1, min_similarity=0.5)

        assert len(results) == 1
        assert results[0]['id'] == 'id1'
        assert results[0]['title'] == 'title1'
        assert results[0]['similarity_score'] == 0.8

    def test_calculate_relevance_score(self, rag_service):
        """Test relevance score calculation"""
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.5, 0.5]
        rag_service.client.embeddings.create.return_value = mock_response

        score = rag_service.calculate_relevance_score("test", "test")

        assert 0.0 <= score <= 1.0

    def test_get_embedding_error(self, rag_service):
        """Test embedding error handling"""
        rag_service.client.embeddings.create.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            rag_service.get_embedding("test text")
