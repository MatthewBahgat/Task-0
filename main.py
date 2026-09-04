from fastapi import FastAPI, BackgroundTasks
import uvicorn
from pydantic import BaseModel, Field
from starlette import status, background
from dotenv import load_dotenv
import google.generativeai as genai
import os
import json


load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
with open("kb_articles.json") as f:
    kb_data = json.load(f)
app = FastAPI()
class IncidentPayload(BaseModel):
    incident_sys_id: str
    number: str
    short_description: str
    description: str
    priority: int = Field(..., ge=1, le=5)

@app.post("/webhook", status_code=status.HTTP_202_ACCEPTED)

async def receive_incident(request: IncidentPayload,  background_tasks: BackgroundTasks):
    print("\n--- Received Incident from ServiceNow ---")
    print(request)
    background_tasks.add_task(process_incident, request)
    return {"status": "success", "received": request.number}

async def process_incident(incident: IncidentPayload):
    print(f"processing {incident.number} in background")
    model = genai.GenerativeModel("gemini-3.6-flash")
    articles_text = ""
    for article in kb_data["articles"]:
        articles_text += f"- {article['text']}\n"

    prompt = f"""
    You are a support ticket triage assistant. You must decide one of: respond, ask, escalate.

    Rules:
    - Respond only when the ticket clearly matches one article and provides sufficient detail — a specific symptom or a troubleshooting step already attempted — to be confident the article's fix applies.
    - Ask when the ticket relates to a topic covered by an article, but lacks enough detail (e.g., no specific symptom or prior troubleshooting mentioned) to confidently apply that article's fix. In this case, request the missing information.
    - Escalate when none of the knowledge articles cover the ticket's topic
    Knowledge articles:
    {articles_text}

    Ticket:
    Short description: {incident.short_description}
    Description: {incident.description}

    Respond in JSON format with exactly two fields: a decision (respond, ask, or escalate) and a message. If the decision is respond, the message should be the fix or solution to give the user, based on the matching article. If the decision is ask, the message should be a clarifying question to help figure out what's actually wrong. If the decision is escalate, the message should briefly note that this needs human attention since none of the articles cover it.
    Return only the raw JSON object with no markdown formatting, no code fences, and no extra text before or after it.
    """

    response = model.generate_content(prompt)
    dic = json.loads(response.text)
    print(dic["decision"])
    print(dic["message"])



if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)