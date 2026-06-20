# System Design Mini Projects in Python Using Flask

**Student Name:** Umesh Kumar Mahato

**Date:** June 20, 2026

**Assignment Title:** System Design - URL Shortener, Rate Limiter, Load Balancer
---

## 1. Project Documentation

### Overview
This assignment contains three small Python projects built with Flask to demonstrate core backend system design ideas: URL shortening, rate limiting, and load balancing. Each project is intentionally simple, runs locally, and focuses on explaining the main design concept clearly.

**Task 1 - URL Shortener Lite**
A Flask API accepts a long URL, generates a short ID using Base62 encoding, stores the mapping in memory, and redirects users when the short URL is opened.

**Task 2 - Rate Limiter Mini**
A Flask API protects an endpoint by limiting each user to 5 requests per minute. User identity is read from the `X-User-ID` header, and recent timestamps are stored in memory.

**Task 3 - Simple Load Balancer Simulation**
Three backend Flask servers run on different ports, and a fourth Flask app acts as a round-robin load balancer that forwards requests across them.

---

## 2. Step-by-Step Implementation

## Task 1 - URL Shortener Lite

### Objective
Build a small URL shortener service with two endpoints:
- `POST /shorten`
- `GET /<short_id>`

### Implementation Summary
The main file for this task is `url_shortener.py`. The service receives a long URL, generates a short ID, stores the mapping in an in-memory dictionary, and redirects users to the original URL when the short ID is requested.

### Code Snippet 1 - In-Memory Storage and Base62 Encoding
```python
BASE62_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
id_to_url = {}
next_id = 1

def encode_base62(number: int) -> str:
    encoded_characters = []
    base = len(BASE62_ALPHABET)

    while number > 0:
        number, remainder = divmod(number, base)
        encoded_characters.append(BASE62_ALPHABET[remainder])

    return "".join(reversed(encoded_characters))
```

### Explanation
This code creates the short-ID generation logic. The `next_id` counter guarantees that each new URL gets a unique number. The `encode_base62()` helper converts that integer into a compact Base62 string using digits, lowercase letters, and uppercase letters.

### Process Description
I used Base62 encoding because it creates short, readable IDs without adding much complexity. I used an incrementing counter because it is predictable, easy to test, and sufficient for a local assignment.

### Code Snippet 2 - Create Short URL Endpoint
```python
@app.post("/shorten")
def shorten_url():
    global next_id

    payload = request.get_json(silent=True)
    url = payload.get("url")

    short_id = encode_base62(next_id)
    id_to_url[short_id] = url
    next_id += 1

    return jsonify({
        "short_id": short_id,
        "short_url": f"{request.host_url.rstrip('/')}/{short_id}",
    }), 201
```

### Explanation
This endpoint accepts a JSON body with a URL, generates a new short ID, stores the mapping, and returns the shortened URL.

### Code Snippet 3 - Redirect Endpoint
```python
@app.get("/<short_id>")
def redirect_to_original(short_id: str):
    original_url = id_to_url.get(short_id)
    if original_url is None:
        return jsonify({"error": "URL not found"}), 404

    return redirect(original_url, code=302)
```

### Explanation
This endpoint looks up the short ID in memory. If the ID exists, the user is redirected to the original URL. If it does not exist, the API returns a 404 error.

### Limitations
- Data is lost when the application stops.
- Storage exists only inside one Python process.
- The design does not scale across multiple instances.

### Screenshots to Include
**Figure 1.** Running `url_shortener.py` in the terminal.

**Figure 2.** `curl` command for `POST /shorten` and the JSON response containing `short_id` and `short_url`.

**Figure 3.** Redirect test for `GET /<short_id>` showing the HTTP redirect response.

---

## Task 2 - Rate Limiter Mini

### Objective
Protect an API endpoint by limiting each user to 5 requests per minute.

### Implementation Summary
The main file for this task is `rate_limiter.py`. The API exposes `GET /data`, reads the user identity from the `X-User-ID` header, and tracks recent request timestamps in memory.

### Code Snippet 1 - Request Log Structure
```python
requests_log = {}
```

### Explanation
This dictionary stores request timestamps for each user. Each key is a user ID, and each value is a list of timestamps representing recent requests.

### Code Snippet 2 - Read User ID
```python
def get_user_id() -> str:
    raw_user_id = request.headers.get("X-User-ID", "")
    cleaned_user_id = raw_user_id.strip()
    return cleaned_user_id or "anonymous"
```

### Explanation
This helper reads the user ID from the request header. If the header is missing or blank, the request is treated as anonymous.

### Code Snippet 3 - Sliding Window Filter
```python
def filter_recent_timestamps(timestamps: list[float], current_timestamp: float) -> list[float]:
    return [
        timestamp
        for timestamp in timestamps
        if current_timestamp - timestamp < 60
    ]
```

### Explanation
This function keeps only the timestamps from the last 60 seconds. It is the core of the sliding-window rate-limiting logic.

### Code Snippet 4 - Enforce the Limit
```python
@app.get("/data")
def get_data():
    user_id = get_user_id()
    current_timestamp = time.time()

    recent_timestamps = filter_recent_timestamps(
        requests_log.get(user_id, []),
        current_timestamp,
    )

    if len(recent_timestamps) >= 5:
        return jsonify({"error": "Too Many Requests: Try again later."}), 429

    recent_timestamps.append(current_timestamp)
    requests_log[user_id] = recent_timestamps

    return jsonify({"message": "Here is your data"}), 200
```

### Explanation
For each request, the API removes old timestamps, counts the remaining requests in the last minute, and either allows the request or returns HTTP 429 if the limit has been reached.

