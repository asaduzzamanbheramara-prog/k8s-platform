#!/bin/bash

export CF_API_TOKEN="YOUR_TOKEN"

echo "Generating DNS..."
python app/main.py

echo "Generating Ingress..."
python app/ingress.py

echo "Applying Kubernetes..."
kubectl apply -f k8s/generated/

echo "DONE"
