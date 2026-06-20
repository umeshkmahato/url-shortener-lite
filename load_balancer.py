# pip install flask requests
"""
Task 3: Simple Load Balancer Simulation

This file implements a small Flask-based load balancer that forwards requests
across three backend servers using a Round Robin strategy.
"""

from threading import Lock

import requests
from flask import Flask, Response, jsonify

app = Flask(__name__)

backends = [
    "http://127.0.0.1:5001",
    "http://127.0.0.1:5002",
    "http://127.0.0.1:5003",
]

# The pointer tracks which backend should be used first for the next incoming request.
# Example:
# - request 1 starts at index 0 -> server 1
# - request 2 starts at index 1 -> server 2
# - request 3 starts at index 2 -> server 3
# - request 4 wraps around to index 0 again
current_backend_index = 0
backend_index_lock = Lock()
REQUEST_TIMEOUT_SECONDS = 2


def reserve_start_index() -> int:
    """Reserve the next round-robin slot and advance the global pointer."""
    global current_backend_index

    # Why move the pointer here?
    # - Each incoming request consumes exactly one round-robin turn.
    # - A lock prevents two concurrent requests from receiving the same starting backend.
    # Production alternative:
    # - Use a reverse proxy like NGINX, HAProxy, Envoy, or a cloud load balancer.
    with backend_index_lock:
        start_index = current_backend_index
        current_backend_index = (current_backend_index + 1) % len(backends)
        return start_index


@app.get("/proxy")
def proxy_request():
    """Forward the request to a backend using round-robin selection."""
    start_index = reserve_start_index()

    # We try backends in round-robin order starting from the reserved index.
    # If the first backend is down, we fall through to the next one.
    for attempt in range(len(backends)):
        backend_index = (start_index + attempt) % len(backends)
        backend_url = backends[backend_index]

        try:
            backend_response = requests.get(backend_url, timeout=REQUEST_TIMEOUT_SECONDS)
            # Why forward the body and status code directly?
            # - It makes the balancer feel transparent to the client for this simple demo.
            # Production alternative:
            # - Forward headers, methods, query strings, tracing metadata, and stream bodies.
            return Response(
                backend_response.content,
                status=backend_response.status_code,
                content_type=backend_response.headers.get(
                    "Content-Type",
                    "text/plain; charset=utf-8",
                ),
            )
        except requests.RequestException:
            continue

    return jsonify({
        "error": "backend unavailable",
        "details": "All backend servers failed to respond.",
    }), 503


if __name__ == "__main__":
    # Port 5005 avoids conflicts with the earlier assignment apps.
    app.run(host="127.0.0.1", port=5005, debug=True, use_reloader=False)


# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
# What this file implements:
# - A simple Flask-based load balancer endpoint: GET /proxy
# - Round Robin traffic distribution across three backend servers
# - Basic fallback if the selected backend is down
#
# How it works:
# - The app stores backend URLs in a list.
# - A global pointer chooses which backend should receive the next request first.
# - After reserving that index, the pointer moves to the next position with modulo arithmetic.
# - The request is forwarded using the requests library.
# - If a backend is unavailable, the balancer tries the next backend in the list.
#
# Why this design is acceptable here:
# - It clearly demonstrates the Round Robin concept with very little setup.
# - It keeps the routing logic explicit and easy to explain in a report.
#
# Limitations of this simple approach:
# - Backend health is checked only when a request fails.
# - The pointer state exists in memory inside one process only.
# - It only forwards a simple GET request to the backend root path.
# - It is not designed for high concurrency or production traffic.
#
# How to run:
#   python load_balancer.py
#
# How to test with curl:
# 1) Start server1.py, server2.py, server3.py, and load_balancer.py
#
# 2) Call the balancer multiple times
#   curl -i http://127.0.0.1:5005/proxy
#   curl -i http://127.0.0.1:5005/proxy
#   curl -i http://127.0.0.1:5005/proxy
#   curl -i http://127.0.0.1:5005/proxy
#
# Expected cycle:
# - Hello from Server 1!
# - Hello from Server 2!
# - Hello from Server 3!
# - Hello from Server 1! again
#
# Optional failure test:
# - Stop one backend server and call /proxy again.
# - The load balancer will try the next backend before returning an error.

