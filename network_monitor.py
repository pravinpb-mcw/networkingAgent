#!/usr/bin/env python3
"""
Network Performance Monitor
Uses LLM and MCP tools to monitor latency, loss, and jitter every minute
"""

import asyncio
import json
import logging
import os
import sys
import time
import sqlite3
import statistics
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import deque

# Add the server directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

# Import MCP tools
from server.get_device_loss_and_latency_history import get_device_loss_and_latency_history
from server.get_network_traffic import get_network_traffic
from server.get_network_events import get_network_events

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('network_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("network-monitor")

class NetworkPerformanceMonitor:
    """Monitor network performance using LLM and MCP tools with trend analysis"""
    
    def __init__(self, db_path: str = "network_monitor.db", max_history: int = 1000, enable_webhooks: bool = False):
        """Initialize the network monitor"""
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file")
        
        # Initialize Gemini LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=self.gemini_api_key,
            temperature=0.3,
            max_tokens=1024
        )
        
        # Performance thresholds
        self.thresholds = {
            "latency_ms": 10.0,  # Alert if latency > 10ms
            "loss_percent": 1.0,  # Alert if loss > 1%
            "jitter": 2.0,        # Alert if jitter > 2ms
        }
        
        # Database and storage
        self.db_path = db_path
        self.max_history = max_history
        self.recent_data = deque(maxlen=max_history)  # In-memory recent data
        
        # Initialize webhook module if enabled
        self.webhook_module = None
        if enable_webhooks:
            try:
                from webhook_module import WebhookModule
                self.webhook_module = WebhookModule()
                if not self.webhook_module.is_configured():
                    logger.warning("Webhooks enabled but no webhook URLs configured")
            except ImportError as e:
                logger.error(f"Failed to import webhook module: {e}")
                logger.warning("Webhook functionality disabled")
        
        # Initialize database
        self._init_database()
        
        logger.info("Network Performance Monitor initialized with trend analysis")
    
    def _init_database(self):
        """Initialize SQLite database for storing historical data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    latency_ms REAL,
                    loss_percent REAL,
                    jitter REAL,
                    goodput REAL,
                    status TEXT,
                    alerts TEXT
                )
            ''')
            
            # Create trends table for aggregated data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trend_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    period TEXT NOT NULL,
                    avg_latency REAL,
                    avg_loss REAL,
                    avg_jitter REAL,
                    max_latency REAL,
                    max_loss REAL,
                    max_jitter REAL,
                    min_latency REAL,
                    min_loss REAL,
                    min_jitter REAL,
                    data_points INTEGER
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info(f"Database initialized: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def _save_metrics_to_db(self, metrics: Dict[str, Any], status: str, alerts: List[str]):
        """Save metrics to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO performance_metrics 
                (timestamp, latency_ms, loss_percent, jitter, goodput, status, alerts)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                metrics.get('latency_ms', 0),
                metrics.get('loss_percent', 0),
                metrics.get('jitter', 0),
                metrics.get('goodput', 0),
                status,
                json.dumps(alerts)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving metrics to database: {e}")
    
    def _get_historical_data(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical data from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get data from last N hours
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            cursor.execute('''
                SELECT timestamp, latency_ms, loss_percent, jitter, goodput, status, alerts
                FROM performance_metrics
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            ''', (cutoff_time,))
            
            rows = cursor.fetchall()
            conn.close()
            
            data = []
            for row in rows:
                data.append({
                    'timestamp': row[0],
                    'latency_ms': row[1],
                    'loss_percent': row[2],
                    'jitter': row[3],
                    'goodput': row[4],
                    'status': row[5],
                    'alerts': json.loads(row[6]) if row[6] else []
                })
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return []
    
    def analyze_trends(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends in historical data"""
        if not historical_data:
            return {'trends': 'No historical data available'}
        
        trends = {
            'latency_trend': self._calculate_trend([d['latency_ms'] for d in historical_data]),
            'loss_trend': self._calculate_trend([d['loss_percent'] for d in historical_data]),
            'jitter_trend': self._calculate_trend([d['jitter'] for d in historical_data]),
            'statistics': self._calculate_statistics(historical_data),
            'anomalies': self._detect_anomalies(historical_data),
            'periods': self._analyze_periods(historical_data)
        }
        
        return trends
    
    def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """Calculate trend direction and magnitude"""
        if len(values) < 2:
            return {'direction': 'insufficient_data', 'magnitude': 0, 'change_percent': 0}
        
        # Simple linear trend calculation
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        if not first_half or not second_half:
            return {'direction': 'insufficient_data', 'magnitude': 0, 'change_percent': 0}
        
        avg_first = statistics.mean(first_half)
        avg_second = statistics.mean(second_half)
        
        change = avg_second - avg_first
        change_percent = (change / avg_first * 100) if avg_first > 0 else 0
        
        if change > 0:
            direction = 'increasing'
        elif change < 0:
            direction = 'decreasing'
        else:
            direction = 'stable'
        
        return {
            'direction': direction,
            'magnitude': abs(change),
            'change_percent': change_percent,
            'current_avg': avg_second,
            'previous_avg': avg_first
        }
    
    def _calculate_statistics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistical measures"""
        latencies = [d['latency_ms'] for d in data]
        losses = [d['loss_percent'] for d in data]
        jitters = [d['jitter'] for d in data]
        
        return {
            'latency': {
                'mean': statistics.mean(latencies) if latencies else 0,
                'median': statistics.median(latencies) if latencies else 0,
                'std': statistics.stdev(latencies) if len(latencies) > 1 else 0,
                'min': min(latencies) if latencies else 0,
                'max': max(latencies) if latencies else 0
            },
            'loss': {
                'mean': statistics.mean(losses) if losses else 0,
                'median': statistics.median(losses) if losses else 0,
                'std': statistics.stdev(losses) if len(losses) > 1 else 0,
                'min': min(losses) if losses else 0,
                'max': max(losses) if losses else 0
            },
            'jitter': {
                'mean': statistics.mean(jitters) if jitters else 0,
                'median': statistics.median(jitters) if jitters else 0,
                'std': statistics.stdev(jitters) if len(jitters) > 1 else 0,
                'min': min(jitters) if jitters else 0,
                'max': max(jitters) if jitters else 0
            }
        }
    
    def _detect_anomalies(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalies in the data"""
        anomalies = []
        
        if len(data) < 3:
            return anomalies
        
        latencies = [d['latency_ms'] for d in data]
        losses = [d['loss_percent'] for d in data]
        jitters = [d['jitter'] for d in data]
        
        # Simple anomaly detection using 2 standard deviations
        for i, (lat, loss, jit) in enumerate(zip(latencies, losses, jitters)):
            if i < 2:  # Skip first few points
                continue
            
            # Check for latency anomalies
            if lat > statistics.mean(latencies[:i]) + 2 * statistics.stdev(latencies[:i]):
                anomalies.append({
                    'timestamp': data[i]['timestamp'],
                    'type': 'high_latency',
                    'value': lat,
                    'threshold': statistics.mean(latencies[:i]) + 2 * statistics.stdev(latencies[:i])
                })
            
            # Check for loss anomalies
            if loss > statistics.mean(losses[:i]) + 2 * statistics.stdev(losses[:i]):
                anomalies.append({
                    'timestamp': data[i]['timestamp'],
                    'type': 'high_loss',
                    'value': loss,
                    'threshold': statistics.mean(losses[:i]) + 2 * statistics.stdev(losses[:i])
                })
        
        return anomalies
    
    def _analyze_periods(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance by time periods"""
        if not data:
            return {}
        
        # Group by hour
        hourly_stats = {}
        for entry in data:
            dt = datetime.fromisoformat(entry['timestamp'])
            hour = dt.strftime('%Y-%m-%d %H:00')
            
            if hour not in hourly_stats:
                hourly_stats[hour] = []
            hourly_stats[hour].append(entry)
        
        # Calculate hourly averages
        hourly_averages = {}
        for hour, entries in hourly_stats.items():
            hourly_averages[hour] = {
                'avg_latency': statistics.mean([e['latency_ms'] for e in entries]),
                'avg_loss': statistics.mean([e['loss_percent'] for e in entries]),
                'avg_jitter': statistics.mean([e['jitter'] for e in entries]),
                'count': len(entries)
            }
        
        return {'hourly_averages': hourly_averages}
    
    async def collect_performance_data(self) -> Dict[str, Any]:
        """Collect performance data from MCP tools"""
        logger.info("Collecting performance data...")
        
        data = {}
        
        try:
            # Get device performance data
            logger.info("Getting device loss and latency history...")
            performance_response = await get_device_loss_and_latency_history()
            # Parse the JSON from the response
            performance_data = json.loads(performance_response[0].text)
            data['performance'] = performance_data
            
            # Get network traffic data
            logger.info("Getting network traffic data...")
            traffic_response = await get_network_traffic()
            # Parse the JSON from the response
            traffic_data = json.loads(traffic_response[0].text)
            data['traffic'] = traffic_data
            
            # Get network events
            logger.info("Getting network events...")
            events_response = await get_network_events()
            # Parse the JSON from the response
            events_data = json.loads(events_response[0].text)
            data['events'] = events_data
            
            logger.info("Performance data collection completed")
            
        except Exception as e:
            logger.error(f"Error collecting performance data: {e}")
            data['error'] = str(e)
        
        return data
    
    def analyze_performance_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance metrics and detect issues with trend analysis"""
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'alerts': [],
            'metrics': {},
            'status': 'normal',
            'trends': {},
            'historical_context': {}
        }
        
        try:
            performance = data.get('performance', {})
            
            if 'data' in performance and isinstance(performance['data'], list):
                # Get the most recent valid data point
                latest_data = {}
                for data_point in performance['data']:
                    if data_point.get('latencyMs') is not None:
                        latest_data = data_point
                        break
                
                # Extract metrics
                latency = latest_data.get('latencyMs', 0)
                loss = latest_data.get('lossPercent', 0)
                jitter = latest_data.get('jitter', 0)
                goodput = latest_data.get('goodput', 0)
                
                analysis['metrics'] = {
                    'latency_ms': latency,
                    'loss_percent': loss,
                    'jitter': jitter,
                    'goodput': goodput
                }
                
                # Get historical data for trend analysis
                historical_data = self._get_historical_data(hours=24)
                
                # Add current data point to historical analysis
                current_point = {
                    'timestamp': datetime.now().isoformat(),
                    'latency_ms': latency,
                    'loss_percent': loss,
                    'jitter': jitter,
                    'goodput': goodput,
                    'status': 'current',
                    'alerts': []
                }
                
                # Analyze trends
                if historical_data:
                    trends = self.analyze_trends(historical_data + [current_point])
                    analysis['trends'] = trends
                    
                    # Add trend-based alerts
                    self._add_trend_alerts(analysis, trends)
                
                # Check current thresholds and create alerts
                if latency > self.thresholds['latency_ms']:
                    analysis['alerts'].append(f"HIGH LATENCY: {latency}ms (threshold: {self.thresholds['latency_ms']}ms)")
                    analysis['status'] = 'warning'
                
                if loss > self.thresholds['loss_percent']:
                    analysis['alerts'].append(f"PACKET LOSS: {loss}% (threshold: {self.thresholds['loss_percent']}%)")
                    analysis['status'] = 'critical'
                
                if jitter > self.thresholds['jitter']:
                    analysis['alerts'].append(f"HIGH JITTER: {jitter}ms (threshold: {self.thresholds['jitter']}ms)")
                    analysis['status'] = 'warning'
                
                # Overall status
                if analysis['status'] == 'normal':
                    analysis['alerts'].append("All metrics within normal ranges")
                
                # Save to database
                self._save_metrics_to_db(analysis['metrics'], analysis['status'], analysis['alerts'])
                
        except Exception as e:
            logger.error(f"Error analyzing metrics: {e}")
            analysis['alerts'].append(f"Analysis error: {str(e)}")
            analysis['status'] = 'error'
        
        return analysis
    
    def _add_trend_alerts(self, analysis: Dict[str, Any], trends: Dict[str, Any]):
        """Add trend-based alerts to the analysis"""
        try:
            # Latency trend alerts
            latency_trend = trends.get('latency_trend', {})
            if latency_trend.get('direction') == 'increasing' and latency_trend.get('change_percent', 0) > 20:
                analysis['alerts'].append(f"LATENCY TREND: Increasing by {latency_trend['change_percent']:.1f}%")
                if analysis['status'] == 'normal':
                    analysis['status'] = 'warning'
            
            # Loss trend alerts
            loss_trend = trends.get('loss_trend', {})
            if loss_trend.get('direction') == 'increasing' and loss_trend.get('change_percent', 0) > 50:
                analysis['alerts'].append(f"LOSS TREND: Increasing by {loss_trend['change_percent']:.1f}%")
                if analysis['status'] == 'normal':
                    analysis['status'] = 'warning'
            
            # Anomaly alerts
            anomalies = trends.get('anomalies', [])
            if anomalies:
                recent_anomalies = [a for a in anomalies if a.get('timestamp')]
                if recent_anomalies:
                    analysis['alerts'].append(f"ANOMALIES: {len(recent_anomalies)} recent anomalies detected")
            
        except Exception as e:
            logger.error(f"Error adding trend alerts: {e}")
    
    async def get_llm_insights(self, data: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Get LLM insights on the performance data"""
        try:
            # Create a summary of the data for the LLM
            performance_summary = self._create_performance_summary(data, analysis)
            
            # System prompt for performance analysis
            system_prompt = """You are a network performance analyst expert. 
            Analyze the provided network performance data and provide structured, actionable insights.
            
            ALWAYS format your response in this exact structure:
            
            STATUS: [Normal/Warning/Critical] - Brief status summary
            
            PERFORMANCE ISSUES:
            • [Issue 1 with specific metrics]
            • [Issue 2 with specific metrics]
            • [None if no issues detected]
            
            ROOT CAUSES:
            • [Possible cause 1]
            • [Possible cause 2]
            • [None if no issues]
            
            RECOMMENDATIONS:
            • [Specific action 1]
            • [Specific action 2]
            • [Continue monitoring if normal]
            
            TRENDS:
            • [Trend 1 with percentage/values]
            • [Trend 2 with percentage/values]
            • [No significant trends if stable]
            
            Keep each section concise and actionable. Use bullet points consistently."""
            
            # Human prompt
            human_prompt = f"""Analyze this network performance data:

{performance_summary}

Provide a structured analysis following the exact format specified. Focus on actionable insights and specific recommendations."""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            response = await self.llm.agenerate([messages])
            insights = response.generations[0][0].text
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting LLM insights: {e}")
            return f"Unable to get LLM insights: {str(e)}"
    
    def _create_performance_summary(self, data: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Create a summary of performance data for LLM analysis including trends"""
        summary_parts = []
        
        # Add analysis results
        summary_parts.append("**Performance Analysis:**")
        summary_parts.append(f"Status: {analysis.get('status', 'unknown')}")
        summary_parts.append(f"Timestamp: {analysis.get('timestamp', 'unknown')}")
        
        # Add metrics
        metrics = analysis.get('metrics', {})
        if metrics:
            summary_parts.append("\n**Current Metrics:**")
            summary_parts.append(f"• Latency: {metrics.get('latency_ms', 'N/A')}ms")
            summary_parts.append(f"• Packet Loss: {metrics.get('loss_percent', 'N/A')}%")
            summary_parts.append(f"• Jitter: {metrics.get('jitter', 'N/A')}ms")
            summary_parts.append(f"• Goodput: {metrics.get('goodput', 'N/A')}")
        
        # Add trend analysis
        trends = analysis.get('trends', {})
        if trends:
            summary_parts.append("\n**Trend Analysis (24h):**")
            
            # Latency trend
            latency_trend = trends.get('latency_trend', {})
            if latency_trend.get('direction') != 'insufficient_data':
                summary_parts.append(f"• Latency: {latency_trend.get('direction', 'unknown')} ({latency_trend.get('change_percent', 0):.1f}% change)")
            
            # Loss trend
            loss_trend = trends.get('loss_trend', {})
            if loss_trend.get('direction') != 'insufficient_data':
                summary_parts.append(f"• Packet Loss: {loss_trend.get('direction', 'unknown')} ({loss_trend.get('change_percent', 0):.1f}% change)")
            
            # Jitter trend
            jitter_trend = trends.get('jitter_trend', {})
            if jitter_trend.get('direction') != 'insufficient_data':
                summary_parts.append(f"• Jitter: {jitter_trend.get('direction', 'unknown')} ({jitter_trend.get('change_percent', 0):.1f}% change)")
            
            # Statistics
            stats = trends.get('statistics', {})
            if stats:
                summary_parts.append("\n**Statistical Summary:**")
                latency_stats = stats.get('latency', {})
                if latency_stats:
                    summary_parts.append(f"• Latency: Avg={latency_stats.get('mean', 0):.2f}ms, Std={latency_stats.get('std', 0):.2f}ms")
                
                loss_stats = stats.get('loss', {})
                if loss_stats:
                    summary_parts.append(f"• Loss: Avg={loss_stats.get('mean', 0):.2f}%, Std={loss_stats.get('std', 0):.2f}%")
            
            # Anomalies
            anomalies = trends.get('anomalies', [])
            if anomalies:
                summary_parts.append(f"\n**Anomalies Detected:** {len(anomalies)}")
                for anomaly in anomalies[:3]:  # Show first 3 anomalies
                    summary_parts.append(f"• {anomaly.get('type', 'unknown')}: {anomaly.get('value', 0)} at {anomaly.get('timestamp', 'unknown')}")
        
        # Add alerts
        alerts = analysis.get('alerts', [])
        if alerts:
            summary_parts.append("\n**Alerts:**")
            for alert in alerts:
                summary_parts.append(f"• {alert}")
        
        # Add data summary
        if 'performance' in data:
            perf_data = data['performance']
            if 'data' in perf_data and isinstance(perf_data['data'], list):
                summary_parts.append(f"\n**Data Points:** {len(perf_data['data'])} recent measurements")
        
        return "\n".join(summary_parts)
    
    def display_insights(self, analysis: Dict[str, Any], insights: str):
        """Display the insights in a formatted way with trend analysis"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print("\n" + "="*80)
        print(f"NETWORK PERFORMANCE MONITOR - {timestamp}")
        print("="*80)
        
        # Display status
        status = analysis.get('status', 'unknown')
        print(f"Status: {status.upper()}")
        
        # Display metrics
        metrics = analysis.get('metrics', {})
        if metrics:
            print("\nCurrent Metrics:")
            print("   " + "="*60)
            print("   | Metric      | Value    | Threshold | Status  |")
            print("   |" + "-"*58 + "|")
            
            # Latency
            latency = metrics.get('latency_ms', 'N/A')
            latency_status = "NORMAL" if latency == 'N/A' or latency <= self.thresholds['latency_ms'] else "HIGH"
            print(f"   | Latency     | {latency:>7}ms | {self.thresholds['latency_ms']:>9}ms | {latency_status:>7} |")
            
            # Packet Loss
            loss = metrics.get('loss_percent', 'N/A')
            loss_status = "NORMAL" if loss == 'N/A' or loss <= self.thresholds['loss_percent'] else "HIGH"
            print(f"   | Packet Loss | {loss:>7}%  | {self.thresholds['loss_percent']:>9}%  | {loss_status:>7} |")
            
            # Jitter
            jitter = metrics.get('jitter', 'N/A')
            jitter_status = "NORMAL" if jitter == 'N/A' or jitter <= self.thresholds['jitter'] else "HIGH"
            print(f"   | Jitter      | {jitter:>7}ms | {self.thresholds['jitter']:>9}ms | {jitter_status:>7} |")
            
            # Goodput
            goodput = metrics.get('goodput', 'N/A')
            goodput_status = "NORMAL"  # Goodput doesn't have a threshold, always normal
            print(f"   | Goodput     | {goodput:>7}   | {'N/A':>9}   | {goodput_status:>7} |")
            
            print("   " + "="*60)
        
        # Display trend analysis
        trends = analysis.get('trends', {})
        if trends:
            print("\nTrend Analysis (24h):")
            
            # Latency trend
            latency_trend = trends.get('latency_trend', {})
            if latency_trend.get('direction') != 'insufficient_data':
                print(f"   Latency: {latency_trend.get('direction', 'unknown')} ({latency_trend.get('change_percent', 0):.1f}% change)")
            
            # Loss trend
            loss_trend = trends.get('loss_trend', {})
            if loss_trend.get('direction') != 'insufficient_data':
                print(f"   Packet Loss: {loss_trend.get('direction', 'unknown')} ({loss_trend.get('change_percent', 0):.1f}% change)")
            
            # Jitter trend
            jitter_trend = trends.get('jitter_trend', {})
            if jitter_trend.get('direction') != 'insufficient_data':
                print(f"   Jitter: {jitter_trend.get('direction', 'unknown')} ({jitter_trend.get('change_percent', 0):.1f}% change)")
            
            # Statistics summary
            stats = trends.get('statistics', {})
            if stats:
                latency_stats = stats.get('latency', {})
                if latency_stats:
                    print(f"   Latency Stats: Avg={latency_stats.get('mean', 0):.2f}ms, Std={latency_stats.get('std', 0):.2f}ms")
                
                loss_stats = stats.get('loss', {})
                if loss_stats:
                    print(f"   Loss Stats: Avg={loss_stats.get('mean', 0):.2f}%, Std={loss_stats.get('std', 0):.2f}%")
            
            # Anomalies
            anomalies = trends.get('anomalies', [])
            if anomalies:
                print(f"   Anomalies: {len(anomalies)} detected")
        
        # Display alerts
        alerts = analysis.get('alerts', [])
        if alerts:
            print("\nAlerts:")
            for alert in alerts:
                print(f"   {alert}")
        
        # Display LLM insights
        if insights:
            print("\nAI Insights:")
            self._display_structured_insights(insights)
        
        print("="*80)
    
    def _display_structured_insights(self, insights: str):
        """Display structured insights in a formatted way"""
        try:
            # Split insights into sections
            lines = insights.strip().split('\n')
            current_section = None
            section_content = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check for section headers
                if line.startswith('STATUS:'):
                    if current_section and section_content:
                        self._print_section(current_section, section_content)
                    current_section = 'STATUS'
                    section_content = [line[7:].strip()]  # Remove 'STATUS:' prefix
                elif line.startswith('PERFORMANCE ISSUES:'):
                    if current_section and section_content:
                        self._print_section(current_section, section_content)
                    current_section = 'PERFORMANCE ISSUES'
                    section_content = []
                elif line.startswith('ROOT CAUSES:'):
                    if current_section and section_content:
                        self._print_section(current_section, section_content)
                    current_section = 'ROOT CAUSES'
                    section_content = []
                elif line.startswith('RECOMMENDATIONS:'):
                    if current_section and section_content:
                        self._print_section(current_section, section_content)
                    current_section = 'RECOMMENDATIONS'
                    section_content = []
                elif line.startswith('TRENDS:'):
                    if current_section and section_content:
                        self._print_section(current_section, section_content)
                    current_section = 'TRENDS'
                    section_content = []
                elif line.startswith('•') and current_section:
                    section_content.append(line[1:].strip())  # Remove bullet point
                elif current_section and line:
                    # Handle multi-line content
                    if section_content:
                        section_content[-1] += " " + line
                    else:
                        section_content.append(line)
            
            # Print the last section
            if current_section and section_content:
                self._print_section(current_section, section_content)
                
        except Exception as e:
            # Fallback to simple display if parsing fails
            print(f"   {insights}")
    
    def _print_section(self, section: str, content: List[str]):
        """Print a formatted section"""
        section_colors = {
            'STATUS': 'GREEN',
            'PERFORMANCE ISSUES': 'RED',
            'ROOT CAUSES': 'YELLOW',
            'RECOMMENDATIONS': 'BLUE',
            'TRENDS': 'CYAN'
        }
        
        color = section_colors.get(section, 'WHITE')
        print(f"\n   {section}:")
        
        if section == 'STATUS':
            # Status is usually a single line
            print(f"     {content[0] if content else 'No status provided'}")
        else:
            # Other sections have bullet points
            for item in content:
                if item.strip():
                    print(f"     • {item.strip()}")
    
    async def run_monitoring_cycle(self):
        """Run one monitoring cycle"""
        try:
            # Collect data
            data = await self.collect_performance_data()
            
            # Analyze metrics
            analysis = self.analyze_performance_metrics(data)
            
            # Get LLM insights
            insights = await self.get_llm_insights(data, analysis)
            
            # Display results
            self.display_insights(analysis, insights)
            
            # Send to webhooks (Teams/Slack) if enabled
            if self.webhook_module:
                webhook_results = self.webhook_module.send_network_insights(analysis, insights)
                if webhook_results:
                    print(f"\nWebhook Results:")
                    for platform, success in webhook_results.items():
                        status = "SUCCESS" if success else "FAILED"
                        print(f"  {platform.upper()}: {status}")
            
            # Save to file
            self._save_monitoring_data(data, analysis, insights)
            
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")
            print(f"Monitoring error: {e}")
    
    def _save_monitoring_data(self, data: Dict[str, Any], analysis: Dict[str, Any], insights: str):
        """Save monitoring data to file"""
        try:
            os.makedirs("monitoring_data", exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"monitoring_data/network_monitor_{timestamp}.json"
            
            monitoring_data = {
                'timestamp': datetime.now().isoformat(),
                'data': data,
                'analysis': analysis,
                'insights': insights
            }
            
            with open(filename, 'w') as f:
                json.dump(monitoring_data, f, indent=2, default=str)
            
            logger.info(f"Monitoring data saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving monitoring data: {e}")
    
    async def start_monitoring(self, interval_minutes: int = 1):
        """Start continuous monitoring"""
        logger.info(f"Starting network performance monitoring (every {interval_minutes} minute(s))")
        print(f"Starting Network Performance Monitor")
        print(f"Monitoring interval: {interval_minutes} minute(s)")
        print(f"Data saved to: monitoring_data/")
        print(f"Logs saved to: network_monitor.log")
        print("Press Ctrl+C to stop monitoring\n")
        
        try:
            while True:
                await self.run_monitoring_cycle()
                
                # Wait for next cycle
                if interval_minutes > 0:
                    await asyncio.sleep(interval_minutes * 60)
                else:
                    break
                    
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
            logger.info("Monitoring stopped by user")
        except Exception as e:
            print(f"\nMonitoring error: {e}")
            logger.error(f"Monitoring error: {e}")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Network Performance Monitor with optional webhook notifications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 network_monitor.py                    # Run without webhooks
  python3 network_monitor.py --webhooks         # Run with webhooks enabled
  python3 network_monitor.py -w                 # Short form for webhooks
  python3 network_monitor.py --help             # Show this help message
        """
    )
    
    parser.add_argument(
        '--webhooks', '-w',
        action='store_true',
        help='Enable webhook notifications to Teams and Slack'
    )
    
    parser.add_argument(
        '--interval', '-i',
        type=int,
        default=1,
        help='Monitoring interval in minutes (default: 1)'
    )
    
    parser.add_argument(
        '--db-path',
        type=str,
        default="network_monitor.db",
        help='Database file path (default: network_monitor.db)'
    )
    
    parser.add_argument(
        '--max-history',
        type=int,
        default=1000,
        help='Maximum number of data points to keep in memory (default: 1000)'
    )
    
    return parser.parse_args()

async def main():
    """Main function"""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        print("="*80)
        print("NETWORK PERFORMANCE MONITOR")
        print("="*80)
        print(f"Monitoring interval: {args.interval} minute(s)")
        print(f"Database path: {args.db_path}")
        print(f"Max history: {args.max_history} data points")
        print(f"Webhooks enabled: {'Yes' if args.webhooks else 'No'}")
        
        if args.webhooks:
            print("\nWebhook Configuration:")
            print("  - Set TEAMS_WEBHOOK_URL in .env file for Teams notifications")
            print("  - Set SLACK_WEBHOOK_URL in .env file for Slack notifications")
            print("  - See WEBHOOK_SETUP.md for setup instructions")
        
        print("="*80)
        
        # Create monitor instance
        monitor = NetworkPerformanceMonitor(
            db_path=args.db_path,
            max_history=args.max_history,
            enable_webhooks=args.webhooks
        )
        
        # Start monitoring
        await monitor.start_monitoring(interval_minutes=args.interval)
        
    except Exception as e:
        print(f"Failed to start monitor: {e}")
        logger.error(f"Failed to start monitor: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 