# OpenAI Service Integration Guide

This guide explains how to integrate and use the OpenAI service in ShopnoltdToolbox.

## Overview

The OpenAI service provides:
- Chat completions with conversation history
- Multiple model support (GPT-4, GPT-3.5-turbo)
- Redis-backed conversation persistence
- Bearer token authentication
- Rate limiting and error handling

## Prerequisites

- Redis instance (for conversation storage)
- OpenAI API key from https://platform.openai.com/api-keys
- Python 3.11+
- Kubernetes cluster (for K8s deployment)

## Installation & Setup

### 1. Environment Configuration

Create a `.env` file in the project root:

```bash
cp services/.env.example .env
```

Edit `.env` with your values:
```env
OPENAI_API_KEY=sk-your-actual-openai-api-key
API_BEARER_TOKEN=your-secret-api-token
REDIS_URL=redis://redis:6379
OPENAI_MODEL=gpt-3.5-turbo
RATE_LIMIT_PER_MINUTE=60
```

### 2. Local Development Setup

```bash
# Install dependencies
pip install -r services/requirements.txt

# Start Redis
docker run -d -p 6379:6379 --name redis redis:7-alpine

# Run the service
python services/shopnoltd-openai-service.py
```

Service is now available at `http://localhost:3001`

### 3. Docker Deployment

Build and run:
```bash
docker build -t shopnoltd/openai-service:latest .
docker run -d -p 3001:3001 \
  -e OPENAI_API_KEY="sk-..." \
  -e API_BEARER_TOKEN="token-..." \
  -e REDIS_URL="redis://host:6379" \
  --link redis:redis \
  shopnoltd/openai-service:latest
```

### 4. Kubernetes Deployment

#### Step 1: Create Namespace
```bash
kubectl create namespace openai
```

#### Step 2: Create Secrets
```bash
kubectl create secret generic openai-secrets \
  --from-literal=api-key="sk-your-openai-api-key" \
  --from-literal=bearer-token="your-secret-bearer-token" \
  -n openai
```

#### Step 3: Deploy the Service
```bash
# Apply all manifests in order
kubectl apply -f apps/openai/configmap.yaml -n openai
kubectl apply -f apps/openai/deployment.yaml -n openai
kubectl apply -f apps/openai/ingress.yaml -n openai
```

Or with Kustomize:
```bash
kubectl apply -k apps/openai/ -n openai
```

#### Step 4: Verify Deployment
```bash
# Check pods
kubectl get pods -n openai

# Check service
kubectl get svc -n openai

# Check logs
kubectl logs -f deployment/openai-service -n openai

# Port forward for testing
kubectl port-forward svc/openai-service 3001:3001 -n openai
```

## API Usage Examples

### Using cURL

#### Health Check
```bash
curl http://localhost:3001/health
```

#### Chat Completion
```bash
curl -X POST http://localhost:3001/api/chat/completions \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is artificial intelligence?",
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 2048
  }'
```

#### Get Conversation History
```bash
curl http://localhost:3001/api/chat/history/{conversation_id} \
  -H "Authorization: Bearer your-token"
```

#### List Available Models
```bash
curl http://localhost:3001/api/models \
  -H "Authorization: Bearer your-token"
```

### Using Python Client

```python
from services.openai_client import SyncOpenAIServiceClient

# Initialize client
client = SyncOpenAIServiceClient(
    base_url="http://localhost:3001",
    bearer_token="your-token"
)

# Get chat response
response = client.chat_completion(
    message="Hello! How are you?",
    model="gpt-3.5-turbo",
    temperature=0.7,
    max_tokens=2048
)

print(f"Response: {response.response}")
print(f"Conversation ID: {response.conversation_id}")
print(f"Tokens used: {response.usage}")

# Continue conversation
response2 = client.chat_completion(
    message="Tell me a joke",
    conversation_id=response.conversation_id
)

print(f"Continued: {response2.response}")

# Get conversation history
history = client.get_conversation_history(response.conversation_id)
print(f"Total messages: {len(history.messages)}")

# Delete conversation
client.delete_conversation(response.conversation_id)
```

### Using JavaScript/Node.js

```javascript
const axios = require('axios');

const client = axios.create({
  baseURL: 'http://localhost:3001',
  headers: {
    'Authorization': 'Bearer your-token',
    'Content-Type': 'application/json'
  }
});

// Chat completion
async function chat(message, conversationId = null) {
  const response = await client.post('/api/chat/completions', {
    message,
    conversation_id: conversationId,
    model: 'gpt-3.5-turbo',
    temperature: 0.7,
    max_tokens: 2048
  });
  return response.data;
}

// Example usage
(async () => {
  const response = await chat('What is machine learning?');
  console.log(response.response);
  console.log(`Conversation: {response.conversation_id}`);
})();
```

## Advanced Configuration

### Custom System Prompts

Set custom behavior for conversations:

```bash
curl -X POST http://localhost:3001/api/chat/completions \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Help me with Python",
    "system_prompt": "You are an expert Python programmer. Provide concise, accurate code examples.",
    "model": "gpt-4"
  }'
```

