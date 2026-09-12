import time
import psutil
try:
    import requests
except ImportError:
    requests = None

from agent.config import API_URL, POLL_INTERVAL

# --- Tier 1: NVIDIA Initialization ---
NVML_AVAILABLE = False
try:
    import pynvml
    NVML_AVAILABLE = True
except ImportError:
    pass

def init_gpu():
    """Initializes the NVIDIA Management Library if available."""
    if NVML_AVAILABLE:
        try:
            pynvml.nvmlInit()
            return True
        except Exception as e:
            print(f"Notice: NVIDIA NVML not initialized: {e}")
    return False

# --- Tier 2: Alternative / Windows WMI Initialization (Optional for temperatures/secondary GPUs) ---
WMI_AVAILABLE = False
try:
    import wmi
    wmi_c = wmi.WMI(namespace="root\\WMI")
    WMI_AVAILABLE = True
except Exception:
    pass


def collect_nvidia_metrics():
    """Tier 1 collection strategy for NVIDIA hardware."""
    try:
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
        return {
            "gpu_utilization": float(util.gpu),
            "gpu_memory_used_mb": float(mem.used / (1024 * 1024)),
            "gpu_temp_c": float(temp)
        }
    except Exception:
        return None


def collect_alternative_metrics():
    """
    Tier 2 collection strategy for non-NVIDIA systems 
    (e.g., Snapdragon / AMD / Intel integrated graphics using Windows counters or WMI).
    """
    gpu_util = None
    gpu_mem = None
    gpu_temp = None

    # Example: If you want to expand WMI or Windows performance counters for CPU/GPU temp
    if WMI_AVAILABLE:
        try:
            # Example query for hardware temperatures if exposed by ACPI
            temperatures = wmi_c.MSAcpi_ThermalZoneTemperature()
            if temperatures:
                # Convert Kelvin (tenths) to Celsius
                gpu_temp = (temperatures[0].CurrentTemperature / 10.0) - 273.15
        except Exception:
            pass

    # You can add custom logic here for Snapdragon/Adreno counters via PowerShell subprocess 
    # or Windows performance counters if specific metrics are required.

    return {
        "gpu_utilization": gpu_util,
        "gpu_memory_used_mb": gpu_mem,
        "gpu_temp_c": gpu_temp
    }


def get_system_metrics():
    """Aggregates system telemetry using a cascading fallback strategy."""
    # Standard CPU and Memory via psutil
    cpu_usage = psutil.cpu_percent(interval=None)
    mem_info = psutil.virtual_memory()
    disk_info = psutil.disk_usage('C:\\' if psutil.WINDOWS else '/')

    # Try Tier 1: NVIDIA
    gpu_data = None
    if NVML_AVAILABLE:
        gpu_data = collect_nvidia_metrics()

    # Try Tier 2: Alternative / Windows System Counters if Tier 1 returned nothing
    if not gpu_data:
        gpu_data = collect_alternative_metrics()

    # Tier 3: Final fallback to null (None) if no GPU telemetry source is active
    if not gpu_data:
        gpu_data = {
            "gpu_utilization": None,
            "gpu_memory_used_mb": None,
            "gpu_temp_c": None
        }

    payload = {
        "timestamp": time.time(),
        "cpu_usage": float(cpu_usage),
        "memory_usage": float(mem_info.percent),
        "available_memory_mb": float(mem_info.available / (1024 * 1024)),
        "disk_usage": float(disk_info.percent),
        "gpu_utilization": gpu_data.get("gpu_utilization"),
        "gpu_memory_used_mb": gpu_data.get("gpu_memory_used_mb"),
        "gpu_temp_c": gpu_data.get("gpu_temp_c")
    }
    
    return payload


def run_agent():
    print(f"Starting telemetry agent... Reporting to {API_URL}")
    is_nvidia = init_gpu()
    if is_nvidia:
        print("Hardware detected: NVIDIA GPU via NVML.")
    else:
        print("Hardware detected: Non-NVIDIA system (Running with multi-tier fallback / graceful nulls).")

    while True:
        try:
            metrics = get_system_metrics()
            if requests:
                response = requests.post(API_URL, json=metrics)
                if response.status_code == 200:
                    print(f"[Sent] CPU: {metrics['cpu_usage']}% | RAM: {metrics['memory_usage']}% | GPU Util: {metrics['gpu_utilization']}%")
                else:
                    print(f"[Error] Server responded with status {response.status_code}")
            else:
                print("[Error] 'requests' module not installed.")
        except Exception as e:
            print(f"[Connection Error] Could not reach backend: {e}")
        
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run_agent()