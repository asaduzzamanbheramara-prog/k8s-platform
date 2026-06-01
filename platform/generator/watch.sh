#!/bin/bash

echo "👀 Watching domain-registry.yaml..."

while true; do
  python3 platform/generator/generate-domains.py
  sleep 30
done
