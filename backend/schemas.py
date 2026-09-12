from pydantic import BaseModel
from typing import Optional

class TelemetryCreate(BaseModel):
    timestamp: Optional[float] = None
    cpu_usage: float
    memory_usage: float
    available_memory_mb: float
    disk_usage: float
    gpu_utilization: Optional[float] = None
    gpu_memory_used_mb: Optional[float] = None
    gpu_temp_c: Optional[float] = None

class TelemetryResponse(BaseModel):
    id: int
    timestamp: float
    cpu_usage: float
    memory_usage: float
    available_memory_mb: float
    disk_usage: float
    gpu_utilization: Optional[float] = None
    gpu_memory_used_mb: Optional[float] = None
    gpu_temp_c: Optional[float] = None

    class Config:
        orm_mode = True