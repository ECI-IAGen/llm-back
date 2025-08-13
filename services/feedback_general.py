"""
Servicio de feedback para coordinadores y profesores usando MCP PostgreSQL
"""
from mcp_use.agents.mcpagent import MCPAgent
from core.mcp_client import MCPClient
from core.mcp_server import MCPServer
from core.llm import LLMProvider, LLMFactory
from services.feedback_prompts import FeedbackPrompts
from services.streaming_agent import StreamingMCPAgent
from services.gateway_notification import GatewayNotificationService
from typing import Optional


class FeedbackGeneralService:
    """
    Servicio para generar feedback específico para coordinadores y profesores
    utilizando datos de la base de datos PostgreSQL a través de MCP.
    """
    
    def __init__(self, config_file: str = "postgres_mcp_crystaldba.json"):
        """
        Inicializar el servicio de feedback.
        
        Args:
            config_file: Archivo de configuración MCP para PostgreSQL
        """
        self.config_file = config_file
        self.mcp_server = None
        self.mcp_client = None
        self.llm = None
        self.agent = None
        self.streaming_agent = None
        self.gateway_notifier = GatewayNotificationService()
        
    async def _initialize(self):
        """Inicializar conexiones MCP y LLM"""
        if self.agent is not None:
            return  # Ya inicializado
            
        try:
            # Crear servidor MCP
            self.mcp_server = MCPServer(config_file=self.config_file)
            
            # Crear cliente MCP con conexión automática
            self.mcp_client = await MCPClient.create(self.mcp_server)
            
            # Verificar conexión
            if not self.mcp_client.connected:
                raise RuntimeError("No se pudo conectar al servidor MCP PostgreSQL")
            
            # Obtener cliente mcp_use
            client = self.mcp_client.get_client()
            
            # Crear LLM
            self.llm = LLMFactory.create_llm(
                provider=LLMProvider.DEEPSEEK,
                model="deepseek-chat",
                temperature=0.1
            )
            
            # Crear agente MCP
            self.agent = MCPAgent(
                llm=self.llm, 
                client=client, 
                max_steps=50,
                disallowed_tools=[]
            )
            
            # Crear agente con streaming
            self.streaming_agent = StreamingMCPAgent(
                agent=self.agent,
                gateway_notifier=self.gateway_notifier
            )
            
            print("✅ Servicio de feedback inicializado correctamente")
            
        except Exception as e:
            print(f"❌ Error inicializando servicio de feedback: {e}")
            raise
    
    async def feedback_general_coordinador(self, user_query: str) -> str:
        """
        Generar feedback específico para coordinadores académicos.
        
        Args:
            user_query: Consulta o petición del coordinador
            
        Returns:
            str: Respuesta personalizada para coordinador con análisis estratégico
        """
        await self._initialize()
        
        try:
            # Obtener prompt personalizado para coordinador
            prompt = FeedbackPrompts.get_coordinador_prompt(user_query)
            
            # Ejecutar consulta con el agente
            result = await self.agent.run(prompt)
            
            return result
            
        except Exception as e:
            error_msg = f"Error generando feedback para coordinador: {e}"
            print(f"❌ {error_msg}")
            return error_msg
    
    async def feedback_general_profesor(self, user_query: str) -> str:
        """
        Generar feedback específico para profesores.
        
        Args:
            user_query: Consulta o petición del profesor
            
        Returns:
            str: Respuesta personalizada para profesor con análisis pedagógico
        """
        await self._initialize()
        
        try:
            # Obtener prompt personalizado para profesor
            prompt = FeedbackPrompts.get_profesor_prompt(user_query)
            
            # Ejecutar consulta con el agente
            result = await self.agent.run(prompt)
            
            return result
            
        except Exception as e:
            error_msg = f"Error generando feedback para profesor: {e}"
            print(f"❌ {error_msg}")
            return error_msg
    
    async def feedback_coordinador_streaming(self, user_query: str, session_id: str, 
                                           callback_url: str) -> str:
        """
        Generar feedback para coordinador con streaming en tiempo real.
        
        Args:
            user_query: Consulta del coordinador
            session_id: ID de la sesión de chat
            callback_url: URL para enviar actualizaciones
            
        Returns:
            str: Respuesta final del análisis
        """
        await self._initialize()
        
        try:
            # Obtener prompt personalizado para coordinador
            prompt = FeedbackPrompts.get_coordinador_prompt(user_query)
            
            # Ejecutar con streaming
            result = await self.streaming_agent.run_with_streaming(
                prompt=prompt,
                session_id=session_id,
                callback_url=callback_url
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Error generando feedback para coordinador: {e}"
            print(f"❌ {error_msg}")
            
            # Enviar error al gateway
            await self.gateway_notifier.send_error_update(
                callback_url=callback_url,
                session_id=session_id,
                error_message=error_msg
            )
            
            raise
    
    async def feedback_profesor_streaming(self, user_query: str, session_id: str,
                                        callback_url: str) -> str:
        """
        Generar feedback para profesor con streaming en tiempo real.
        
        Args:
            user_query: Consulta del profesor
            session_id: ID de la sesión de chat
            callback_url: URL para enviar actualizaciones
            
        Returns:
            str: Respuesta final del análisis
        """
        await self._initialize()
        
        try:
            # Obtener prompt personalizado para profesor
            prompt = FeedbackPrompts.get_profesor_prompt(user_query)
            
            # Ejecutar con streaming
            result = await self.streaming_agent.run_with_streaming(
                prompt=prompt,
                session_id=session_id,
                callback_url=callback_url
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Error generando feedback para profesor: {e}"
            print(f"❌ {error_msg}")
            
            # Enviar error al gateway
            await self.gateway_notifier.send_error_update(
                callback_url=callback_url,
                session_id=session_id,
                error_message=error_msg
            )
            
            raise
    
    async def get_available_tools(self) -> list:
        """
        Obtener lista de herramientas disponibles en MCP.
        
        Returns:
            list: Lista de herramientas disponibles
        """
        await self._initialize()
        
        try:
            tools = await self.mcp_client.get_all_tools()
            return tools
        except Exception as e:
            print(f"❌ Error obteniendo herramientas: {e}")
            return []
    
    async def close(self):
        """Cerrar conexiones y limpiar recursos"""
        if self.mcp_client:
            await self.mcp_client.disconnect()
            print("✅ Servicio de feedback cerrado correctamente")
        
        if self.gateway_notifier:
            await self.gateway_notifier.close()


# Función de conveniencia para uso directo
async def crear_feedback_coordinador(user_query: str, config_file: str = "postgres_mcp_crystaldba.json") -> str:
    """
    Función de conveniencia para crear feedback de coordinador.
    
    Args:
        user_query: Consulta del coordinador
        config_file: Archivo de configuración MCP
        
    Returns:
        str: Feedback generado
    """
    service = FeedbackGeneralService(config_file)
    try:
        result = await service.feedback_general_coordinador(user_query)
        return result
    finally:
        await service.close()


async def crear_feedback_profesor(user_query: str, config_file: str = "postgres_mcp_crystaldba.json") -> str:
    """
    Función de conveniencia para crear feedback de profesor.
    
    Args:
        user_query: Consulta del profesor
        config_file: Archivo de configuración MCP
        
    Returns:
        str: Feedback generado
    """
    service = FeedbackGeneralService(config_file)
    try:
        result = await service.feedback_general_profesor(user_query)
        return result
    finally:
        await service.close()
