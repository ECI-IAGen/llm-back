"""
Test script para probar el nuevo create_tools_context
"""
import asyncio
from src.config import Config
from src.github_mcp_client import GitHubMCPClient

async def test_tools_context():
    """Prueba el nuevo create_tools_context"""
    config = Config.from_env()
    client = GitHubMCPClient(config)
    
    if await client.connect():
        print("🔍 TESTING create_tools_context():")
        print("=" * 60)
        
        context = await client.create_tools_context()
        print(context)
        
        await client.disconnect()
    else:
        print("❌ No se pudo conectar a GitHub MCP")

if __name__ == "__main__":
    asyncio.run(test_tools_context())
