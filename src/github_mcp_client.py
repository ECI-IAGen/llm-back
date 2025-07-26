"""
Cliente MCP simplificado para GitHub
"""
import json
from typing import Dict, Any, Optional, List
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from src.config import Config, Colors


class GitHubMCPClient:
    """Cliente MCP para interactuar con GitHub a través de herramientas MCP"""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = None
        self.connected = False
        self.available_tools = []
        
    async def connect(self) -> bool:
        """
        Establece la conexión MCP con GitHub
        
        Returns:
            True si la conexión fue exitosa, False en caso contrario
        """
        try:
            # Parámetros para lanzar Docker + MCP Server
            params = StdioServerParameters(
                command="docker",
                args=[
                    "run", "-i", "--rm",
                    f"-eGITHUB_PERSONAL_ACCESS_TOKEN={self.config.github_pat}",
                    "ghcr.io/github/github-mcp-server"
                ],
                env={}
            )
            
            # Abrir canal stdio ↔ MCP
            self.stdio_context = stdio_client(params)
            self.read, self.write = await self.stdio_context.__aenter__()
            
            # Crear sesión
            self.session_context = ClientSession(self.read, self.write)
            self.session = await self.session_context.__aenter__()
            
            # Handshake e inicialización
            await self.session.initialize()
            
            # Listar herramientas disponibles
            tools_result = await self.session.list_tools()
            self.available_tools = [tool.name for tool in tools_result.tools]
            
            self.connected = True
            print(f"{Colors.GREEN}✅ Conectado a GitHub MCP")
            print(f"📋 Herramientas disponibles: {', '.join(self.available_tools)}{Colors.ENDC}")
            
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ Error conectando a GitHub MCP: {str(e)}{Colors.ENDC}")
            return False
    
    async def disconnect(self):
        """Cierra la conexión MCP"""
        try:
            if self.session_context:
                await self.session_context.__aexit__(None, None, None)
            if self.stdio_context:
                await self.stdio_context.__aexit__(None, None, None)
            self.connected = False
            print(f"{Colors.YELLOW}🔌 Desconectado de GitHub MCP{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.RED}Error desconectando: {str(e)}{Colors.ENDC}")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Llama a una herramienta MCP
        
        Args:
            tool_name: Nombre de la herramienta
            arguments: Argumentos para la herramienta
            
        Returns:
            Resultado de la herramienta
        """
        if not self.connected or not self.session:
            return {"error": "No hay conexión MCP activa"}
            
        if tool_name not in self.available_tools:
            return {"error": f"Herramienta '{tool_name}' no disponible"}
        
        try:
            result = await self.session.call_tool(tool_name, arguments=arguments)
            
            # Parsear la respuesta
            res_dict = result.model_dump()
            
            if res_dict.get('content') and len(res_dict['content']) > 0:
                response_text = res_dict['content'][0]['text']
                try:
                    return json.loads(response_text)
                except json.JSONDecodeError:
                    return {"text": response_text}
            else:
                return {"error": "No se recibió respuesta válida"}
                
        except Exception as e:
            return {"error": f"Error llamando herramienta '{tool_name}': {str(e)}"}
    
    async def create_tools_context(self) -> str:
        """
        Crea un contexto de las herramientas MCP disponibles para DeepSeek
        
        Returns:
            Descripción de las herramientas disponibles con sus parámetros
        """
        if not self.connected:
            return "No hay conexión MCP activa con GitHub."
        
        context = "Herramientas disponibles para interactuar con GitHub:\n\n"
        
        try:
            # Obtener información detallada de las herramientas
            tools_result = await self.session.list_tools()
            
            for tool in tools_result.tools:
                # Obtener parámetros requeridos y opcionales
                params = []
                if hasattr(tool, 'inputSchema') and tool.inputSchema and 'properties' in tool.inputSchema:
                    required_params = tool.inputSchema.get('required', [])
                    
                    for prop_name in tool.inputSchema['properties'].keys():
                        if prop_name in required_params:
                            params.append(f"{prop_name}*")  # * indica requerido
                        else:
                            params.append(prop_name)
                
                params_str = f"({', '.join(params)})" if params else "(sin parámetros)"
                context += f"- {tool.name}{params_str}\n"
                
                # Agregar descripción si está disponible
                if hasattr(tool, 'description') and tool.description:
                    context += f"  └─ {tool.description}\n"
                
        except Exception as e:
            # Fallback a la lista simple si hay error
            for tool in self.available_tools:
                context += f"- {tool}\n"
        
        context += "\nPuedes usar cualquiera de estas herramientas según lo que necesites hacer."
        context += "\nLos parámetros marcados con * son obligatorios."
        
        return context
    
    def get_available_tools_list(self) -> List[str]:
        """
        Retorna la lista simple de herramientas disponibles
        
        Returns:
            Lista de nombres de herramientas
        """
        return self.available_tools.copy()
    
    async def execute_tool_request(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una herramienta específica con argumentos dados
        
        Args:
            tool_name: Nombre de la herramienta a ejecutar
            arguments: Argumentos para la herramienta
            
        Returns:
            Resultado de la herramienta
        """
        return await self.call_tool(tool_name, arguments)
    
    def __getattr__(self, name: str):
        """
        Permite llamar cualquier herramienta MCP como método de la clase
        Ejemplo: client.search_repositories(query="hello world")
        """
        if name in self.available_tools:
            async def dynamic_tool(**kwargs):
                return await self.call_tool(name, kwargs)
            return dynamic_tool
        raise AttributeError(f"'{self.__class__.__name__}' no tiene el atributo '{name}' y '{name}' no es una herramienta MCP disponible")
    
    async def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el schema de una herramienta específica
        
        Args:
            tool_name: Nombre de la herramienta
            
        Returns:
            Schema de la herramienta o None si no existe
        """
        if not self.connected:
            return None
            
        try:
            tools_result = await self.session.list_tools()
            for tool in tools_result.tools:
                if tool.name == tool_name:
                    return {
                        'name': tool.name,
                        'description': tool.description,
                        'schema': tool.inputSchema if hasattr(tool, 'inputSchema') else None
                    }
            return None
        except Exception:
            return None

    async def show_available_tools(self):
        """Muestra todas las herramientas disponibles y sus argumentos de forma simple"""
        if not self.connected:
            print("❌ No hay conexión MCP activa")
            return
            
        try:
            tools_result = await self.session.list_tools()
            print(f"\n{Colors.GREEN}📋 HERRAMIENTAS GITHUB MCP DISPONIBLES{Colors.ENDC}")
            print("=" * 60)
            
            for tool in tools_result.tools:
                # Obtener parámetros requeridos
                params = []
                if hasattr(tool, 'inputSchema') and tool.inputSchema and 'properties' in tool.inputSchema:
                    required_params = tool.inputSchema.get('required', [])
                    optional_params = []
                    
                    for prop_name in tool.inputSchema['properties'].keys():
                        if prop_name in required_params:
                            params.append(f"{prop_name}*")  # * indica requerido
                        else:
                            optional_params.append(prop_name)
                    
                    # Agregar parámetros opcionales al final
                    params.extend(optional_params)
                
                params_str = ", ".join(params) if params else "sin parámetros"
                print(f"{Colors.CYAN}{tool.name}{Colors.ENDC}: {params_str}")
                
        except Exception as e:
            print(f"❌ Error obteniendo herramientas: {e}")


# Función para ejecutar cuando se ejecuta el archivo directamente
async def main():
    """Función principal para mostrar herramientas disponibles"""
    from src.config import Config
    
    print(f"{Colors.GREEN}🚀 Conectando a GitHub MCP...{Colors.ENDC}")
    
    config = Config.from_env()
    client = GitHubMCPClient(config)
    
    if await client.connect():
        await client.show_available_tools()
        await client.disconnect()
    else:
        print("❌ No se pudo conectar a GitHub MCP")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
