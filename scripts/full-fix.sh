#!/bin/bash

echo "🔧 CREATING MISSING NAMESPACES..."
kubectl create namespace portainer 2>/dev/null || true

echo "🔍 CHECKING ENDPOINTS..."
kubectl get endpoints -A

echo "🔄 RESTARTING CRITICAL DEPLOYMENTS..."
kubectl rollout restart deployment -n kobo kpi kobocat 2>/dev/null || true
kubectl rollout restart deployment -n erp erp-api billing-api 2>/dev/null || true
kubectl rollout restart deployment -n realtime chat live meet 2>/dev/null || true

echo "⏳ WAITING 20s..."
sleep 20

echo "🌐 FINAL HEALTH CHECK..."
for d in chat live meet kobo kpi kc kf ee api openai; do
  echo "---- $d ----"
  curl -s -o /dev/null -w "%{http_code}\n" https://$d.shopnoltd.dpdns.org
done
