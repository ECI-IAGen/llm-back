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
        """Load MCP configuration from JSON file and inject all env variables"""
        load_dotenv()
        # Build full path to config file
        full_config_path = os.path.join(self.config_path, self.config_file)
        print(f"Loading MCP configuration from: {full_config_path}")
        try:
            with open(full_config_path, 'r', encoding='utf-8') as f:
                self.config_dict = json.load(f)
            
            # Inject all environment variables into Docker containers
            self._inject_env_variables()
            
            return self.config_dict
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {full_config_path}")
    
    def _inject_env_variables(self):
        """Inject all environment variables into MCP server configurations"""
        # Get all environment variables
        env_vars = dict(os.environ)
        
        # Iterate through all MCP servers in config
        if "mcpServers" in self.config_dict:
            for server_name, server_config in self.config_dict["mcpServers"].items():
                # If this server uses Docker, inject env vars
                if server_config.get("command") == "docker":
                    # Ensure env section exists
                    if "env" not in server_config:
                        server_config["env"] = {}
                    
                    # Add all environment variables to the container
                    for key, value in env_vars.items():
                        # Skip system variables and only include relevant ones
                        if not key.startswith(('_', 'PATH', 'HOME', 'USER', 'TEMP', 'TMP', 'WINDIR', 'SYSTEMROOT')):
                            server_config["env"][key] = value
                    
                    print(f"✅ Injected {len([k for k in env_vars.keys() if not k.startswith(('_', 'PATH', 'HOME', 'USER', 'TEMP', 'TMP', 'WINDIR', 'SYSTEMROOT'))])} environment variables into {server_name} container")
