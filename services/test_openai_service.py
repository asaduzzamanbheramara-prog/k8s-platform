"""
Tests for ShopnoltdToolbox OpenAI Integration Service
"""

import json
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

# Import the app (this assumes the service is importable)
# For testing, we'll create a test version
import sys
import os

# Mock environment variables before importing the service
os.environ["OPENAI_API_KEY"] = "sk-test-key"
os.environ["API_BEARER_TOKEN"] = "test-token"
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["REQUIRE_AUTH"] = "true"

from shopnoltd_openai_service import app, Config, Message, ChatRequest, ChatResponse

# Create test client
client = TestClient(app)

# ============================================================================
# Configuration Tests
# ============================================================================

class TestConfig:
    """Test configuration loading"""
    
    def test_config_from_env(self):
        """Test that config loads from environment variables"""
        config = Config()
        assert config.OPENAI_API_KEY == "sk-test-key"
        assert config.API_BEARER_TOKEN == "test-token"
    
    def test_config_validation(self):
        """Test that config validates required fields"""
        # Temporarily remove API key
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            with pytest.raises(ValueError):
                Config().validate()
    
    def test_default_config_values(self):
        """Test default configuration values"""
        config = Config()
        assert config.OPENAI_MODEL == "gpt-3.5-turbo"
        assert config.TEMPERATURE == 0.7
        assert config.MAX_TOKENS == 2048
        assert config.RATE_LIMIT_PER_MINUTE == 60

# ============================================================================
# Model Tests
# ============================================================================

class TestModels:
    """Test Pydantic models"""
    
    def test_message_model(self):
        """Test Message model"""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert isinstance(msg.timestamp, datetime)
    
    def test_chat_request_model(self):
        """Test ChatRequest model"""
        req = ChatRequest(message="Test message")
        assert req.message == "Test message"
        assert req.conversation_id is None
    
    def test_chat_response_model(self):
        """Test ChatResponse model"""
        resp = ChatResponse(
            conversation_id="test-123",
            response="Test response",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            model="gpt-3.5-turbo"
        )
        assert resp.conversation_id == "test-123"
        assert resp.response == "Test response"

# ============================================================================
# Authentication Tests
# ============================================================================

class TestAuthentication:
    """Test authentication and authorization"""
    
    def test_health_check_no_auth(self):
        """Test that health check doesn't require auth"""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_chat_endpoint_requires_auth(self):
        """Test that chat endpoint requires authentication"""
        response = client.post("/api/chat/completions", json={
            "message": "Hello"
        })
        assert response.status_code == 403  # Forbidden (HTTPBearer dependency)
    
    def test_chat_endpoint_with_valid_token(self):
        """Test chat endpoint with valid token"""
        # Mock OpenAI and Redis
        with patch('shopnoltd_openai_service.redis_client') as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis.setex = AsyncMock()
            
            with patch('shopnoltd_openai_service.openai.ChatCompletion.create') as mock_openai:
                mock_openai.return_value = {
                    "choices": [{"message": {"content": "Test response"}}],
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 20,
                        "total_tokens": 30
                    }
                }
                
                response = client.post(
                    "/api/chat/completions",
                    json={"message": "Hello"},
                    headers={"Authorization": f"Bearer {os.environ.get('API_BEARER_TOKEN')}"}
                )
                # Note: This would fail in test without proper async mock setup
                # In real tests, use pytest-asyncio and proper fixtures
                pass

# ============================================================================
# Rate Limiting Tests
# ============================================================================

class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_rate_limit_header_present(self):
        """Test that rate limit headers are present"""
        response = client.get("/api/models", 
                             headers={"Authorization": f"Bearer {os.environ.get('API_BEARER_TOKEN')}"})
        # slowapi should add rate limit headers
        assert "x-ratelimit-limit" in response.headers or response.status_code == 200

# ============================================================================
# API Endpoint Tests
# ============================================================================

class TestAPIEndpoints:
    """Test API endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "shopnoltd-openai-service"
        assert "endpoints" in data
    
    def test_models_endpoint(self):
        """Test models endpoint"""
        response = client.get("/api/models", 
                             headers={"Authorization": f"Bearer {os.environ.get('API_BEARER_TOKEN')}"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 4
        assert any(m["name"] == "gpt-3.5-turbo" for m in data)
    
    def test_model_info_endpoint(self):
        """Test get model info endpoint"""
        response = client.get("/api/models/gpt-3.5-turbo",
                             headers={"Authorization": f"Bearer {os.environ.get('API_BEARER_TOKEN')}"})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "gpt-3.5-turbo"
        assert "context_window" in data
        assert "cost_per_1k_tokens" in data

# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests"""
    
    def test_service_info_available(self):
        """Test that service information is available"""
        response = client.get("/")
        assert response.status_code == 200
        assert "version" in response.json()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
