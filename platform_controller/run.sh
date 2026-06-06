#!/bin/bash

export CF_API_TOKEN="YOUR_TOKEN"
export CF_ZONE_ID="bc13b09abb3f6b03ac725dc12a3cbac5"
export CF_TUNNEL_ID="5d6e037a-7c09-4788-8532-11dba5fc1a72"

echo "🚀 Running DNS sync controller..."
python3 ingress_watcher.py
