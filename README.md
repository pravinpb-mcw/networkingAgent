# Network Observability Agent Dashboard

A comprehensive Network Observability Dashboard powered by **Cisco Meraki**, **MCP (Model Context Protocol)**, and **LLM (Large Language Model)** integration. This tool provides real-time network monitoring, automated insights, and an interactive chat interface to query your network status using natural language.

## 🚀 Features

-   **Real-time Monitoring**: Track packet loss, latency, jitter, and traffic patterns.
-   **Interactive AI Chat**: Ask questions about your network (e.g., "Check for packet loss", "Show top clients") and get instant answers.
-   **Automated Insights**: The AI agent analyzes network data to identify anomalies and security threats.
-   **Visual Analytics**: Interactive charts and graphs for performance trends and data volume.
-   **MCP Integration**: Built on the Model Context Protocol for standardized tool usage.

## 📋 Prerequisites

-   **Python 3.10+**
-   **Cisco Meraki Account** (with API access)
-   **LLM API Key** (Anthropic, Gemini, or ZhipuAI)

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd networkingAgent
```

### 2. Set Up Virtual Environment
It is recommended to use a virtual environment to manage dependencies.

**Windows:**
```powershell
# Create virtual environment
python -m venv .wenv

# Activate virtual environment
.wenv\Scripts\activate
```

**macOS/Linux:**
```bash
# Create virtual environment
python3 -m venv .wenv

# Activate virtual environment
source .wenv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the `networkingAgent` directory with your API keys and configuration.

```ini
# Cisco Meraki API Configuration
MERAKI_API_KEY=your_meraki_api_key_here
BASE_URL=https://api.meraki.com/api/v1
NETWORK_ID=your_network_id
ORGANIZATION_ID=your_organization_id
SERIAL=your_device_serial
IP=your_device_ip
PRODUCT_TYPE=appliance
TIMESPAN=86400

# LLM Configuration (Choose one or more)
ANTHROPIC_API_KEY=your_anthropic_key
ANTHROPIC_BASE_URL=https://api.anthropic.com # Optional: Custom base URL
GEMINI_API_KEY=your_gemini_key
ZHIPUAI_API_KEY=your_zhipuai_key
```

**How to get Meraki IDs:**
-   **NETWORK_ID**: Found in the URL of your Meraki Dashboard when viewing a network.
-   **ORGANIZATION_ID**: Found in the URL when viewing Organization Settings.

## 🖥️ Usage

### Start the Dashboard
Run the Streamlit application:

```bash
streamlit run dashboard.py
```

The dashboard will open in your default web browser (usually at `http://localhost:8501`).

### Using the Chatbot
1.  Navigate to the **MCP Chatbot** tab.
2.  Use the **Quick Commands** buttons for common tasks (e.g., "Check Performance", "Top Clients").
3.  Or type your question in the chat input (e.g., "Is there any high latency on the network?").

### Network Monitor
1.  Navigate to the **Network Monitor** tab.
2.  Click **Start Monitoring** in the sidebar to begin real-time data collection.
3.  View live status and data points.

## 📂 Project Structure

```
networkingAgent/
├── dashboard.py                # Main Streamlit Dashboard application
├── mcp-inspector-config.json   # MCP Client configuration
├── requirements.txt            # Python dependencies
├── .env                        # Configuration file (not committed)
├── server/                     # MCP Server & Tools
│   ├── meraki_server.py        # MCP Server entry point
│   ├── meraki_client.py        # Shared Meraki API client
│   ├── get_network_clients.py  # Tool: Get connected clients
│   ├── get_network_traffic.py  # Tool: Analyze traffic
│   ├── get_network_events.py   # Tool: Get network events
│   └── ...
└── test/                       # Test scripts
    └── test_tools.py           # Tool verification script
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
