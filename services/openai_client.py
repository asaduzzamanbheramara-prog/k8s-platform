"""
Python client for ShopnoltdToolbox OpenAI Service
"""

import httpx
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class Message:
    """Represents a message in conversation"""
    role: str
    content: str
    timestamp: Optional[str] = None


@dataclass
class ChatResponse:
    """Response from chat completion"""
    conversation_id: str
    response: str
    usage: Dict[str, int]
    model: str
    timestamp: str


@dataclass
class Conversation:
    """Full conversation with history"""
    conversation_id: str
    created_at: str
    updated_at: str
    messages: List[Dict[str, Any]]
    model: str
    system_prompt: Optional[str] = None


@dataclass
class ModelInfo:
    """Information about OpenAI model"""
    name: str
    description: str
    context_window: int
    cost_per_1k_tokens: Dict[str, float]


class OpenAIServiceClient:
    """Client for OpenAI Integration Service"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:3001",
        bearer_token: str = "",
        timeout: float = 30.0
    ):
        """
        Initialize the client
        
        Args:
            base_url: Service base URL
            bearer_token: Bearer token for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.bearer_token = bearer_token
        self.timeout = timeout
        self.headers = {}
        if bearer_token:
            self.headers["Authorization"] = f"Bearer {bearer_token}"
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
    
    async def chat_completion(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_prompt: Optional[str] = None
    ) -> ChatResponse:
        """
        Get chat completion
        
        Args:
            message: User message
            conversation_id: Optional existing conversation ID
            model: OpenAI model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            system_prompt: System prompt override
        
        Returns:
            ChatResponse object
        """
        payload = {
            "message": message,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if conversation_id:
            payload["conversation_id"] = conversation_id
        if system_prompt:
            payload["system_prompt"] = system_prompt
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/chat/completions",
                json=payload,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return ChatResponse(**data)
    
    async def get_conversation_history(
        self,
        conversation_id: str
    ) -> Conversation:
        """
        Retrieve conversation history
        
        Args:
            conversation_id: Conversation ID
        
        Returns:
            Conversation object with full history
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/chat/history/{conversation_id}",
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return Conversation(**data)
    
    async def delete_conversation(
        self,
        conversation_id: str
    ) -> Dict[str, str]:
        """
        Delete conversation history
        
        Args:
            conversation_id: Conversation ID to delete
        
        Returns:
            Status response
        """
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/api/chat/history/{conversation_id}",
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
    
    async def list_models(self) -> List[ModelInfo]:
        """
        List available models
        
        Returns:
            List of available models
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/models",
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return [ModelInfo(**model) for model in data]
    
    async def get_model_info(self, model_name: str) -> ModelInfo:
        """
        Get information about specific model
        
        Args:
            model_name: Name of the model
        
        Returns:
            ModelInfo object
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/models/{model_name}",
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return ModelInfo(**data)


class SyncOpenAIServiceClient(OpenAIServiceClient):
    """Synchronous version of OpenAI Service Client"""
    
    def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        with httpx.Client() as client:
            response = client.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
    
    def chat_completion(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_prompt: Optional[str] = None
    ) -> ChatResponse:
        """Get chat completion (synchronous)"""
        payload = {
            "message": message,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if conversation_id:
            payload["conversation_id"] = conversation_id
        if system_prompt:
            payload["system_prompt"] = system_prompt
        
        with httpx.Client() as client:
            response = client.post(
                f"{self.base_url}/api/chat/completions",
                json=payload,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return ChatResponse(**data)
    
    def get_conversation_history(
        self,
        conversation_id: str
    ) -> Conversation:
        """Retrieve conversation history (synchronous)"""
        with httpx.Client() as client:
            response = client.get(
                f"{self.base_url}/api/chat/history/{conversation_id}",
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return Conversation(**data)
    
    def delete_conversation(
        self,
        conversation_id: str
    ) -> Dict[str, str]:
        """Delete conversation history (synchronous)"""
        with httpx.Client() as client:
            response = client.delete(
                f"{self.base_url}/api/chat/history/{conversation_id}",
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
    
    def list_models(self) -> List[ModelInfo]:
        """List available models (synchronous)"""
        with httpx.Client() as client:
            response = client.get(
                f"{self.base_url}/api/models",
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return [ModelInfo(**model) for model in data]
    
    def get_model_info(self, model_name: str) -> ModelInfo:
        """Get information about specific model (synchronous)"""
        with httpx.Client() as client:
            response = client.get(
                f"{self.base_url}/api/models/{model_name}",
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return ModelInfo(**data)


# Example usage
async def async_example():
    """Example: Using async client"""
    client = OpenAIServiceClient(
        base_url="http://localhost:3001",
        bearer_token="your-token"
    )
    
    # Check health
    health = await client.health_check()
    print(f"Service status: {health['status']}")
    
    # Get chat response
    response = await client.chat_completion(
        message="What is machine learning?",
        model="gpt-3.5-turbo"
    )
    print(f"Response: {response.response}")
    print(f"Conversation ID: {response.conversation_id}")
    print(f"Tokens used: {response.usage['total_tokens']}")
    
    # Continue conversation
    response2 = await client.chat_completion(
        message="Tell me more about supervised learning",
        conversation_id=response.conversation_id
    )
    print(f"Response: {response2.response}")


def sync_example():
    """Example: Using sync client"""
    client = SyncOpenAIServiceClient(
        base_url="http://localhost:3001",
        bearer_token="your-token"
    )
    
    # Get chat response
    response = client.chat_completion(
        message="Hello! How can I help you today?"
    )
    print(f"Response: {response.response}")


if __name__ == "__main__":
    # Run async example
    import asyncio
    asyncio.run(async_example())
