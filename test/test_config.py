#!/usr/bin/env python3
"""
Unit tests for configuration management
"""

import os
import tempfile
import unittest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config

class TestConfig(unittest.TestCase):
    """Test configuration management"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = Path(self.temp_dir) / ".env"
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_config_initialization(self):
        """Test config initialization"""
        config = Config()
        self.assertIsInstance(config, Config)
    
    def test_meraki_config(self):
        """Test Meraki configuration"""
        # Set test environment variables
        os.environ["MERAKI_API_KEY"] = "test_key"
        os.environ["NETWORK_ID"] = "test_network"
        os.environ["ORGANIZATION_ID"] = "test_org"
        
        config = Config()
        meraki_config = config.meraki_config
        
        self.assertEqual(meraki_config["api_key"], "test_key")
        self.assertEqual(meraki_config["network_id"], "test_network")
        self.assertEqual(meraki_config["organization_id"], "test_org")
        self.assertEqual(meraki_config["base_url"], "https://api.meraki.com/api/v1")
        self.assertEqual(meraki_config["timespan"], 86400)
    
    def test_llm_config(self):
        """Test LLM configuration"""
        os.environ["GEMINI_API_KEY"] = "test_gemini_key"
        
        config = Config()
        llm_config = config.llm_config
        
        self.assertEqual(llm_config["gemini_api_key"], "test_gemini_key")
        self.assertEqual(llm_config["model"], "gemini-2.5-flash")
        self.assertEqual(llm_config["temperature"], 0.3)
        self.assertEqual(llm_config["max_tokens"], 1024)
    
    def test_server_config(self):
        """Test server configuration"""
        config = Config()
        server_config = config.server_config
        
        self.assertFalse(server_config["use_mock"])
        self.assertEqual(server_config["mock_base_url"], "http://127.0.0.1:5000")
        self.assertFalse(server_config["force_mock_all"])
        self.assertFalse(server_config["force_real_all"])

if __name__ == "__main__":
    unittest.main()
