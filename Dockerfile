# ==========================================
# Build Stage
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /tmp

COPY services/requirements.txt .

RUN pip install --user --no-cache-dir -r requirements.txt

# ==========================================
# Runtime Stage
# ==========================================
FROM python:3.11-slim

LABEL maintainer="ShopnoltdToolbox Team"
LABEL description="OpenAI Integration Service"

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /root/.local /root/.local

ENV PATH="/root/.local/bin:${PATH}"

COPY services/shopnoltd_openai_service.py .

EXPOSE 3001

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
 CMD curl -f http://localhost:3001/health || exit 1

CMD ["uvicorn","shopnoltd_openai_service:app","--host","0.0.0.0","--port","3001"]
