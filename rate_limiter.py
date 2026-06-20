# pip install flask
"""
Task 2: Rate Limiter Mini

This file implements a small Flask API protected by an in-memory per-user rate limiter.
The goal is to demonstrate a simple sliding-window algorithm using timestamps.
"""

import time
from threading import Lock

from flask import Flask, jsonify, request

app = Flask(__name__)

# Rate-limiting configuration.
MAX_REQUESTS_PER_WINDOW = 5
WINDOW_SECONDS = 60
ANONYMOUS_USER_ID = "anonymous"

# In-memory request log structure:
# {
#     "user_id_1": [timestamp1, timestamp2, ...],
#     "user_id_2": [timestamp1, timestamp2, ...],
# }
#
# Why store timestamps in a list?
# - It makes the sliding-window idea very visible for learning purposes.
# - On each request, we can remove old timestamps and count only recent ones.
#
# Production alternative:
# - Use Redis with key expiry, a token bucket/leaky bucket algorithm,
#   or an API gateway/load balancer with built-in rate limiting.
requests_log = {}
requests_lock = Lock()


def get_user_id() -> str:
    """Read the caller identity from the request header."""
    # We treat a missing header as an anonymous caller to keep the demo simple.
    # Another valid choice would be to return HTTP 400 and require the header.
    raw_user_id = request.headers.get("X-User-ID", "")
    cleaned_user_id = raw_user_id.strip()
    return cleaned_user_id or ANONYMOUS_USER_ID


def filter_recent_timestamps(timestamps: list[float], current_timestamp: float) -> list[float]:
    """Keep only timestamps that still belong to the active sliding window."""
    # Why do this on every request?
    # - It keeps the stored list aligned with the last 60 seconds only.
    # - It also prevents old request history from growing forever for this demo.
    return [
        timestamp
        for timestamp in timestamps
        if current_timestamp - timestamp < WINDOW_SECONDS
    ]


@app.get("/data")
def get_data():
    """Return sample data if the caller is under the rate limit."""
    user_id = get_user_id()
    current_timestamp = time.time()

    # Sliding window explanation:
    # - We only care about requests made in the last 60 seconds.
    # - Older timestamps are filtered out on every request so the list reflects
    #   the current active window instead of growing forever.
    #
    # Why are we doing it this way?
    # - It is easy to understand and matches the assignment requirements exactly.
    # Production alternative:
    # - Use Redis sorted sets, token buckets, or centralized rate limit middleware.
    # The lock keeps updates safe if multiple requests reach the Flask process at the same time.
    with requests_lock:
        recent_timestamps = filter_recent_timestamps(
            requests_log.get(user_id, []),
            current_timestamp,
        )

        if len(recent_timestamps) >= MAX_REQUESTS_PER_WINDOW:
            return jsonify({
                "error": "Too Many Requests: Try again later.",
                "user_id": user_id,
                "limit": MAX_REQUESTS_PER_WINDOW,
                "window_seconds": WINDOW_SECONDS,
            }), 429

        recent_timestamps.append(current_timestamp)
        requests_log[user_id] = recent_timestamps

        remaining_requests = MAX_REQUESTS_PER_WINDOW - len(recent_timestamps)

    return jsonify({
        "message": "Here is your data",
        "user_id": user_id,
        "requests_remaining_in_window": remaining_requests,
        "window_seconds": WINDOW_SECONDS,
    }), 200


if __name__ == "__main__":
    # Port 5004 keeps this app separate from the URL shortener and future backend servers.
    # In production, a real WSGI server would run the Flask app instead of the dev server.
    app.run(host="127.0.0.1", port=5004, debug=True, use_reloader=False)


# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
# What this file implements:
# - A simple API endpoint: GET /data
# - A per-user in-memory rate limiter using a sliding 60-second window
# - A maximum of 5 requests per minute for each user ID
#
# How it works:
# - The app reads the user identity from the X-User-ID header.
# - If the header is missing or blank, the caller is treated as "anonymous".
# - For each request, the app keeps only timestamps from the last 60 seconds.
# - If 5 or more timestamps remain, the app returns HTTP 429.
# - Otherwise, it stores the current timestamp and returns success JSON.
#
# Why this design is acceptable here:
# - It keeps the logic transparent and easy to describe in a report.
# - It directly demonstrates sliding-window rate limiting with minimal code.
#
# Limitations of this simple approach:
# - Data disappears when the process restarts.
# - The limit only applies inside one Python process.
# - It is not shared across multiple machines or containers.
# - A very large number of users would eventually consume more memory.
#
# How to run:
#   python rate_limiter.py
#
# How to test with curl:
# 1) Send a request as a named user
#   curl -i http://127.0.0.1:5004/data -H "X-User-ID: alice"
#
# 2) Send 6 requests quickly to trigger the rate limit
#   for i in 1 2 3 4 5 6; do
#     curl -s -i http://127.0.0.1:5004/data -H "X-User-ID: alice"
#     echo
#   done
#
# 3) Test the anonymous-user fallback
#   curl -i http://127.0.0.1:5004/data
#
# Expected behavior:
# - Requests 1 through 5 succeed within a 60-second window.
# - Request 6 for the same user returns HTTP 429 Too Many Requests.
# - After enough time passes, old timestamps fall out of the window automatically.


