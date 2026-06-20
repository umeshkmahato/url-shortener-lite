#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="~/url-shortener-lite"
PYTHON_BIN="$ROOT_DIR/.venv/bin/python"

URL_SHORTENER_PORT=5000
RATE_LIMITER_PORT=5004
SERVER1_PORT=5001
SERVER2_PORT=5002
SERVER3_PORT=5003
LOAD_BALANCER_PORT=5005

if [ ! -x "$PYTHON_BIN" ]; then
  echo "Error: Python not found at $PYTHON_BIN"
  echo "Create/install the virtual environment first, then retry."
  exit 1
fi

cleanup() {
  for port in \
    "$URL_SHORTENER_PORT" \
    "$RATE_LIMITER_PORT" \
    "$SERVER1_PORT" \
    "$SERVER2_PORT" \
    "$SERVER3_PORT" \
    "$LOAD_BALANCER_PORT"; do
    lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null | xargs -r kill || true
  done
}

trap cleanup EXIT

echo "Stopping any existing local servers on required ports..."
cleanup

cd "$ROOT_DIR"

echo "Starting Task 1 app..."
"$PYTHON_BIN" url_shortener.py > /tmp/url_shortener.log 2>&1 &
sleep 1

echo "\n[Task 1] POST /shorten"
curl -s -i -X POST http://127.0.0.1:${URL_SHORTENER_PORT}/shorten \
  -H "Content-Type: application/json" \
  -d @"$ROOT_DIR/post_request_payload.json" | cat

echo "\n[Task 1] GET /1"
curl -s -i http://127.0.0.1:${URL_SHORTENER_PORT}/1 | cat

echo "\n[Task 1] GET /doesnotexist"
curl -s -i http://127.0.0.1:${URL_SHORTENER_PORT}/doesnotexist | cat

echo "\nStopping Task 1 app..."
lsof -tiTCP:${URL_SHORTENER_PORT} -sTCP:LISTEN | xargs -r kill || true
sleep 1

echo "\nStarting Task 2 app..."
"$PYTHON_BIN" rate_limiter.py > /tmp/rate_limiter.log 2>&1 &
sleep 1

echo "\n[Task 2] 6 requests as alice (expect 429 on #6)"
for i in 1 2 3 4 5 6; do
  echo "Request #$i"
  curl -s -i http://127.0.0.1:${RATE_LIMITER_PORT}/data -H "X-User-ID: alice" | cat
  echo
  sleep 0.2
done

echo "\n[Task 2] Anonymous request"
curl -s -i http://127.0.0.1:${RATE_LIMITER_PORT}/data | cat

echo "\nStopping Task 2 app..."
lsof -tiTCP:${RATE_LIMITER_PORT} -sTCP:LISTEN | xargs -r kill || true
sleep 1

echo "\nStarting Task 3 backend servers and load balancer..."
"$PYTHON_BIN" server1.py > /tmp/server1.log 2>&1 &
"$PYTHON_BIN" server2.py > /tmp/server2.log 2>&1 &
"$PYTHON_BIN" server3.py > /tmp/server3.log 2>&1 &
"$PYTHON_BIN" load_balancer.py > /tmp/load_balancer.log 2>&1 &
sleep 1

echo "\n[Task 3] Direct backend checks"
curl -s -i http://127.0.0.1:${SERVER1_PORT}/ | cat
echo
curl -s -i http://127.0.0.1:${SERVER2_PORT}/ | cat
echo
curl -s -i http://127.0.0.1:${SERVER3_PORT}/ | cat

echo "\n[Task 3] Round robin checks via /proxy"
for i in 1 2 3 4; do
  echo "Proxy request #$i"
  curl -s -i http://127.0.0.1:${LOAD_BALANCER_PORT}/proxy | cat
  echo
  sleep 0.2
done

echo "\nAll checks completed."
echo "Server logs:"
echo "  /tmp/url_shortener.log"
echo "  /tmp/rate_limiter.log"
echo "  /tmp/server1.log"
echo "  /tmp/server2.log"
echo "  /tmp/server3.log"
echo "  /tmp/load_balancer.log"

