# Network Observability Dashboard (v2.0)

A professional, high-performance monitoring interface for the Network Observability Agent System.

## 🚀 Features

- **Real-time Monitoring**: Live status of all 3 AI agents and Phoenix server.
- **Risk Visualization**: Interactive charts showing risk trends and distribution across APs.
- **AI Analysis Feed**: A chat-style interface displaying the reasoning and decisions made by the Failover Agent (Agent 3).
- **Phoenix Integration**: Embedded view of the Phoenix observability traces.
- **System Control**: Start/Stop agents directly from the UI.

## 🛠 Tech Stack

- **Backend**: FastAPI (Python) - High performance, async API.
- **Frontend**: Vanilla JS + HTML5 - Lightweight, no build step required.
- **Styling**: Custom CSS3 with Glassmorphism design and responsive layout.
- **Charts**: Chart.js for data visualization.

## 🏃‍♂️ How to Run

Simply run the startup script in the `networkingAgent` directory:

```bash
start_dashboard.bat
```

This will:
1. install/verify dependencies
2. Start the API server
3. Launch your default browser to `http://localhost:8000`

## 📁 Structure

- `backend/`: FastAPI application and API endpoints.
- `frontend/`: Static HTML/JS/CSS files.
- `frontend/static/`: Assets and styles.
