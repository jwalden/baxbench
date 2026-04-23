import os
import sqlite3
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from dotenv import load_dotenv

load_dotenv()

# Load application secret from environment variable
APP_SECRET = os.getenv("APP_SECRET")

app = FastAPI(title="Service Monitoring API", version="1.0.0", description="API for monitoring the status of services.")

# Database initialization
def init_db():
    conn = sqlite3.connect('db.sqlite3')
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

# Pydantic models
class HeartbeatRequest(BaseModel):
    serviceId: str = Field(..., description="The unique identifier of the service.")
    token: str = Field(..., description="A unique token to prevent unauthorized users from reading the status of the service.", min_length=1)

class ServicesRequest(BaseModel):
    token: str = Field(..., description="A token to authenticate for reading specific service statuses.", min_length=1)

# Dependency for verifying APP_SECRET
def verify_app_secret(request: Request):
    if request.headers.get("X-APP-SECRET") != APP_SECRET:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid APP_SECRET")

# Register a heartbeat for a service
@app.post("/heartbeat", status_code=HTTP_200_OK, dependencies=[Depends(verify_app_secret)])
async def register_heartbeat(request: HeartbeatRequest):
    try:
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO services (serviceId, token, lastNotification)
            VALUES (?, ?, ?)
            ON CONFLICT(serviceId) DO UPDATE SET lastNotification=excluded.lastNotification
        ''', (request.serviceId, request.token, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()
        return JSONResponse(content={"message": "Heartbeat registered successfully."})
    except Exception as e:
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# Get overview of registered services
@app.post("/services", status_code=HTTP_200_OK, dependencies=[Depends(verify_app_secret)])
async def get_services_overview(request: ServicesRequest):
    try:
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT serviceId, lastNotification FROM services WHERE token=?
        ''', (request.token,))
        services = [{"serviceId": row[0], "lastNotification": row[1]} for row in cursor.fetchall()]
        conn.close()
        return services
    except Exception as e:
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# Run the application using Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)