### Using Different Models

```bash
# Using GPT-4 (more powerful but slower/expensive)
curl -X POST http://localhost:3001/api/chat/completions \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Solve this complex problem...",
    "model": "gpt-4",
    "max_tokens": 4096
  }'

# Using GPT-3.5-turbo-16k (larger context window)
curl -X POST http://localhost:3001/api/chat/completions \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze this long document...",
    "model": "gpt-3.5-turbo-16k",
    "max_tokens": 4096
  }'
```

### Adjusting Temperature

Lower temperature (0.0-0.5): More deterministic, precise
Higher temperature (0.7-2.0): More creative, varied

```bash
curl -X POST http://localhost:3001/api/chat/completions \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Write a creative story",
    "temperature": 1.5
  }'
```

## Monitoring & Observability

### Kubernetes Monitoring

#### Check Pod Status
```bash
kubectl describe pod -l app=openai-service -n openai
```

#### View Logs
```bash
# Current logs
kubectl logs deployment/openai-service -n openai

# Follow logs
kubectl logs -f deployment/openai-service -n openai

# Previous pod logs
kubectl logs --previous deployment/openai-service -n openai
```

#### Monitor Resource Usage
```bash
kubectl top pods -n openai
kubectl top nodes
```

#### Check Events
```bash
kubectl get events -n openai --sort-by='.lastTimestamp'
```

### Metrics

The service exposes usage statistics:

```json
{
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 156,
    "total_tokens": 168
  }
}
```

Monitor these for:
- Cost optimization (different models cost differently)
- Performance analysis
- Quota management

### Health Checks

All deployments include:
- **Liveness Probe**: Restarts unhealthy containers
- **Readiness Probe**: Removes from load balancer if not ready

View probe status:
```bash
kubectl get pod -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")]}'
```

## Troubleshooting

### "Redis service unavailable"
```
Error: Redis service unavailable
```
**Solution**: Ensure Redis is running and accessible
```bash
# Check Redis connection
redis-cli -h redis ping
# Output: PONG
```

### "Invalid authentication credentials"
```
401 Unauthorized: Invalid authentication credentials
```
**Solution**: Verify the bearer token
```bash
# Check if token matches
echo $API_BEARER_TOKEN
# Use this token in Authorization header
```

### "OpenAI API error"
```
502 Bad Gateway: OpenAI API error
```
**Solution**: 
- Verify OpenAI API key is valid
- Check OpenAI API status: https://status.openai.com/
- Ensure account has credits

### "Rate limit exceeded"
```
429 Too Many Requests: Rate limit exceeded
```
**Solution**: Increase `RATE_LIMIT_PER_MINUTE` or implement client-side backoff

### Pod CrashLoopBackOff
**Solution**: Check logs for errors
```bash
kubectl logs deployment/openai-service -n openai --all-containers=true
```

## Cost Optimization

### Model Selection Guide

| Model | Cost | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| gpt-3.5-turbo | $$ | Fast | Good | General purpose, customer support |
| gpt-4 | $$$$ | Slow | Excellent | Complex reasoning, specialized tasks |
| gpt-3.5-turbo-16k | $$$ | Medium | Good | Long documents, large context |

### Cost Estimation

Calculate per-request costs:
```
Cost = (prompt_tokens / 1000) * prompt_cost + (completion_tokens / 1000) * completion_cost
```

Example - gpt-3.5-turbo:
- 100 prompt tokens: $0.00005
- 150 completion tokens: $0.000225
- Total: $0.000275 per request

### Budget Tips

1. Use GPT-3.5-turbo for most requests
2. Limit `max_tokens` based on use case
3. Implement conversation cleanup (TTL configured)
4. Monitor token usage metrics
5. Use rate limiting to prevent abuse

## Security Best Practices

### API Keys
- ✅ Never commit API keys to git
- ✅ Use environment variables
- ✅ Rotate keys periodically
- ✅ Use separate keys for dev/prod

### Bearer Tokens
- ✅ Generate strong random tokens
- ✅ Store in Kubernetes secrets
- ✅ Rotate periodically
- ✅ Scope to specific users/applications

### Network Security
- ✅ Use TLS/HTTPS (ingress configured)
- ✅ Restrict CORS origins
- ✅ Rate limiting enabled
- ✅ Run as non-root user

### Data Privacy
- ✅ Conversations auto-delete after TTL
- ✅ No persistent conversation storage
- ✅ In-memory Redis (not disk-backed by default)
- ✅ Consider GDPR/privacy requirements

## Support & Resources

- **OpenAI API Docs**: https://platform.openai.com/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Redis Docs**: https://redis.io/docs/
- **Kubernetes Docs**: https://kubernetes.io/docs/
- **Service Repo**: https://gitlab.com/asaduzzaman.bheramara-group/k8s-platform

## Contributing

To extend the service:
1. Add new endpoints following the existing pattern
2. Update tests
3. Update documentation
4. Create PR with changes

## License

Part of Shopnoltd platform - All Rights Reserved
