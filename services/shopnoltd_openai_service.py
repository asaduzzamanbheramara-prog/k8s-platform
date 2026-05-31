"""
ShopnoltdToolbox OpenAI Integration Service
Production-ready FastAPI service for OpenAI chat completions with conversation management
"""

import os
import logging
import json
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from functools import lru_cache
from contextlib import asynccontextmanager

import aioredis
import openai
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration & Models
# ============================================================================

class Config:
    """Service configuration from environment variables"""
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    OPENAI_MODELS: List[str] = [
        "gpt-4",
        "gpt-4-turbo-preview",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k"
    ]
    TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "2048"))
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    # Redis configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    CONVERSATION_TTL_HOURS: int = int(os.getenv("CONVERSATION_TTL_HOURS", "24"))
    
    # Authentication
    API_BEARER_TOKEN: str = os.getenv("API_BEARER_TOKEN")
    REQUIRE_AUTH: bool = os.getenv("REQUIRE_AUTH", "true").lower() == "true"
    
    # CORS
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    
    def validate(self):
        """Validate required configuration"""
        if not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        if self.REQUIRE_AUTH and not self.API_BEARER_TOKEN:
            raise ValueError("API_BEARER_TOKEN required when REQUIRE_AUTH=true")

config = Config()
config.validate()

# Initialize OpenAI
openai.api_key = config.OPENAI_API_KEY

# Request/Response Models
class Message(BaseModel):
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID (omit for new)")
    model: Optional[str] = Field(default=config.OPENAI_MODEL)
    temperature: Optional[float] = Field(default=config.TEMPERATURE)
    max_tokens: Optional[int] = Field(default=config.MAX_TOKENS)
    system_prompt: Optional[str] = Field(None, description="System prompt override")

class ChatResponse(BaseModel):
    conversation_id: str
    response: str
    usage: Dict[str, int] = Field(..., description="Token usage stats")
    model: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Conversation(BaseModel):
    conversation_id: str
    created_at: datetime
    updated_at: datetime
    messages: List[Message]
    model: str
    system_prompt: Optional[str] = None

class ModelInfo(BaseModel):
    name: str
    description: str
    context_window: int
    cost_per_1k_tokens: Dict[str, float]

# ============================================================================
# Service Dependencies
# ============================================================================

