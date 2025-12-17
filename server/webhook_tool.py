#!/usr/bin/env python3
"""
Webhook MCP Tool
Provides webhook functionality as an MCP tool for sending alerts to Teams/Slack
"""

import json
import logging
import os
import sys
from typing import Any, Dict, Optional

# Add parent directory to path to import webhook_module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core"))

from core.webhook_module import WebhookModule

logger = logging.getLogger("webhook-tool")


def send_teams_alert(
    title: str,
    message: str,
    status: str = "normal",
    metrics: Optional[Dict] = None,
    alerts: Optional[list] = None
) -> Dict[str, Any]:
    """
    Send alert to Microsoft Teams webhook
    
    Args:
        title: Alert title
        message: Alert message content
        status: Alert status (normal, warning, critical, error)
        metrics: Optional metrics dictionary
        alerts: Optional list of alert strings
    
    Returns:
        Dictionary with success status and message
    """
    try:
        webhook = WebhookModule()
        
        if not webhook.is_configured():
            return {
                "success": False,
                "message": "Webhook not configured. Set TEAMS_WEBHOOK_URL in .env file"
            }
        
        # Convert metrics dict if provided
        metrics_dict = metrics if metrics else {}
        alerts_list = alerts if alerts else []
        
        success = webhook.send_to_teams(title, message, status, metrics_dict, alerts_list)
        
        if success:
            return {
                "success": True,
                "message": f"Alert sent to Teams: {title}"
            }
        else:
            return {
                "success": False,
                "message": "Failed to send alert to Teams"
            }
            
    except Exception as e:
        logger.error(f"Error in send_teams_alert: {e}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


def send_slack_alert(
    title: str,
    message: str,
    status: str = "normal",
    metrics: Optional[Dict] = None,
    alerts: Optional[list] = None
) -> Dict[str, Any]:
    """
    Send alert to Slack webhook
    
    Args:
        title: Alert title
        message: Alert message content
        status: Alert status (normal, warning, critical, error)
        metrics: Optional metrics dictionary
        alerts: Optional list of alert strings
    
    Returns:
        Dictionary with success status and message
    """
    try:
        webhook = WebhookModule()
        
        if not webhook.is_configured():
            return {
                "success": False,
                "message": "Webhook not configured. Set SLACK_WEBHOOK_URL in .env file"
            }
        
        # Convert metrics dict if provided
        metrics_dict = metrics if metrics else {}
        alerts_list = alerts if alerts else []
        
        success = webhook.send_to_slack(title, message, status, metrics_dict, alerts_list)
        
        if success:
            return {
                "success": True,
                "message": f"Alert sent to Slack: {title}"
            }
        else:
            return {
                "success": False,
                "message": "Failed to send alert to Slack"
            }
            
    except Exception as e:
        logger.error(f"Error in send_slack_alert: {e}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


def send_network_alert(
    title: str,
    message: str,
    status: str = "normal",
    metrics: Optional[Dict] = None,
    alerts: Optional[list] = None
) -> Dict[str, Any]:
    """
    Send network alert to all configured webhooks (Teams and Slack)
    
    Args:
        title: Alert title
        message: Alert message content
        status: Alert status (normal, warning, critical, error)
        metrics: Optional metrics dictionary with network metrics
        alerts: Optional list of alert strings
    
    Returns:
        Dictionary with success status for each platform
    """
    try:
        webhook = WebhookModule()
        
        if not webhook.is_configured():
            return {
                "success": False,
                "message": "No webhooks configured. Set TEAMS_WEBHOOK_URL and/or SLACK_WEBHOOK_URL in .env file"
            }
        
        # Convert metrics dict if provided
        metrics_dict = metrics if metrics else {}
        alerts_list = alerts if alerts else []
        
        results = webhook.send_to_all(title, message, status, metrics_dict, alerts_list)
        
        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)
        
        return {
            "success": success_count > 0,
            "message": f"Alert sent to {success_count}/{total_count} platforms",
            "details": results
        }
            
    except Exception as e:
        logger.error(f"Error in send_network_alert: {e}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


def send_network_insights(
    analysis: Dict[str, Any],
    insights: str
) -> Dict[str, Any]:
    """
    Send detailed network performance insights to webhooks
    
    Args:
        analysis: Network analysis dictionary with status, metrics, alerts, trends
        insights: AI-generated insights text
    
    Returns:
        Dictionary with success status for each platform
    """
    try:
        webhook = WebhookModule()
        
        if not webhook.is_configured():
            return {
                "success": False,
                "message": "No webhooks configured. Set TEAMS_WEBHOOK_URL and/or SLACK_WEBHOOK_URL in .env file"
            }
        
        results = webhook.send_network_insights(analysis, insights)
        
        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)
        
        return {
            "success": success_count > 0,
            "message": f"Network insights sent to {success_count}/{total_count} platforms",
            "details": results
        }
            
    except Exception as e:
        logger.error(f"Error in send_network_insights: {e}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


# Tool metadata for MCP server
WEBHOOK_TOOLS = [
    {
        "name": "send_teams_alert",
        "description": "Send alert to Microsoft Teams webhook",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Alert title"
                },
                "message": {
                    "type": "string",
                    "description": "Alert message content"
                },
                "status": {
                    "type": "string",
                    "enum": ["normal", "warning", "critical", "error"],
                    "description": "Alert status level",
                    "default": "normal"
                },
                "metrics": {
                    "type": "object",
                    "description": "Optional metrics dictionary",
                    "additionalProperties": True
                },
                "alerts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of alert strings"
                }
            },
            "required": ["title", "message"]
        }
    },
    {
        "name": "send_slack_alert",
        "description": "Send alert to Slack webhook",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Alert title"
                },
                "message": {
                    "type": "string",
                    "description": "Alert message content"
                },
                "status": {
                    "type": "string",
                    "enum": ["normal", "warning", "critical", "error"],
                    "description": "Alert status level",
                    "default": "normal"
                },
                "metrics": {
                    "type": "object",
                    "description": "Optional metrics dictionary",
                    "additionalProperties": True
                },
                "alerts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of alert strings"
                }
            },
            "required": ["title", "message"]
        }
    },
    {
        "name": "send_network_alert",
        "description": "Send network alert to all configured webhooks (Teams and Slack)",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Alert title"
                },
                "message": {
                    "type": "string",
                    "description": "Alert message content"
                },
                "status": {
                    "type": "string",
                    "enum": ["normal", "warning", "critical", "error"],
                    "description": "Alert status level",
                    "default": "normal"
                },
                "metrics": {
                    "type": "object",
                    "description": "Optional network metrics dictionary",
                    "additionalProperties": True
                },
                "alerts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of alert strings"
                }
            },
            "required": ["title", "message"]
        }
    },
    {
        "name": "send_network_insights",
        "description": "Send detailed network performance insights to webhooks",
        "parameters": {
            "type": "object",
            "properties": {
                "analysis": {
                    "type": "object",
                    "description": "Network analysis dictionary with status, metrics, alerts, trends",
                    "properties": {
                        "status": {"type": "string"},
                        "metrics": {
                            "type": "object",
                            "additionalProperties": True
                        },
                        "alerts": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "trends": {
                            "type": "object",
                            "additionalProperties": True
                        },
                        "timestamp": {"type": "string"}
                    },
                    "required": ["status"]
                },
                "insights": {
                    "type": "string",
                    "description": "AI-generated insights text"
                }
            },
            "required": ["analysis", "insights"]
        }
    }
]
