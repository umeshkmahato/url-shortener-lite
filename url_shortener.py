# pip install flask
"""
Task 1: URL Shortener Lite

This file implements a very small URL shortener using Flask and in-memory storage.
It is intentionally simple so the full logic is easy to explain in a system design report.
"""

from threading import Lock
from urllib.parse import urlparse

from flask import Flask, jsonify, redirect, request

app = Flask(__name__)

# Base62 uses 10 digits + 26 lowercase letters + 26 uppercase letters = 62 symbols.
# We encode an integer counter into this alphabet so generated IDs stay short and readable.
BASE62_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

# In-memory storage for the assignment:
# - id_to_url maps a generated short ID back to the original long URL.
# - next_id is our simple auto-incrementing integer source.
# This works well for a demo because it is easy to understand and requires no database.
# Limitation: all data is lost when the process restarts, and multiple app instances would not share state.
id_to_url = {}
next_id = 1
storage_lock = Lock()


def encode_base62(number: int) -> str:
    """Convert a positive integer into a Base62 string."""
    # Why do this? We want short, compact IDs instead of exposing raw integers like 1, 2, 3.
    # Production alternative: use database IDs, UUIDs, hash-based tokens, or collision-resistant random strings.
    if number <= 0:
        raise ValueError("Base62 encoding expects a positive integer")

    encoded_characters = []
    base = len(BASE62_ALPHABET)

    while number > 0:
        number, remainder = divmod(number, base)
        encoded_characters.append(BASE62_ALPHABET[remainder])

    return "".join(reversed(encoded_characters))


def is_valid_url(value: str) -> bool:
    """Basic URL validation for this simple assignment."""
    # Why do this? It prevents empty strings and obviously malformed inputs from being stored.
    # Production alternative: stricter validation, normalization, allowlists, or security scanning.
    try:
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


@app.post("/shorten")
def shorten_url():
    """Create a short ID for a submitted URL."""
    global next_id

    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    url = payload.get("url")
    if url is None:
        return jsonify({"error": "Missing 'url' field"}), 400
    if not isinstance(url, str):
        return jsonify({"error": "'url' must be a string"}), 400
    if not is_valid_url(url):
        return jsonify({"error": "Invalid URL. Use http:// or https://"}), 400

    # We lock the counter update so two requests do not accidentally receive the same ID.
    # Production alternative: let a database or distributed ID service generate unique IDs safely.
    with storage_lock:
        current_id = next_id
        short_id = encode_base62(current_id)
        id_to_url[short_id] = url
        next_id += 1

    base_url = request.host_url.rstrip("/")
    return jsonify({
        "short_id": short_id,
        "short_url": f"{base_url}/{short_id}",
    }), 201


@app.get("/<short_id>")
def redirect_to_original(short_id: str):
    """Look up the original URL and redirect the client to it."""
    # Why do this lookup in memory? It keeps the assignment focused on request flow, not database setup.
    # Production alternative: store mappings in Redis, PostgreSQL, DynamoDB, or another persistent store.
    original_url = id_to_url.get(short_id)
    if original_url is None:
        return jsonify({"error": "URL not found"}), 404

    # 302 is a standard temporary redirect and is enough for this assignment.
    return redirect(original_url, code=302)


if __name__ == "__main__":
    # Running with debug=True makes local development easier.
    # In production, use a real WSGI server such as gunicorn or uWSGI.
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)


# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
# What this file implements:
# - A tiny URL shortener service with:
#   1) POST /shorten to create a short URL
#   2) GET /<short_id> to redirect to the original URL
#
# How it works:
# - Each new URL gets the next integer from a simple counter.
# - That integer is converted into a Base62 short ID using [0-9a-zA-Z].
# - The app stores the mapping in an in-memory dictionary: {short_id: long_url}.
#
# Why this design is acceptable here:
# - It keeps the project self-contained and very easy to explain.
# - It avoids adding a database before the core request flow is understood.
#
# Limitations of this simple approach:
# - All mappings disappear when the app stops or restarts.
# - Data is only stored inside one Python process.
# - It is not suitable for scaling across multiple machines.
#
# How to run:
#   python url_shortener.py
#
# How to test with curl:
# 1) Create a short URL
#   curl -i -X POST http://127.0.0.1:5000/shorten \
#     -H "Content-Type: application/json" \
#     -d '{"url":"https://www.example.com/some/long/path"}'
#
# 2) Follow the short URL returned above
#   curl -i http://127.0.0.1:5000/1
#   curl -i -L http://127.0.0.1:5000/1
#
# Note:
# - The first generated ID is "1" because Base62 encoding of integer 1 is "1".
# - Later IDs become short strings such as "2", "3", ..., "z", "A", and so on.


