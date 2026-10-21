# Competency Tracker API

A REST API I built with FastAPI to track the skills I'm learning. It supports
GET, POST, PUT, PATCH and DELETE, and every response (errors included) is JSON.

## Setup

Needs Python 3.10+.

```bash
pip install -r requirements-dev.txt
```

## Running it

```bash
uvicorn main:app --reload
```

Then open http://127.0.0.1:8000/docs to try out the endpoints.

Run the tests with:

```bash
pytest -v
```
