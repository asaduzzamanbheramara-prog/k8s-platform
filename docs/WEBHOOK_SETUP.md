# Webhook Configuration for Shopnoltd K8s Platform

## Overview
Webhook server listens for GitHub and GitLab push events and automatically syncs code and deploys to Kubernetes.

## Server Setup

### Installation

1. Install Python dependencies:
```bash
pip3 install --upgrade pip
# webhook-server.py uses only stdlib modules - no additional packages needed
```

2. Make scripts executable:
```bash
chmod +x /home/shopno/k8s-platform/scripts/webhook-server.py
chmod +x /home/shopno/k8s-platform/scripts/server-sync-webhook.sh
```

### Running the Server

#### Option 1: Manual Start
```bash
python3 /home/shopno/k8s-platform/scripts/webhook-server.py &
```

#### Option 2: Systemd Service
Create `/etc/systemd/system/k8s-webhook.service`:
```ini
[Unit]
Description=Kubernetes Webhook Server
After=network.target

[Service]
Type=simple
User=shopno
WorkingDirectory=/home/shopno/k8s-platform
ExecStart=/usr/bin/python3 /home/shopno/k8s-platform/scripts/webhook-server.py
Restart=always
RestartSec=10

Environment="WEBHOOK_PORT=8080"
Environment="WEBHOOK_SECRET=your-secret-here"

[Install]
WantedBy=multi-user.target
```

Start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable k8s-webhook
sudo systemctl start k8s-webhook
sudo systemctl status k8s-webhook
```

#### Option 3: Docker Container
```bash
docker run -d \
  --name k8s-webhook \
  -p 8080:8080 \
  -v /home/shopno/k8s-platform:/app \
  -e WEBHOOK_PORT=8080 \
  -e WEBHOOK_SECRET="your-secret-here" \
  python:3.9 \
  python3 /app/scripts/webhook-server.py
```

### Configuration

#### Environment Variables
- `WEBHOOK_PORT` - Port to listen on (default: 8080)
- `WEBHOOK_SECRET` - Secret for validating webhooks (optional but recommended)

#### Firewall Rules
```bash
# Allow webhook port
sudo ufw allow 8080/tcp
```

#### Reverse Proxy (recommended for HTTPS)
Setup nginx reverse proxy to forward HTTPS traffic to webhook server:
```nginx
server {
    listen 443 ssl http2;
    server_name webhook.shopnoltd.dpdns.org;
    
    ssl_certificate /etc/letsencrypt/live/webhook.shopnoltd.dpdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/webhook.shopnoltd.dpdns.org/privkey.pem;
    
    location /webhook {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /health {
        proxy_pass http://localhost:8080;
    }
}
```

## GitHub Webhook Setup

### Step 1: Generate Secret
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Step 2: Configure Webhook in GitHub
1. Go to Repository Settings → Webhooks → Add webhook
2. **Payload URL**: `https://webhook.shopnoltd.dpdns.org/webhook` or `http://your-ip:8080/webhook`
3. **Content type**: application/json
4. **Secret**: Paste the generated secret
5. **Which events**: Select "Push events"
6. **Active**: Check enabled
7. Click "Add webhook"

### Step 3: Test Webhook
- In Webhooks settings, click "Recent Deliveries"
- You should see successful (200) delivery
- Check server logs: `tail -f /var/log/k8s-webhooks/webhook-server.log`

## GitLab Webhook Setup

### Step 1: Configure Webhook in GitLab
1. Go to Project Settings → Webhooks
2. **URL**: `https://webhook.shopnoltd.dpdns.org/webhook` or `http://your-ip:8080/webhook`
3. **Secret token**: Paste your secret
4. **Trigger**: Select "Push events"
5. **SSL verification**: Enable if using HTTPS
6. Click "Add webhook"

### Step 2: Test Webhook
- In Webhooks section, click "Test" → "Push events"
- Should see success response
- Check server logs: `tail -f /var/log/k8s-webhooks/webhook-server.log`

## Webhook Flow

```
GitHub/GitLab Push Event
        ↓
POST /webhook (Webhook Server)
        ↓
Validate Signature
        ↓
Parse Payload (extract branch)
        ↓
Spawn Async Worker Thread
        ↓
Call server-sync-webhook.sh
        ↓
Git Fetch & Reset
        ↓
kubectl apply (Deploy Manifests)
        ↓
Verify Deployment
        ↓
Sync to GitLab Mirror (if configured)
```

## Monitoring

### Check Server Status
```bash
# Check if server is running
curl http://localhost:8080/health

# View active processes
ps aux | grep webhook-server

# Check logs
tail -f /var/log/k8s-webhooks/webhook-server.log
tail -f /var/log/k8s-webhooks/server-sync.log
```

### Troubleshooting

#### Webhook not triggering
- Verify webhook URL is accessible from GitHub/GitLab
- Check firewall allows port 8080
- Verify webhook secret matches (if configured)

#### Deployment fails after webhook
- Check sync logs: `tail /var/log/k8s-webhooks/server-sync.log`
- Verify kubectl access: `kubectl get pods -A`
- Check git permissions: `git --version && git config user.name`

#### SSL certificate errors
- For HTTPS: Setup proper SSL certificate
- For self-signed: Disable SSL verification in GitHub/GitLab webhook settings

## Security Considerations

1. **Always use webhook secrets** to validate requests
2. **Use HTTPS** for webhook URLs in production
3. **Restrict network access** to webhook server (firewall rules)
4. **Use systemd hardening** to limit service privileges
5. **Rotate secrets** periodically
6. **Monitor webhook logs** for suspicious activity

## Webhook Payload Handling

### Supported Branches
Only these branches trigger deployments:
- `main`
- `master`
- `develop`
- `prod`

Other branches are silently skipped.

### Processing
- Webhook response: 202 Accepted (async processing)
- Sync happens in background thread
- Lock prevents concurrent syncs
- Timeout: 10 minutes per sync

## Files

- `scripts/webhook-server.py` - Main webhook server
- `scripts/server-sync-webhook.sh` - Deployment sync script
- `/var/log/k8s-webhooks/webhook-server.log` - Server logs
- `/var/log/k8s-webhooks/server-sync.log` - Sync operation logs
