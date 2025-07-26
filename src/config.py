"""
Configuración centralizada para el chat con DeepSeek y GitHub MCP
"""
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


@dataclass
class Config:
    """Configuración de la aplicación"""
    github_pat: str
    deepseek_api_key: str
    github_username: str = "MateoSebF"
    max_repos_display: int = 10
    docker_image: str = "ghcr.io/github/github-mcp-server"
    
    @classmethod
    def from_env(cls) -> "Config":
        """Crea una instancia de Config desde variables de entorno"""
        github_pat = os.getenv("GITHUB_PAT")
        deepseek_api_key = os.getenv("DEEP_SEEK_API_KEY")
        
        if not github_pat:
            raise ValueError("❌ GITHUB_PAT no encontrado en variables de entorno")
        if not deepseek_api_key:
            raise ValueError("❌ DEEP_SEEK_API_KEY no encontrado en variables de entorno")
            
        return cls(
            github_pat=github_pat,
            deepseek_api_key=deepseek_api_key
        )
    
    def validate(self) -> bool:
        """Valida que la configuración sea correcta"""
        return bool(self.github_pat and self.deepseek_api_key)


# Colores para la consola
class Colors:
    """Códigos de color ANSI para la terminal"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    YELLOW = '\033[93m'  # Alias para WARNING
    FAIL = '\033[91m'
    RED = '\033[91m'     # Alias para FAIL
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
