# URL Shortener Lite / System Design

This workspace contains three small Python + Flask projects for a system design assignment.

## Project Documentation (Google Doc)

Full write-up, code explanations, process descriptions, and screenshot placeholders are available here:

**[System Design URL Shortener Project – Google Doc](https://docs.google.com/document/d/136Bpx85JEEqQFSbD0Sd2mw4M-ToLA97ja5Zdi0XUwO8/edit?usp=sharing)**

## Files

### Task 1 - URL Shortener Lite
- `url_shortener.py`

### Task 2 - Rate Limiter Mini
- `rate_limiter.py`

### Task 3 - Simple Load Balancer Simulation
- `server1.py`
- `server2.py`
- `server3.py`
- `load_balancer.py`

## Install dependencies

```bash
cd <LOCAL_PATH>/PycharmProjects/url-shortener-lite
.venv/bin/python -m pip install -r requirements.txt
```

Use your machine's exact absolute project path in place of `<LOCAL_PATH>/PycharmProjects/url-shortener-lite`.

Path tip:

```bash
pwd
```

Run `pwd` inside the project folder and copy that full path into commands.

## Run each app

### Task 1
```bash
python url_shortener.py
```

### Task 2
```bash
python rate_limiter.py
```

### Task 3
Start all four processes in separate terminals:

```bash
python server1.py
python server2.py
python server3.py
python load_balancer.py
```

## Quick Task 3 test

```bash
curl -i http://127.0.0.1:5005/proxy
curl -i http://127.0.0.1:5005/proxy
curl -i http://127.0.0.1:5005/proxy
curl -i http://127.0.0.1:5005/proxy
```

Expected rotation:
1. `Hello from Server 1!`
2. `Hello from Server 2!`
3. `Hello from Server 3!`
4. back to `Hello from Server 1!`

## Troubleshooting

### 1) Postman shows `403 Forbidden` on `POST /shorten`
If you get `403` in Postman while calling:
- `POST http://127.0.0.1:5000/shorten`

check the following:
- Use **Postman Desktop Agent** (not cloud-only mode) for localhost requests.
- Disable proxy in Postman (`Settings -> Proxy`) if enabled.
- Ensure request is:
  - Method: `POST`
  - URL: `http://127.0.0.1:5000/shorten`
  - Header: `Content-Type: application/json`
  - Body type: `raw` + `JSON`
- Turn OFF auto-redirect in Postman for redirect checks (`GET /<short_id>`), so you can see local `302` instead of destination-site behavior.

Quick local verification:

```bash
curl -i -X POST http://127.0.0.1:5000/shorten \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.linkedin.com/in/umeshkmahato"}'
```

If this returns `201`, the local API is working and the Postman/client path is the issue.

### 2) App not running / connection refused
Check listeners:

```bash
lsof -n -P -iTCP:5000 -sTCP:LISTEN
lsof -n -P -iTCP:5004 -sTCP:LISTEN
lsof -n -P -iTCP:5001 -sTCP:LISTEN
lsof -n -P -iTCP:5002 -sTCP:LISTEN
lsof -n -P -iTCP:5003 -sTCP:LISTEN
lsof -n -P -iTCP:5005 -sTCP:LISTEN
```

### 3) Start everything quickly
Use the helper script:

```bash
bash <LOCAL_PATH>/PycharmProjects/url-shortener-lite/start_all.sh
```

This starts all apps for Task 1, Task 2, and Task 3 and prints status by port.

### 4) Automated end-to-end checks
Run all curl checks automatically:

```bash
chmod +x <LOCAL_PATH>/PycharmProjects/url-shortener-lite/run_tests.sh
<LOCAL_PATH>/PycharmProjects/url-shortener-lite/run_tests.sh
```

### 5) Postman import file
Import this file in Postman to get prebuilt requests:
- `postman_collection.json`

### 6) `.venv` issue (`python3 -m venv .venv`)
If scripts fail with errors like:
- `.../.venv/bin/python: No such file or directory`
- `command not found` for `.venv/bin/python`

it usually means the virtual environment is missing, corrupted, or not created in this folder.

Identify the issue:

```bash
cd <LOCAL_PATH>/PycharmProjects/url-shortener-lite
ls -la .venv
ls -la .venv/bin/python
```

If the files are missing, recreate the environment:

```bash
cd <LOCAL_PATH>/PycharmProjects/url-shortener-lite
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Verify it is fixed:

```bash
.venv/bin/python --version
.venv/bin/python -m pip --version
```

Then start apps again:

```bash
bash <LOCAL_PATH>/PycharmProjects/url-shortener-lite/start_all.sh
```

