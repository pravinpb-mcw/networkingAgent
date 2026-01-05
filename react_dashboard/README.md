# Network Observability - React Dashboard

This is a modern, React-based dashboard for the Network Observability Agent system. It replaces the legacy HTML/JS dashboard with a professional, component-based UI using:

- **React 19** & **Vite**
- **TypeScript**
- **Tailwind CSS v4**
- **Shadcn UI** components
- **Recharts** for visualization
- **Lucide React** for icons

## Prerequisites

- Node.js (v18 or higher)
- Python 3.10+ (for the backend)

## Setup & Running

The easiest way to run the system is using the provided batch file in the `batch/` directory:

```bash
..\batch\start_react_dashboard.bat
```

This script will:
1. Start the Python Backend API (FastAPI) on port 8000.
2. Install Node dependencies (if needed).
3. Start the React Frontend (Vite) on port 5173.

## Manual Setup

### 1. Start Backend
From the root directory:
```bash
python -m uvicorn dashboard.backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Start Frontend
From the `react_dashboard` directory:
```bash
npm install
npm run dev
```

## Features

- **Real-time Monitoring**: Live updates of network risk scores and agent status.
- **AI Analysis Feed**: Stream of insights from the autonomous agents.
- **Interactive Charts**: Visualization of risk trends and network metrics.
- **System Controls**: Start/Stop agents, configure webhooks, and simulate network failures.
- **Phoenix Integration**: Embedded view of Phoenix Traces for debugging.
