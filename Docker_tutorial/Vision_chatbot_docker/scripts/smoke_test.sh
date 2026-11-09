#!/usr/bin/env bash
set -euo pipefail
curl -fsS http://localhost:8000/health
printf '\n'
curl -fsS -X POST http://localhost:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{"tenure_months":12,"monthly_spend":80,"support_tickets":3,"contract_type":"monthly","auto_pay":"no"}'
printf '\n'
curl -fsS http://localhost:8000/predictions
printf '\n'
