#!/bin/bash

DOMAINS=(
  "shopnoltd.dpdns.org"
  "www.shopnoltd.dpdns.org"

  "erp.shopnoltd.dpdns.org"
  "billing.shopnoltd.dpdns.org"
  "api.shopnoltd.dpdns.org"

  "kf.shopnoltd.dpdns.org"
  "kc.shopnoltd.dpdns.org"
  "ee.shopnoltd.dpdns.org"
  "kobo.shopnoltd.dpdns.org"

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
  "cursor.shopnoltd.dpdns.org"
)

echo "🌐 DOMAIN HEALTH REPORT"
echo "=============================="

for d in "${DOMAINS[@]}"; do
  code=$(curl -k -o /dev/null -s -w "%{http_code}" https://$d)

  if [[ "$code" == "200" || "$code" == "301" || "$code" == "302" ]]; then
    echo "✅ $d -> $code"
  elif [[ "$code" == "000" ]]; then
    echo "❌ $d -> NO RESPONSE"
  else
    echo "⚠️  $d -> $code"
  fi
done

echo "=============================="
