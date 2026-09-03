from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()

@app.post("/webhook")
async def receive_incident(request: Request):
    data = await request.json()
    print("\n--- Received Incident from ServiceNow ---")
    print(data)
    return {"status": "success", "received": data.get("number")}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)