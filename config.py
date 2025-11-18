#!/usr/bin/env python3
"""
Configuration management for the Network Agent
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

logger = logging.getLogger("config")

class Config:
    """Configuration manager for the Network Agent"""
    
    def __init__(self, env_file: Optional[str] = None):
        """Initialize configuration"""
        self.env_file = env_file or ".env"
        self._load_environment()
        self._validate_config()
    
    def _load_environment(self):
        """Load environment variables from .env file"""
        env_path = Path(self.env_file)
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(f"Loaded environment from {env_path}")
        else:
            logger.warning(f"Environment file {env_path} not found, using system environment")
    
    def _validate_config(self):
        """Validate required configuration"""
        required_vars = [
            "MERAKI_API_KEY",
            "NETWORK_ID", 
            "ORGANIZATION_ID"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.warning(f"Missing required environment variables: {missing_vars}")
    
    @property
    def meraki_config(self) -> Dict[str, Any]:
        """Get Meraki API configuration"""
        return {
            "api_key": os.getenv("MERAKI_API_KEY"),
            "base_url": os.getenv("BASE_URL", "https://api.meraki.com/api/v1"),
            "network_id": os.getenv("NETWORK_ID"),
            "organization_id": os.getenv("ORGANIZATION_ID"),
            "serial": os.getenv("SERIAL"),
            "ip": os.getenv("IP"),
            "product_type": os.getenv("PRODUCT_TYPE", "appliance"),
            "timespan": int(os.getenv("TIMESPAN", "86400"))
        }
    
    @property
    def llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration"""
        return {
            "gemini_api_key": os.getenv("GEMINI_API_KEY"),
            "model": os.getenv("LLM_MODEL", "gemini-2.5-flash"),
            "temperature": float(os.getenv("LLM_TEMPERATURE", "0.3")),
            "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "1024"))
        }
    
    @property
    def server_config(self) -> Dict[str, Any]:
        """Get server configuration"""
        return {
            "use_mock": os.getenv("USE_MOCK", "false").lower() == "true",
            "mock_base_url": os.getenv("MOCK_BASE_URL", "http://127.0.0.1:5000"),
            "force_mock_all": os.getenv("FORCE_MOCK_ALL", "false").lower() == "true",
            "force_real_all": os.getenv("FORCE_REAL_ALL", "false").lower() == "true"
        }

def setup_environment(env_file: Optional[str] = None) -> Config:
    """Setup and return configuration"""
    return Config(env_file)

# Global configuration instance
config = setup_environment()
