#!/usr/bin/env bash
set -euo pipefail

PYTHON="~/url-shortener-lite/.venv/bin/python"
DIR="~/url-shortener-lite"

echo "Stopping any previous instances..."
for port in 5000 5001 5002 5003 5004 5005; do
  lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null | xargs -r kill 2>/dev/null || true
done
sleep 1

cd "$DIR"

echo "Starting all apps..."
"$PYTHON" url_shortener.py > /tmp/url_shortener.log 2>&1 &
"$PYTHON" rate_limiter.py  > /tmp/rate_limiter.log  2>&1 &
"$PYTHON" server1.py       > /tmp/server1.log       2>&1 &
"$PYTHON" server2.py       > /tmp/server2.log       2>&1 &
"$PYTHON" server3.py       > /tmp/server3.log       2>&1 &
"$PYTHON" load_balancer.py > /tmp/load_balancer.log 2>&1 &

sleep 2

echo ""
echo "==============================="
echo "  Application Status"
echo "==============================="
check_port() {
  local port=$1 label=$2
  pid=$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)
  if [ -n "$pid" ]; then
    echo "  UP    :$port  $label"
  else
    echo "  DOWN  :$port  $label  <-- check /tmp/$label.log"
  fi
}
check_port 5000 "url_shortener.py  (Task 1 - URL Shortener)"
check_port 5004 "rate_limiter.py   (Task 2 - Rate Limiter)"
check_port 5001 "server1.py        (Task 3 - Backend 1)"
check_port 5002 "server2.py        (Task 3 - Backend 2)"
check_port 5003 "server3.py        (Task 3 - Backend 3)"
check_port 5005 "load_balancer.py  (Task 3 - Load Balancer)"
echo "==============================="
echo ""
echo "Quick test commands:"
echo "  curl -s -X POST http://127.0.0.1:5000/shorten -H 'Content-Type: application/json' -d '{\"url\":\"https://example.com\"}'"
echo "  curl -s http://127.0.0.1:5004/data -H 'X-User-ID: alice'"
echo "  curl -s http://127.0.0.1:5005/proxy"
echo ""
echo "Logs: /tmp/url_shortener.log  /tmp/rate_limiter.log  /tmp/server1.log  /tmp/server2.log  /tmp/server3.log  /tmp/load_balancer.log"

