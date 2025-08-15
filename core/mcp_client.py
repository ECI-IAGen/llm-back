"""
MCP Client básico usando mcp_use
"""
from mcp_use import MCPClient as MCPUseClient


class MCPClient:
    """Cliente MCP simple que wrappea mcp_use con conexión automática"""
    
    def __init__(self, mcp_server):
        self.mcp_server = mcp_server
        self.client = None
        self.connected = False
        self._connection_task = None
    
    @classmethod
    async def create(cls, mcp_server):
        """Factory method para crear un MCPClient con conexión automática"""
        instance = cls(mcp_server)
        await instance._auto_connect()
        return instance
    
    async def _auto_connect(self) -> bool:
        """Conectar automáticamente al servidor MCP"""
        try:
            # Cargar configuración
            config = self.mcp_server.load_config()
            
            # Crear cliente
            self.client = MCPUseClient.from_dict(config)
            print("Cliente MCP creado con configuración:", config)
            # Crear sesiones
            await self.client.create_all_sessions()
            print("Sesiones creadas")
            
            self.connected = True
            print("✅ Cliente MCP conectado automáticamente")
            return True
            
        except Exception as e:
            print(f"❌ Error conectando automáticamente: {e}")
            return False
    
    async def connect(self) -> bool:
        """Conectar al servidor MCP (método legacy)"""
        if self.connected:
            return True
        return await self._auto_connect()
    
    async def disconnect(self):
        """Desconectar del servidor MCP"""
        if self.client:
            # El cliente mcp_use se limpia automáticamente
            pass
        self.connected = False
    
    def get_client(self):
        """Obtener el cliente mcp_use subyacente"""
        if not self.connected:
            raise RuntimeError("Cliente no conectado. Usa MCPClient.create() para conexión automática.")
        return self.client
    
    async def get_all_tools(self):
        """
        Obtener todas las herramientas disponibles de todas las sesiones
        Returns: List[str] - Lista de nombres de herramientas
        """
        if not self.connected:
            raise RuntimeError("Cliente no conectado. Usa MCPClient.create() para conexión automática.")
        
        print("=== HERRAMIENTAS DISPONIBLES ===")
        all_tools = []
        sessions = self.client.get_all_active_sessions()
        
        for server_name, session in sessions.items():
            print(f"\nServidor: {server_name}")
            try:
                print("  Herramientas disponibles:")
                tools = await session.connector.list_tools()
                print("  Total de herramientas:", len(tools))
                if tools:
                    for tool in tools:
                        # Los objetos Tool tienen atributos, no son diccionarios
                        tool_name = tool.name if hasattr(tool, 'name') else str(tool)
                        all_tools.append(tool_name)
                else:
                    print("  No se pudo acceder a list_tools")
            except Exception as e:
                print(f"  Error obteniendo herramientas: {e}")
        
        print(f"\nTotal de herramientas disponibles: {len(all_tools)}")
        print("="*50)
        return all_tools
    
    def filter_allowed_tools(self, all_tools, allowed_tools):
        """
        Filtrar herramientas permitidas y mostrar resumen
        Args:
            all_tools: Lista de todas las herramientas
            allowed_tools: Lista de herramientas permitidas
        Returns:
            tuple: (allowed, restricted)
        """
        allowed = [tool for tool in all_tools if tool in allowed_tools]
        restricted = [tool for tool in all_tools if tool not in allowed_tools]
        
        print(f"Herramientas permitidas: {len(allowed)}")
        print(f"Herramientas restringidas: {len(restricted)}")
        
        return allowed, restricted
