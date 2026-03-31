import os
import sqlite3
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from starlette.responses import JSONResponse
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Service Monitoring API", version="1.0.0", description="API for monitoring the status of services.")

# Database setup
DATABASE = 'db.sqlite3'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS services (
                serviceId TEXT PRIMARY KEY,
                token TEXT NOT NULL,
                lastNotification TEXT NOT NULL
            )
        ''')
        conn.commit()

init_db()

class HeartbeatRequest(BaseModel):
    serviceId: str
    token: str

class ServicesRequest(BaseModel):
    token: str

@app.post("/heartbeat", status_code=HTTP_200_OK)
async def register_heartbeat(request: HeartbeatRequest):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            cursor.execute('''
                INSERT INTO services (serviceId, token, lastNotification)
                VALUES (?, ?, ?)
                ON CONFLICT(serviceId) DO UPDATE SET lastNotification=excluded.lastNotification
            ''', (request.serviceId, request.token, now))
            conn.commit()
        return JSONResponse(content={"message": "Heartbeat registered successfully."}, status_code=HTTP_200_OK)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=HTTP_500_INTERNAL_SERVER_ERROR)

@app.post("/services", status_code=HTTP_200_OK)
async def get_services_overview(request: ServicesRequest):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT serviceId, lastNotification FROM services WHERE token=?
            ''', (request.token,))
            services = cursor.fetchall()
            services_list = [{"serviceId": service[0], "lastNotification": service[1]} for service in services]
        return JSONResponse(content=services_list, status_code=HTTP_200_OK)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=HTTP_500_INTERNAL_SERVER_ERROR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)