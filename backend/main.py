from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import time

from backend.database import get_db_connection, init_db
from backend.schemas import TelemetryCreate, TelemetryResponse

app = FastAPI(title="Telemetry Dashboard API", version="1.0.0")

# Enable CORS so your frontend can communicate cleanly with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    """Ensure the database and tables exist when the server starts."""
    init_db()

@app.post("/telemetry", response_model=TelemetryResponse)
def receive_telemetry(data: TelemetryCreate):
    """Ingests a new batch of system and GPU telemetry metrics from the agent."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO metrics (
            timestamp, cpu_usage, memory_usage, available_memory_mb, 
            disk_usage, gpu_utilization, gpu_memory_used_mb, gpu_temp_c
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.timestamp or time.time(),
        data.cpu_usage,
        data.memory_usage,
        data.available_memory_mb,
        data.disk_usage,
        data.gpu_utilization,
        data.gpu_memory_used_mb,
        data.gpu_temp_c
    ))
    
    conn.commit()
    metric_id = cursor.lastrowid
    
    # Fetch the newly inserted row to return it
    cursor.execute("SELECT * FROM metrics WHERE id = ?", (metric_id,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row)

@app.get("/metrics/latest", response_model=TelemetryResponse)
def get_latest_metrics():
    """Retrieves the most recent system telemetry data point for the dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="No telemetry metrics found.")
        
    return dict(row)

@app.get("/")
def root():
    return {"status": "online", "message": "Telemetry API is running."}
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")