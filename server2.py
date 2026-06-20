# pip install flask
"""Task 3 backend server 2."""

from flask import Flask

app = Flask(__name__)


@app.get("/")
def home():
    """Return a simple response that identifies this backend."""
    # Why keep the backend this small?
    # - The goal is to make the load balancer behavior obvious during testing.
    # Production alternative: real application servers with business logic and health checks.
    return "Hello from Server 2!"


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5002, debug=True, use_reloader=False)


# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
# What this file implements:
# - Backend server 2 for the round-robin load balancer demo.
#
# How to run:
#   python server2.py
#
# How to test:
#   curl -i http://127.0.0.1:5002/

