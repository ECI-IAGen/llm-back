"""
Core MCP Server implementation that supports both Docker and JSON configuration
"""
import os
import json
from typing import Dict, Any
from dotenv import load_dotenv


class MCPServer:
    """MCP Server that can connect via JSON config """
    
    def __init__(self, config_file: str = "github_mcp_oficial.json"):
        self.config_path = "config"
        self.config_file = config_file
        self.config_dict = None
    
    def load_config(self) -> Dict[str, Any]:
        """Load MCP configuration from JSON file"""
        load_dotenv()
        
        # Build full path to config file
        full_config_path = os.path.join(self.config_path, self.config_file)
    
        print(f"Loading MCP configuration from: {full_config_path}")
        try:
            with open(full_config_path, 'r', encoding='utf-8') as f:
                self.config_dict = json.load(f)
            # Replace environment variables
            config_str = json.dumps(self.config_dict)
            github_token = os.getenv('GITHUB_PAT')
            if github_token:
                config_str = config_str.replace('${GITHUB_PAT}', github_token)
            self.config_dict = json.loads(config_str)
            return self.config_dict
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {full_config_path}")
