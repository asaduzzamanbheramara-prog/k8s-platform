#!/usr/bin/env python3
"""
webhook-server.py - Webhook server for automatic deployment syncing
Listens for GitHub and GitLab webhook events and triggers deployments
"""

import json
import logging
import os
import subprocess
import sys
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

# Configuration
PORT = int(os.getenv("WEBHOOK_PORT", "8080"))
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
LOG_FILE = "/var/log/k8s-webhooks/webhook-server.log"
SYNC_SCRIPT = "/home/shopno/k8s-platform/scripts/server-sync-webhook.sh"
REPO_DIR = "/home/shopno/k8s-platform"

# Setup logging
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class WebhookHandler(BaseHTTPRequestHandler):
    """HTTP request handler for webhook events"""
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(format % args)
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path != "/webhook":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")
            return
        
        # Read request body
        content_length = int(self.headers.get("Content-Length", 0))
        try:
            payload = self.rfile.read(content_length).decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to read payload: {e}")
            self.send_response(400)
            self.end_headers()
            return
        
        # Parse webhook based on headers
        webhook_type = self._detect_webhook_type()
        logger.info(f"Received {webhook_type} webhook")
        
        # Validate webhook signature
        if not self._validate_signature(payload):
            logger.warning("Invalid webhook signature")
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"Invalid signature")
            return
        
        # Parse payload
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            self.send_response(400)
            self.end_headers()
            return
        
        # Process webhook asynchronously
        self.send_response(202)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "accepted"}).encode())
        
        # Trigger deployment in background thread
        thread = threading.Thread(target=self._process_webhook, args=(data, webhook_type))
        thread.daemon = True
        thread.start()
    
    def do_GET(self):
        """Handle health check GET requests"""
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def _detect_webhook_type(self):
        """Detect webhook type from headers"""
        if "X-GitHub-Event" in self.headers:
            return "GitHub"
        elif "X-Gitlab-Event" in self.headers:
            return "GitLab"
        return "Unknown"
    
    def _validate_signature(self, payload):
        """Validate webhook signature"""
        if not WEBHOOK_SECRET:
            logger.warning("No webhook secret configured, skipping validation")
            return True
        
        import hmac
        import hashlib
        
        if "X-GitHub-Signature-256" in self.headers:
            signature = self.headers["X-GitHub-Signature-256"]
            expected = "sha256=" + hmac.new(
                WEBHOOK_SECRET.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(signature, expected)
        
        elif "X-Gitlab-Token" in self.headers:
            token = self.headers["X-Gitlab-Token"]
            return token == WEBHOOK_SECRET
        
        return False
    
    def _process_webhook(self, data, webhook_type):
        """Process webhook and trigger deployment"""
        try:
            # Extract branch info
            if webhook_type == "GitHub":
                branch = data.get("ref", "main").replace("refs/heads/", "")
                repo = data.get("repository", {}).get("full_name", "unknown")
            elif webhook_type == "GitLab":
                branch = data.get("ref", "main").replace("refs/heads/", "")
                repo = data.get("project", {}).get("path_with_namespace", "unknown")
            else:
                logger.warning(f"Unknown webhook type: {webhook_type}")
                return
            
            logger.info(f"Processing {webhook_type} push to {repo}:{branch}")
            
            # Check if branch should be synced
            sync_branches = ["main", "master", "develop", "prod"]
            if branch not in sync_branches:
                logger.info(f"Skipping sync for branch {branch} (not in sync list)")
                return
            
            # Call sync script
            payload_json = json.dumps(data)
            process = subprocess.Popen(
                [SYNC_SCRIPT],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=REPO_DIR
            )
            
            stdout, stderr = process.communicate(input=payload_json, timeout=600)
            
            if process.returncode == 0:
                logger.info(f"Deployment sync completed successfully for {branch}")
            else:
                logger.error(f"Deployment sync failed: {stderr}")
        
        except subprocess.TimeoutExpired:
            logger.error("Deployment sync timed out after 600 seconds")
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")

def run_server():
    """Run the webhook server"""
    server_address = ("0.0.0.0", PORT)
    httpd = HTTPServer(server_address, WebhookHandler)
    logger.info(f"Webhook server listening on port {PORT}")
    logger.info(f"Endpoint: http://localhost:{PORT}/webhook")
    logger.info(f"Health check: http://localhost:{PORT}/health")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Webhook server shutting down")
        httpd.shutdown()

if __name__ == "__main__":
    run_server()
