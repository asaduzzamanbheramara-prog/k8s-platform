# OpenAI Integration Service

Production-ready FastAPI microservice for OpenAI chat completions.

## Features

- Chat completion endpoint
- Multi-model support
- Redis conversation persistence
- Bearer token auth
- Rate limiting
- Kubernetes ready

## Quick Start

pip install -r services/requirements.txt
cp services/.env.example .env
python services/shopnoltd-openai-service.py

Service: http://localhost:3001

## Configuration

See services/.env.example for all environment variables.

## Security

- Bearer token authentication
- Rate limiting per IP
- Non-root container
- Read-only filesystem

## License

Part of Shopnoltd platform - All Rights Reserved
