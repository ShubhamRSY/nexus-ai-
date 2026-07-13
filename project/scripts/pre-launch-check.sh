#!/usr/bin/env bash
# Pre-launch smoke check — run from laptop against production URL.
# Usage: BASE_URL=https://yournexus.duckdns.org bash scripts/pre-launch-check.sh
set -euo pipefail

BASE_URL="${BASE_URL:-https://yournexus.duckdns.org}"
FAIL=0

check() {
  local name="$1"
  local url="$2"
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 20 "$url" || echo "000")
  if [[ "$code" == "200" ]]; then
    echo "OK   $name ($code)"
  else
    echo "FAIL $name ($code) — $url"
    FAIL=1
  fi
}

echo "==> Nexus pre-launch check: $BASE_URL"
check "Landing"  "$BASE_URL/landing"
check "Signup"   "$BASE_URL/signup"
check "Pricing"  "$BASE_URL/pricing"
check "Demo"     "$BASE_URL/"
check "Health"   "$BASE_URL/api/v1/health"

if command -v k6 >/dev/null 2>&1; then
  echo ""
  echo "==> k6 smoke (VUS=3, 15s)..."
  ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  BASE_URL="$BASE_URL" VUS=3 DURATION=15s k6 run "$ROOT/scripts/loadtest/k6-smoke.js" || FAIL=1
else
  echo ""
  echo "SKIP k6 not installed (brew install k6)"
fi

echo ""
if [[ "$FAIL" -eq 0 ]]; then
  echo "All checks passed."
else
  echo "Some checks failed — fix VM before LinkedIn launch."
  exit 1
fi
