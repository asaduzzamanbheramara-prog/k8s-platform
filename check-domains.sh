#!/bin/bash
# Comprehensive domain and subdomain check for shopnoltd.dpdns.org

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  SHOPNOLTD DOMAIN & SUBDOMAIN HEALTH CHECK                    ║"
echo "║  $(date '+%Y-%m-%d %H:%M:%S')                              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo

# Define all domains
DOMAINS=(
  "shopnoltd.dpdns.org"
  "www.shopnoltd.dpdns.org"
  "kf.shopnoltd.dpdns.org"
  "kc.shopnoltd.dpdns.org"
  "ee.shopnoltd.dpdns.org"
  "kobo.shopnoltd.dpdns.org"
  "kpi.shopnoltd.dpdns.org"
  "erp.shopnoltd.dpdns.org"
  "billing.shopnoltd.dpdns.org"
  "api.shopnoltd.dpdns.org"
  "mail.shopnoltd.dpdns.org"
  "storage.shopnoltd.dpdns.org"
  "grafana.shopnoltd.dpdns.org"
  "prometheus.shopnoltd.dpdns.org"
  "portainer.shopnoltd.dpdns.org"
  "argocd.shopnoltd.dpdns.org"
  "chat.shopnoltd.dpdns.org"
  "meet.shopnoltd.dpdns.org"
  "live.shopnoltd.dpdns.org"
  "openai.shopnoltd.dpdns.org"
)

echo "📋 TESTING $(echo ${#DOMAINS[@]}) DOMAINS/SUBDOMAINS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

SUCCESS=0
FAILED=0
TIMEOUT=0

for domain in "${DOMAINS[@]}"; do
  printf "%-45s " "Testing $domain..."
  
  # Test HTTPS response with timeout
  RESPONSE=$(curl -s -I -m 5 -k "https://$domain" 2>&1)
  HTTP_CODE=$(echo "$RESPONSE" | grep "^HTTP" | awk '{print $2}')
  
  if [ -z "$HTTP_CODE" ]; then
    echo "❌ TIMEOUT/FAILED"
    ((TIMEOUT++))
  elif [ "$HTTP_CODE" -lt 400 ]; then
    echo "✅ $HTTP_CODE"
    ((SUCCESS++))
  elif [ "$HTTP_CODE" -eq 503 ]; then
    echo "⚠️  $HTTP_CODE (Service Unavailable)"
    ((FAILED++))
  else
    echo "⚠️  $HTTP_CODE"
    ((FAILED++))
  fi
done

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
printf "✅ Responding:  %d\n" "$SUCCESS"
printf "⚠️  Issues:      %d\n" "$FAILED"
printf "❌ Timeouts:    %d\n" "$TIMEOUT"
printf "📈 Total:       %d\n" "${#DOMAINS[@]}"
echo

echo "🔧 KUBERNETES CLUSTER STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
kubectl get nodes
echo
kubectl get pods -A | grep -E "(Running|CrashLoop|Pending)" | head -20
echo

echo "🌐 CLOUDFLARE TUNNEL STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
kubectl logs -n kube-system -l app=cloudflared-global --tail=5 2>/dev/null || echo "Tunnel logs: check manually"
echo

echo "🎯 INGRESS ROUTES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
kubectl get ingress -A --sort-by=.metadata.namespace
echo

echo "✨ CHECK COMPLETE"