redis_client: Optional[aioredis.Redis] = None
limiter = Limiter(key_func=get_remote_address)
security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify API bearer token"""
    if not config.REQUIRE_AUTH:
        return "public"
    
    if credentials.credentials != config.API_BEARER_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return credentials.credentials

async def get_redis() -> aioredis.Redis:
    """Get Redis connection"""
    if redis_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis service unavailable"
        )
    return redis_client

# ============================================================================
# Conversation Management
# ============================================================================

class ConversationManager:
    """Manage conversation history in Redis"""
    
    def __init__(self, redis: aioredis.Redis):
        self.redis = redis
        self.ttl = config.CONVERSATION_TTL_HOURS * 3600
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Retrieve conversation from Redis"""
        try:
            data = await self.redis.get(f"conversation:{conversation_id}")
            if data:
                return Conversation(**json.loads(data))
        except Exception as e:
            logger.error(f"Error retrieving conversation {conversation_id}: {e}")
        return None
    
    async def save_conversation(self, conversation: Conversation) -> None:
        """Save conversation to Redis with TTL"""
        try:
            await self.redis.setex(
                f"conversation:{conversation.conversation_id}",
                self.ttl,
                json.dumps(
                    conversation.dict(),
                    default=lambda x: x.isoformat() if isinstance(x, datetime) else str(x)
                )
            )
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            raise
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation from Redis"""
        try:
            result = await self.redis.delete(f"conversation:{conversation_id}")
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {e}")
            return False
    
    async def create_conversation(
        self,
        model: str,
        system_prompt: Optional[str] = None
    ) -> Conversation:
        """Create new conversation"""
        now = datetime.utcnow()
        conversation = Conversation(
            conversation_id=str(uuid.uuid4()),
            created_at=now,
            updated_at=now,
            messages=[],
            model=model,
            system_prompt=system_prompt
        )
        await self.save_conversation(conversation)
        return conversation

# ============================================================================
# OpenAI Integration
# ============================================================================

class OpenAIClient:
    """Wrapper for OpenAI API with retry logic and error handling"""
    
    MAX_RETRIES = 3
    RETRY_DELAY = 1
    
    async def get_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = config.OPENAI_MODEL,
        temperature: float = config.TEMPERATURE,
        max_tokens: int = config.MAX_TOKENS
    ) -> Dict[str, Any]:
        """Get chat completion from OpenAI with retry logic"""
        
        for attempt in range(self.MAX_RETRIES):
            try:
                logger.info(f"OpenAI request - Model: {model}, Tokens: {max_tokens}")
                
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                logger.info(f"OpenAI success - Usage: {response['usage']}")
                return response
                
            except openai.error.RateLimitError as e:
                logger.warning(f"Rate limit hit (attempt {attempt + 1}/{self.MAX_RETRIES}): {e}")
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
                else:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="OpenAI API rate limit exceeded"
                    )
            
            except openai.error.AuthenticationError as e:
                logger.error(f"OpenAI authentication failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="OpenAI API authentication failed"
                )
            
            except openai.error.APIError as e:
                logger.error(f"OpenAI API error (attempt {attempt + 1}/{self.MAX_RETRIES}): {e}")
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
                else:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="OpenAI API error"
                    )
    
    def count_tokens(self, text: str) -> int:
        """Estimate token count"""
        return len(text) // 4
    
    def get_model_context_window(self, model: str) -> int:
        """Get context window size for model"""
        windows = {
            "gpt-4": 8192,
            "gpt-4-turbo-preview": 128000,
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384
        }
        return windows.get(model, 4096)

# ============================================================================
# Application Setup
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager"""
    global redis_client
    
    # Startup
    try:
        redis_client = await aioredis.create_redis_pool(config.REDIS_URL)
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
        logger.warning("Running without conversation persistence")
    
    yield
    
    # Shutdown
    if redis_client:
        redis_client.close()
        await redis_client.wait_closed()
        logger.info("Redis connection closed")

app = FastAPI(
    title="ShopnoltdToolbox OpenAI Service",
    description="Production-ready OpenAI integration with conversation management",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting error handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": f"Rate limit exceeded: {exc.detail}"}
    )

# Initialize services
openai_client = OpenAIClient()

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "shopnoltd-openai-service",
        "version": "1.0.0",
        "redis": redis_client is not None
    }

