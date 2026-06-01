# K8s Platform Scripts & Automation

## Webhook Auto-Sync System

### Overview
Automated deployment system that listens for GitHub/GitLab push events and automatically syncs code and deploys to Kubernetes.

### Components

1. **webhook-server.py** - Main webhook HTTP server
   - Listens on port 8080 (configurable)
   - Validates GitHub/GitLab webhook signatures
   - Processes push events asynchronously

2. **server-sync-webhook.sh** - Deployment sync handler
   - Pulls latest code from repository
   - Applies Kubernetes manifests
   - Syncs to GitLab mirror
   - Verifies deployment

3. **k8s-webhook.service** - Systemd service file
   - Auto-restart on failure
   - Hardened security settings
   - Journal logging

### Quick Start

#### 1. Install and Start Server

```bash
# Copy service file to systemd
sudo cp scripts/k8s-webhook.service /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable k8s-webhook
sudo systemctl start k8s-webhook

# Verify running
sudo systemctl status k8s-webhook
curl http://localhost:8080/health
```

#### 2. Configure GitHub Webhook

See `docs/WEBHOOK_SETUP.md` for detailed instructions.

#### 3. Test Deployment

Push to main branch:
```bash
git push origin main
```

Monitor logs:
```bash
sudo journalctl -u k8s-webhook -f
tail -f /var/log/k8s-webhooks/webhook-server.log
tail -f /var/log/k8s-webhooks/server-sync.log
```

### Configuration

Edit service file to set webhook secret:
```bash
sudo nano /etc/systemd/system/k8s-webhook.service
# Set WEBHOOK_SECRET environment variable
sudo systemctl restart k8s-webhook
```

### Troubleshooting

#### Server won't start
```bash
sudo systemctl status k8s-webhook
sudo journalctl -u k8s-webhook -n 50
```

#### Deployments not happening
```bash
# Check logs
tail -f /var/log/k8s-webhooks/webhook-server.log

# Verify webhook endpoint
curl http://localhost:8080/health

# Test manually
curl -X POST http://localhost:8080/webhook -H "Content-Type: application/json" -d '{}'
```

#### Permission denied errors
```bash
# Ensure logs directory is writable
sudo mkdir -p /var/log/k8s-webhooks
sudo chown shopno:shopno /var/log/k8s-webhooks
```

### Other Scripts

- **auto-sync.sh** - GitHub to GitLab mirror sync
- **check-domains.sh** - DNS health check
- **deploy.sh** - Manual deployment script
- **sync.sh** - Repository sync script

See individual scripts for usage.

### Documentation

- `docs/DNS_SETUP.md` - DNS configuration guide
- `docs/WEBHOOK_SETUP.md` - Webhook setup instructions
- `docs/DOMAINS.md` - Domain reference
- `docs/DEPLOYMENT_GUIDE.md` - Deployment procedures