### Process Description
I used a sliding-window approach because it matches the requirement of “last 60 seconds” clearly. I used in-memory storage because it keeps the implementation simple and makes the rate-limiting logic easy to explain.

### Limitations
- Request history is lost on restart.
- The limit only applies within one running process.
- A shared store such as Redis would be needed in production.

### Screenshots to Include
**Figure 4.** Running `rate_limiter.py` in the terminal.

**Figure 5.** Successful request to `GET /data` with `X-User-ID: alice`.

**Figure 6.** Repeated requests showing the sixth request returning HTTP 429.

**Figure 7.** Request without `X-User-ID` showing anonymous-user handling.

---

## Task 3 - Simple Load Balancer Simulation

### Objective
Simulate a round-robin load balancer that distributes traffic across three backend servers.

### Implementation Summary
This task uses four files:
- `server1.py`
- `server2.py`
- `server3.py`
- `load_balancer.py`

The three backend servers run on ports 5001, 5002, and 5003. The load balancer runs on port 5005 and forwards requests to the backends in round-robin order.

### Code Snippet 1 - Backend Definition
```python
backends = [
    "http://127.0.0.1:5001",
    "http://127.0.0.1:5002",
    "http://127.0.0.1:5003",
]
current_backend_index = 0
```

### Explanation
This list stores the backend server addresses. The `current_backend_index` variable tracks which backend should receive the next request.

### Code Snippet 2 - Round-Robin Pointer
```python
def reserve_start_index() -> int:
    global current_backend_index
    start_index = current_backend_index
    current_backend_index = (current_backend_index + 1) % len(backends)
    return start_index
```

### Explanation
This function reserves the current backend index and then moves the pointer forward. Modulo arithmetic makes the pointer wrap back to the first backend after the last one.

### Code Snippet 3 - Forward Request to Backend
```python
@app.get("/proxy")
def proxy_request():
    start_index = reserve_start_index()

    for attempt in range(len(backends)):
        backend_index = (start_index + attempt) % len(backends)
        backend_url = backends[backend_index]

        try:
            backend_response = requests.get(backend_url, timeout=2)
            return Response(
                backend_response.content,
                status=backend_response.status_code,
                content_type=backend_response.headers.get("Content-Type", "text/plain"),
            )
        except requests.RequestException:
            continue

    return jsonify({"error": "backend unavailable"}), 503
```

### Explanation
The load balancer picks a backend using the round-robin pointer, forwards the request with the `requests` library, and returns the backend’s response. If one backend is unavailable, it tries the next one. If all backends fail, it returns HTTP 503.

### Process Description
I used round robin because it is simple, fair, and easy to demonstrate. I created three separate backend servers so the routing pattern is visible during testing. I also added basic failure handling to make the behavior more realistic.

### Limitations
- The round-robin pointer exists only in memory.
- Health checks are basic and happen only during request failure.
- The balancer forwards only a simple GET request in this demo.

### Screenshots to Include
**Figure 8.** All four terminal windows running `server1.py`, `server2.py`, `server3.py`, and `load_balancer.py`.

**Figure 9.** Direct calls to each backend server showing unique responses.

**Figure 10.** Multiple `GET /proxy` calls showing round-robin behavior across the three servers.

**Figure 11.** Load balancer behavior after one backend server is stopped.

**Figure 12.** HTTP 503 response when all backend servers are unavailable.

---

## 3. Final Notes

### Challenges Faced and How I Solved Them
One challenge was keeping the projects simple while still demonstrating realistic backend concepts. I solved this by using in-memory data structures and small Flask apps so the core logic stayed easy to follow.

Another challenge was making the code easy to explain in documentation. I addressed this by using clear function names, small helper functions, and comments that describe both the logic and the design decisions.

A final challenge was handling error cases correctly. I added validation and fallback behavior for invalid URLs, missing headers, rate-limit violations, and unavailable backend servers.

### Key Learnings
This assignment showed that simple data structures can model important backend behaviors such as lookup, request tracking, and traffic distribution.

It also reinforced that good API design includes both successful responses and well-defined failure handling.

Most importantly, the assignment highlighted the trade-off between simplicity and scalability. Each solution works well as a local demonstration, but production systems would require persistent storage, shared state, stronger fault tolerance, and more advanced infrastructure.

---

## Optional Figure Placement Template
You can paste screenshots directly below each caption in Google Docs, for example:

**Figure 1. Running `url_shortener.py` in the terminal.**
[Paste screenshot here]

**Figure 2. `POST /shorten` request and JSON response.**
[Paste screenshot here]

**Figure 3. Redirect response for `GET /<short_id>`.**
[Paste screenshot here]

---

## 4. Optional Testing Assets

### Postman Collection
- File: `postman_collection.json`
- Purpose: Import all key API requests for Task 1, Task 2, and Task 3 into Postman.
- Included requests:
  - `POST /shorten`, `GET /1`, `GET /doesnotexist`
  - `GET /data` (named user and anonymous)
  - `GET /proxy` (multiple calls for round-robin checks)

### Automated Script
- File: `run_tests.sh`
- Purpose: Start local apps and run end-to-end curl checks for all three tasks automatically.
- Verifies:
  - Task 1: create short URL, redirect, and 404 behavior
  - Task 2: 5-per-minute limit and 429 on request 6
  - Task 3: direct backend checks and round-robin proxy flow

### How to Use
```bash
cd ~/url-shortener-lite
chmod +x run_tests.sh
./run_tests.sh
```

### Evidence Note
The script was executed locally and completed all Task 1/2/3 checks with expected HTTP responses.