@app.post("/api/chat/completions", response_model=ChatResponse)
@limiter.limit(f"{config.RATE_LIMIT_PER_MINUTE}/minute")
async def chat_completions(
    request: Request,
    chat_request: ChatRequest,
    token: str = Depends(verify_token),
    redis: aioredis.Redis = Depends(get_redis)
):
    """Send message and get OpenAI response"""
    
    try:
        manager = ConversationManager(redis)
        
        # Get or create conversation
        if chat_request.conversation_id:
            conversation = await manager.get_conversation(chat_request.conversation_id)
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Conversation {chat_request.conversation_id} not found"
                )
        else:
            conversation = await manager.create_conversation(
                model=chat_request.model,
                system_prompt=chat_request.system_prompt
            )
        
        # Add user message
        conversation.messages.append(
            Message(role="user", content=chat_request.message)
        )
        
        # Build messages for API
        messages = []
        if conversation.system_prompt:
            messages.append({
                "role": "system",
                "content": conversation.system_prompt
            })
        
        for msg in conversation.messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Get OpenAI response
        response = await openai_client.get_chat_completion(
            messages=messages,
            model=conversation.model,
            temperature=chat_request.temperature or config.TEMPERATURE,
            max_tokens=chat_request.max_tokens or config.MAX_TOKENS
        )
        
        # Extract response
        assistant_message = response["choices"][0]["message"]["content"]
        usage = response["usage"]
        
        # Save assistant response to conversation
        conversation.messages.append(
            Message(role="assistant", content=assistant_message)
        )
        conversation.updated_at = datetime.utcnow()
        
        # Save conversation
        await manager.save_conversation(conversation)
        
        logger.info(
            f"Chat completion - Conversation: {conversation.conversation_id}, "
            f"Input tokens: {usage['prompt_tokens']}, "
            f"Output tokens: {usage['completion_tokens']}"
        )
        
        return ChatResponse(
            conversation_id=conversation.conversation_id,
            response=assistant_message,
            usage={
                "prompt_tokens": usage["prompt_tokens"],
                "completion_tokens": usage["completion_tokens"],
                "total_tokens": usage["total_tokens"]
            },
            model=conversation.model
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat completion error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/api/chat/history/{conversation_id}", response_model=Conversation)
@limiter.limit(f"{config.RATE_LIMIT_PER_MINUTE}/minute")
async def get_conversation_history(
    request: Request,
    conversation_id: str,
    token: str = Depends(verify_token),
    redis: aioredis.Redis = Depends(get_redis)
):
    """Retrieve conversation history"""
    try:
        manager = ConversationManager(redis)
        conversation = await manager.get_conversation(conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        logger.info(f"Retrieved conversation {conversation_id}")
        return conversation
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.delete("/api/chat/history/{conversation_id}")
@limiter.limit(f"{config.RATE_LIMIT_PER_MINUTE}/minute")
async def delete_conversation_history(
    request: Request,
    conversation_id: str,
    token: str = Depends(verify_token),
    redis: aioredis.Redis = Depends(get_redis)
):
    """Delete conversation history"""
    try:
        manager = ConversationManager(redis)
        deleted = await manager.delete_conversation(conversation_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        logger.info(f"Deleted conversation {conversation_id}")
        return {"status": "deleted", "conversation_id": conversation_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/api/models", response_model=List[ModelInfo])
@limiter.limit(f"{config.RATE_LIMIT_PER_MINUTE}/minute")
async def list_models(
    request: Request,
    token: str = Depends(verify_token)
):
    """List available OpenAI models"""
    models = [
        ModelInfo(
            name="gpt-4",
            description="Most capable model, slower, more expensive",
            context_window=8192,
            cost_per_1k_tokens={"prompt": 0.03, "completion": 0.06}
        ),
        ModelInfo(
            name="gpt-4-turbo-preview",
            description="Faster GPT-4 with 128K context window",
            context_window=128000,
            cost_per_1k_tokens={"prompt": 0.01, "completion": 0.03}
        ),
        ModelInfo(
            name="gpt-3.5-turbo",
            description="Fast and cost-effective model",
            context_window=4096,
            cost_per_1k_tokens={"prompt": 0.0005, "completion": 0.0015}
        ),
        ModelInfo(
            name="gpt-3.5-turbo-16k",
            description="GPT-3.5-turbo with 16K context window",
            context_window=16384,
            cost_per_1k_tokens={"prompt": 0.003, "completion": 0.004}
        )
    ]
    return models

@app.get("/api/models/{model_name}")
@limiter.limit(f"{config.RATE_LIMIT_PER_MINUTE}/minute")
async def get_model_info(
    request: Request,
    model_name: str,
    token: str = Depends(verify_token)
):
    """Get information about specific model"""
    models = await list_models(request, token)
    for model in models:
        if model.name == model_name:
            return model
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Model {model_name} not found"
    )

@app.get("/")
async def root():
    """Service information"""
    return {
        "service": "shopnoltd-openai-service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "chat": {
                "post_message": "POST /api/chat/completions",
                "get_history": "GET /api/chat/history/{conversation_id}",
                "delete_history": "DELETE /api/chat/history/{conversation_id}"
            },
            "models": {
                "list_models": "GET /api/models",
                "get_model_info": "GET /api/models/{model_name}"
            }
        },
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("SERVICE_HOST", "0.0.0.0")
    port = int(os.getenv("SERVICE_PORT", "3001"))
    
    logger.info(f"Starting OpenAI Service on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
