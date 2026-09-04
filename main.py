from fastapi import FastAPI, BackgroundTasks
import uvicorn
from pydantic import BaseModel, Field
from starlette import status, background

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

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)