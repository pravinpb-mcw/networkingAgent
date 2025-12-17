#!/usr/bin/env python3
"""
Webhook Module for Network Monitor
Separate module for webhook functionality
"""

import json
import logging
import os
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger("webhook-module")

class WebhookModule:
    """Webhook functionality for network monitoring"""
    
    def __init__(self):
        """Initialize webhook module"""
        self.teams_webhook_url = os.getenv("TEAMS_WEBHOOK_URL")
        self.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        
        # Check if webhooks are configured
        if not self.teams_webhook_url and not self.slack_webhook_url:
            logger.warning("No webhook URLs configured. Set TEAMS_WEBHOOK_URL and/or SLACK_WEBHOOK_URL in .env file")
        
        if self.teams_webhook_url:
            logger.info("Teams webhook configured")
        if self.slack_webhook_url:
            logger.info("Slack webhook configured")
    
    def is_configured(self) -> bool:
        """Check if any webhooks are configured"""
        return bool(self.teams_webhook_url or self.slack_webhook_url)
    
    def send_to_teams(self, title: str, message: str, status: str = "normal", metrics: Optional[Dict] = None, alerts: Optional[List[str]] = None) -> bool:
        """Send message to Microsoft Teams"""
        if not self.teams_webhook_url:
            logger.warning("Teams webhook URL not configured")
            return False
        
        try:
            # Create Teams message card
            card = self._create_teams_card(title, message, status, metrics, alerts)
            
            # Send to Teams
            response = requests.post(
                self.teams_webhook_url,
                json=card,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Message sent to Teams successfully")
                return True
            else:
                logger.error(f"Failed to send to Teams: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending to Teams: {e}")
            return False
    
    def send_to_slack(self, title: str, message: str, status: str = "normal", metrics: Optional[Dict] = None, alerts: Optional[List[str]] = None) -> bool:
        """Send message to Slack"""
        if not self.slack_webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False
        
        try:
            # Create Slack message
            slack_message = self._create_slack_message(title, message, status, metrics, alerts)
            
            # Send to Slack
            response = requests.post(
                self.slack_webhook_url,
                json=slack_message,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Message sent to Slack successfully")
                return True
            else:
                logger.error(f"Failed to send to Slack: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending to Slack: {e}")
            return False
    
    def send_to_all(self, title: str, message: str, status: str = "normal", metrics: Optional[Dict] = None, alerts: Optional[List[str]] = None) -> Dict[str, bool]:
        """Send message to both Teams and Slack"""
        results = {}
        
        if self.teams_webhook_url:
            results['teams'] = self.send_to_teams(title, message, status, metrics, alerts)
        
        if self.slack_webhook_url:
            results['slack'] = self.send_to_slack(title, message, status, metrics, alerts)
        
        return results
    
    def _create_teams_card(self, title: str, message: str, status: str, metrics: Optional[Dict], alerts: Optional[List[str]]) -> Dict[str, Any]:
        """Create Teams message card"""
        # Status colors
        status_colors = {
            'normal': '00FF00',    # Green
            'warning': 'FFA500',   # Orange
            'critical': 'FF0000',  # Red
            'error': 'FF0000'      # Red
        }
        
        color = status_colors.get(status, '00FF00')
        
        # Create card with console-style message
        card = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": color,
            "summary": title,
            "sections": [
                {
                    "activityTitle": title,
                    "activitySubtitle": f"Status: {status.upper()}",
                    "activityImage": "https://img.icons8.com/color/48/000000/network.png",
                    "text": message,
                    "markdown": True
                }
            ]
        }
        
        return card
    
    def _create_slack_message(self, title: str, message: str, status: str, metrics: Optional[Dict], alerts: Optional[List[str]]) -> Dict[str, Any]:
        """Create Slack message with blocks"""
        # Status colors
        status_colors = {
            'normal': '#00FF00',    # Green
            'warning': '#FFA500',   # Orange
            'critical': '#FF0000',  # Red
            'error': '#FF0000'      # Red
        }
        
        color = status_colors.get(status, '#00FF00')
        
        # Create blocks with console-style message
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": title,
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"```\n{message}\n```"
                }
            }
        ]
        
        # Add timestamp
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            ]
        })
        
        return {
            "blocks": blocks,
            "color": color
        }
    
    def _format_insights_for_webhook(self, insights: str) -> str:
        """Format insights for webhook messages"""
        try:
            # Extract key sections for webhook
            lines = insights.strip().split('\n')
            formatted_parts = []
            
            for line in lines:
                line = line.strip()
                if line.startswith('STATUS:'):
                    status = line[7:].strip()
                    formatted_parts.append(f"**Status:** {status}")
                elif line.startswith('PERFORMANCE ISSUES:') or line.startswith('ROOT CAUSES:') or line.startswith('RECOMMENDATIONS:') or line.startswith('TRENDS:'):
                    # Skip section headers, we'll handle content separately
                    continue
                elif line.startswith('•'):
                    # Add bullet points
                    formatted_parts.append(f"  {line}")
            
            # If no structured format found, return original
            if not formatted_parts:
                return insights[:300] + "..." if len(insights) > 300 else insights
            
            return "\n".join(formatted_parts)
            
        except Exception as e:
            # Fallback to original insights
            return insights[:300] + "..." if len(insights) > 300 else insights
    
    def _format_insights_for_webhook_console(self, insights: str) -> str:
        """Format insights in console format for webhook messages"""
        try:
            # Split insights into sections
            lines = insights.strip().split('\n')
            current_section = None
            section_content = []
            formatted_parts = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check for section headers
                if line.startswith('STATUS:'):
                    if current_section and section_content:
                        formatted_parts.extend(self._format_section_console(current_section, section_content))
                    current_section = 'STATUS'
                    section_content = [line[7:].strip()]  # Remove 'STATUS:' prefix
                elif line.startswith('PERFORMANCE ISSUES:'):
                    if current_section and section_content:
                        formatted_parts.extend(self._format_section_console(current_section, section_content))
                    current_section = 'PERFORMANCE ISSUES'
                    section_content = []
                elif line.startswith('ROOT CAUSES:'):
                    if current_section and section_content:
                        formatted_parts.extend(self._format_section_console(current_section, section_content))
                    current_section = 'ROOT CAUSES'
                    section_content = []
                elif line.startswith('RECOMMENDATIONS:'):
                    if current_section and section_content:
                        formatted_parts.extend(self._format_section_console(current_section, section_content))
                    current_section = 'RECOMMENDATIONS'
                    section_content = []
                elif line.startswith('TRENDS:'):
                    if current_section and section_content:
                        formatted_parts.extend(self._format_section_console(current_section, section_content))
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
            
            # Format the last section
            if current_section and section_content:
                formatted_parts.extend(self._format_section_console(current_section, section_content))
            
            return "\n".join(formatted_parts)
                
        except Exception as e:
            # Fallback to simple display if parsing fails
            return f"   {insights}"
    
    def _format_section_console(self, section: str, content: List[str]) -> List[str]:
        """Format a section in console style"""
        formatted_lines = []
        
        if section == 'STATUS':
            # Status is usually a single line
            formatted_lines.append(f"   {section}:")
            formatted_lines.append(f"     {content[0] if content else 'No status provided'}")
        else:
            # Other sections have bullet points
            formatted_lines.append(f"   {section}:")
            for item in content:
                if item.strip():
                    formatted_lines.append(f"     • {item.strip()}")
        
        return formatted_lines
    
    def send_network_insights(self, analysis: Dict[str, Any], insights: str) -> Dict[str, bool]:
        """Send network performance insights to both platforms"""
        # Extract data from analysis
        status = analysis.get('status', 'normal')
        metrics = analysis.get('metrics', {})
        alerts = analysis.get('alerts', [])
        trends = analysis.get('trends', {})
        timestamp = analysis.get('timestamp', datetime.now().isoformat())
        
        # Create title and message in the same format as console
        title = f"NETWORK PERFORMANCE MONITOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Create message in console format
        message_parts = []
        
        # Add status
        message_parts.append(f"Status: {status.upper()}")
        
        # Add metrics table
        if metrics:
            message_parts.append("\nCurrent Metrics:")
            message_parts.append("   " + "="*60)
            message_parts.append("   | Metric      | Value    | Threshold | Status  |")
            message_parts.append("   |" + "-"*58 + "|")
            
            # Define thresholds for status calculation
            thresholds = {
                'latency_ms': 10.0,
                'loss_percent': 1.0,
                'jitter': 2.0
            }
            
            # Latency
            latency = metrics.get('latency_ms', 'N/A')
            latency_status = "NORMAL" if latency == 'N/A' or latency <= thresholds['latency_ms'] else "HIGH"
            message_parts.append(f"   | Latency     | {latency:>7}ms | {thresholds['latency_ms']:>9}ms | {latency_status:>7} |")
            
            # Packet Loss
            loss = metrics.get('loss_percent', 'N/A')
            loss_status = "NORMAL" if loss == 'N/A' or loss <= thresholds['loss_percent'] else "HIGH"
            message_parts.append(f"   | Packet Loss | {loss:>7}%  | {thresholds['loss_percent']:>9}%  | {loss_status:>7} |")
            
            # Jitter
            jitter = metrics.get('jitter', 'N/A')
            jitter_status = "NORMAL" if jitter == 'N/A' or jitter <= thresholds['jitter'] else "HIGH"
            message_parts.append(f"   | Jitter      | {jitter:>7}ms | {thresholds['jitter']:>9}ms | {jitter_status:>7} |")
            
            # Goodput
            goodput = metrics.get('goodput', 'N/A')
            goodput_status = "NORMAL"
            message_parts.append(f"   | Goodput     | {goodput:>7}   | {'N/A':>9}   | {goodput_status:>7} |")
            
            message_parts.append("   " + "="*60)
        
        # Add trend analysis
        if trends:
            message_parts.append("\nTrend Analysis (24h):")
            
            # Latency trend
            latency_trend = trends.get('latency_trend', {})
            if latency_trend.get('direction') != 'insufficient_data':
                message_parts.append(f"   Latency: {latency_trend.get('direction', 'unknown')} ({latency_trend.get('change_percent', 0):.1f}% change)")
            
            # Loss trend
            loss_trend = trends.get('loss_trend', {})
            if loss_trend.get('direction') != 'insufficient_data':
                message_parts.append(f"   Packet Loss: {loss_trend.get('direction', 'unknown')} ({loss_trend.get('change_percent', 0):.1f}% change)")
            
            # Jitter trend
            jitter_trend = trends.get('jitter_trend', {})
            if jitter_trend.get('direction') != 'insufficient_data':
                message_parts.append(f"   Jitter: {jitter_trend.get('direction', 'unknown')} ({jitter_trend.get('change_percent', 0):.1f}% change)")
            
            # Statistics summary
            stats = trends.get('statistics', {})
            if stats:
                latency_stats = stats.get('latency', {})
                if latency_stats:
                    message_parts.append(f"   Latency Stats: Avg={latency_stats.get('mean', 0):.2f}ms, Std={latency_stats.get('std', 0):.2f}ms")
                
                loss_stats = stats.get('loss', {})
                if loss_stats:
                    message_parts.append(f"   Loss Stats: Avg={loss_stats.get('mean', 0):.2f}%, Std={loss_stats.get('std', 0):.2f}%")
            
            # Anomalies
            anomalies = trends.get('anomalies', [])
            if anomalies:
                message_parts.append(f"   Anomalies: {len(anomalies)} detected")
        
        # Add alerts
        if alerts:
            message_parts.append("\nAlerts:")
            for alert in alerts:
                message_parts.append(f"   {alert}")
        
        # Add AI insights in structured format
        if insights:
            message_parts.append("\nAI Insights:")
            structured_insights = self._format_insights_for_webhook_console(insights)
            message_parts.append(structured_insights)
        
        message = "\n".join(message_parts)
        
        # Send to both platforms
        return self.send_to_all(title, message, status, metrics, alerts) 