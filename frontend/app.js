const API_BASE = "http://localhost:8000";
const maxDataPoints = 20;

const ctx = document.getElementById('telemetryChart').getContext('2d');
const telemetryChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [
            { label: 'CPU %', borderColor: '#34d399', backgroundColor: '#34d399', data: [], tension: 0.2 },
            { label: 'RAM %', borderColor: '#60a5fa', backgroundColor: '#60a5fa', data: [], tension: 0.2 },
            { label: 'GPU Util %', borderColor: '#c084fc', backgroundColor: '#c084fc', data: [], tension: 0.2 }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: { beginAtZero: true, max: 100, grid: { color: '#27272a' } },
            x: { grid: { display: false } }
        },
        animation: false
    }
});

async function fetchLatestMetrics() {
    try {
        const response = await fetch(`${API_BASE}/metrics/latest`);
        if (!response.ok) throw new Error("API offline");
        
        const data = await response.json();

        document.getElementById('status-dot').className = "w-2.5 h-2.5 rounded-full bg-emerald-500";
        document.getElementById('status-text').innerText = "Live Ingestion Active";

        document.getElementById('card-cpu').innerText = data.cpu_usage.toFixed(1) + "%";
        document.getElementById('card-ram').innerText = data.memory_usage.toFixed(1) + "%";
        document.getElementById('card-gpu-util').innerText = data.gpu_utilization !== null ? data.gpu_utilization.toFixed(1) + "%" : "N/A";
        document.getElementById('card-gpu-temp').innerText = data.gpu_temp_c !== null ? data.gpu_temp_c.toFixed(1) + "°C" : "N/A";

        const timeLabel = new Date(data.timestamp * 1000).toLocaleTimeString();
        
        if (telemetryChart.data.labels.length >= maxDataPoints) {
            telemetryChart.data.labels.shift();
            telemetryChart.data.datasets.forEach(dataset => dataset.data.shift());
        }

        telemetryChart.data.labels.push(timeLabel);
        telemetryChart.data.datasets[0].data.push(data.cpu_usage);
        telemetryChart.data.datasets[1].data.push(data.memory_usage);
        telemetryChart.data.datasets[2].data.push(data.gpu_utilization || 0);
        telemetryChart.update();

    } catch (err) {
        document.getElementById('status-dot').className = "w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse bg-red-500";
        document.getElementById('status-text').innerText = "Waiting for Backend...";
    }
}

setInterval(fetchLatestMetrics, 2000);