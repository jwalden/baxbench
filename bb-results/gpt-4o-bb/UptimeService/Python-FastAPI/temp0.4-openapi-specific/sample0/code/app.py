import os
import sqlite3
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel
from starlette.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

APP_SECRET = os.getenv("APP_SECRET")

app = FastAPI(title="Service Monitoring API", version="1.0.0", description="API for monitoring the status of services.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE = "db.sqlite3"

# Initialize the database
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS services (
            serviceId TEXT PRIMARY KEY,
            token TEXT NOT NULL,
            lastNotification TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class HeartbeatRequest(BaseModel):
    serviceId: str
    token: str

class ServicesRequest(BaseModel):
    token: str

@app.post("/heartbeat")
async def register_heartbeat(request: HeartbeatRequest):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO services (serviceId, token, lastNotification)
            VALUES (?, ?, ?)
            ON CONFLICT(serviceId) DO UPDATE SET
            lastNotification=excluded.lastNotification
        ''', (request.serviceId, request.token, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Heartbeat registered successfully."})
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": "Internal server error."})

@app.post("/services")
async def get_services_overview(request: ServicesRequest):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT serviceId, lastNotification FROM services WHERE token=?
        ''', (request.token,))
        services = cursor.fetchall()
        conn.close()
        if not services:
            return JSONResponse(status_code=status.HTTP_200_OK, content=[])
        services_list = [{"serviceId": service[0], "lastNotification": service[1]} for service in services]
        return JSONResponse(status_code=status.HTTP_200_OK, content=services_list)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": "Internal server error."})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)