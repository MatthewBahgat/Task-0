# Task 0 — Agentic Incident Flow on ServiceNow PDI

A small automation loop: when a new incident is created in ServiceNow, a Business Rule sends it to this FastAPI service, which asks Gemini to decide **respond**, **ask**, or **escalate** based on a fixed set of knowledge base articles, then writes the result back onto the same incident.

## How it works

1. A new incident is created in ServiceNow (PDI).
2. A Business Rule (`business_rule.js`) fires on insert and sends the incident's data as JSON to this service's `/webhook` endpoint.
3. `/webhook` validates the payload, responds `202 Accepted` immediately, and hands the real work to a background task.
4. The background task sends the ticket + the 5 knowledge articles to Gemini, asking for a JSON decision (`respond`, `ask`, or `escalate`) and a message.
5. Based on the decision, the service writes back to the same incident via the ServiceNow REST API:
   - **respond** → resolves the ticket, sets `work_notes` and `close_notes` with the solution
   - **ask** → adds a customer-visible comment asking for more detail
   - **escalate** → adds an internal work note flagging it for human attention
6. If the same incident arrives twice, it's only processed once (in-memory guard).

## Requirements

- Python 3.11+
- A free ServiceNow PDI (developer instance)
- A free Gemini API key (Google AI Studio)
- ngrok (or any tunnel) to expose your local service publicly

## Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/MatthewBahgat/Task-0.git
cd Task-0
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and fill in your real values:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Your Gemini API key from [Google AI Studio](https://aistudio.google.com) |
| `SN_INSTANCE_URL` | Your ServiceNow PDI base URL, e.g. `https://devXXXXXX.service-now.com` (no trailing slash) |
| `SN_USERNAME` | Your ServiceNow admin username |
| `SN_PASSWORD` | Your ServiceNow admin password |

### 3. Run the service

```bash
uvicorn main:app --reload
```

The service starts at `http://127.0.0.1:8000`. You can inspect and test the `/webhook` endpoint directly at `http://127.0.0.1:8000/docs`.

### 4. Expose the service publicly with ngrok

```bash
ngrok http 8000
```

Copy the generated `https://....ngrok-free.app` URL.

### 5. Connect ServiceNow to your service

Follow `pdi_guide.md` (included in the asset pack) to:
- Request your free PDI
- Create the Business Rule using `business_rule.js`, replacing `YOUR_ENDPOINT` with your ngrok URL + `/webhook`

### 6. Test it

Create a new incident in your PDI (Application Navigator → search "Incident" → "Create New"). Within a few seconds, your terminal should show the incident being received, processed, and the decision being written back. Refresh the incident form to see the update.

You can also test the three sample tickets in `test_incidents.json` directly via `/docs` without needing a real ServiceNow ticket.

## Project files

| File | Purpose |
|---|---|
| `main.py` | The FastAPI service — webhook, Gemini decision logic, ServiceNow write-back |
| `prompt.txt` | The exact Gemini prompt template used, as sent by the service |
| `business_rule.js` | ServiceNow Business Rule script (from the asset pack) |
| `kb_articles.json` | The 5 knowledge articles the agent is restricted to |
| `test_incidents.json` | Three sample tickets with their expected decisions |
| `payload_contract.json` | Reference for the exact JSON shape ServiceNow sends |
| `.env.example` | Names of required environment variables (no real values) |
| `reflection.md` | Reflection on the hardest parts and what could be improved |

## Notes

- The Gemini and ServiceNow calls run as a FastAPI `BackgroundTask`, so `/webhook` always responds within ~2 seconds regardless of how long the decision/write-back takes.
- Duplicate incidents (same `incident_sys_id` arriving twice) are only processed once, using an in-memory set. This resets if the service restarts.
- A free ServiceNow PDI goes to sleep after periods of inactivity — if the Business Rule seems to not be firing, check that your instance is awake.
