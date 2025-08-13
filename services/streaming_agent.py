"""
Wrapper del agente MCP con notificaciones en tiempo real
"""
import asyncio
import logging
from typing import Optional, AsyncGenerator
from mcp_use.agents.mcpagent import MCPAgent
from services.gateway_notification import GatewayNotificationService

logger = logging.getLogger(__name__)

class MCPLogHandler(logging.Handler):
    """Handler personalizado para capturar logs del agente MCP"""
    
    def __init__(self, gateway_notifier: GatewayNotificationService, 
                 session_id: str, callback_url: str):
        super().__init__()
        self.gateway_notifier = gateway_notifier
        self.session_id = session_id
        self.callback_url = callback_url
        
    def emit(self, record):
        """Capturar y enviar logs del agente MCP"""
        if record.name == 'mcp_use' and record.levelno >= logging.INFO:
            message = record.getMessage()
            
            # Enviar el mensaje exacto de la consola al gateway
            asyncio.create_task(
                self.gateway_notifier.send_update(
                    callback_url=self.callback_url,
                    session_id=self.session_id,
                    message=message,
                    status="processing",
                    is_complete=False
                )
            )


class StreamingMCPAgent:
    """
    Wrapper del MCPAgent que envía actualizaciones de estado en tiempo real
    """
    
    def __init__(self, agent: MCPAgent, gateway_notifier: GatewayNotificationService):
        """
        Inicializar el agente con streaming.
        
        Args:
            agent: Instancia del MCPAgent
            gateway_notifier: Servicio de notificaciones al gateway
        """
        self.agent = agent
        self.gateway_notifier = gateway_notifier
    
    async def run_with_streaming(self, prompt: str, session_id: str, 
                               callback_url: str) -> str:
        """
        Ejecutar el agente enviando actualizaciones en tiempo real.
        
        Args:
            prompt: Prompt para el agente
            session_id: ID de la sesión
            callback_url: URL para enviar actualizaciones
            
        Returns:
            str: Resultado final del agente
        """
        # Configurar handler personalizado para capturar logs del agente MCP
        mcp_logger = logging.getLogger('mcp_use')
        log_handler = MCPLogHandler(self.gateway_notifier, session_id, callback_url)
        mcp_logger.addHandler(log_handler)
        
        try:
            # Enviar notificación inicial
            await self.gateway_notifier.send_update(
                callback_url=callback_url,
                session_id=session_id,
                message="🚀 Iniciando análisis...",
                status="processing",
                is_complete=False
            )
            
            # Ejecutar el agente (sin monitoreo de progreso ficticio)
            result = await self.agent.run(prompt)
            # Enviar resultado final
            await self.gateway_notifier.send_update(
                callback_url=callback_url,
                session_id=session_id,
                message=result,
                status="completed",
                is_complete=True
            )
            
            return result
            
        except Exception as e:
            # Enviar error al gateway
            await self.gateway_notifier.send_update(
                callback_url=callback_url,
                session_id=session_id,
                message=str(e),
                status="completed",
                is_complete=True
            )
            raise
        finally:
            # Remover el handler personalizado
            mcp_logger.removeHandler(log_handler)
    
class EnhancedMCPAgent:
    """
    Versión mejorada del agente MCP con callbacks personalizados
    """
    
    def __init__(self, agent: MCPAgent, gateway_notifier: GatewayNotificationService):
        self.agent = agent
        self.gateway_notifier = gateway_notifier
    
    async def run_with_callbacks(self, prompt: str, session_id: str, 
                               callback_url: str) -> str:
        """
        Ejecutar agente con callbacks para actualizaciones en tiempo real.
        
        Args:
            prompt: Prompt para el agente
            session_id: ID de la sesión
            callback_url: URL para callbacks
            
        Returns:
            str: Resultado del agente
        """
        # Configurar handler personalizado para capturar logs del agente MCP
        mcp_logger = logging.getLogger('mcp_use')
        log_handler = MCPLogHandler(self.gateway_notifier, session_id, callback_url)
        mcp_logger.addHandler(log_handler)
        
        try:
            # Notificación inicial
            await self.gateway_notifier.send_update(
                callback_url=callback_url,
                session_id=session_id,
                message="🚀 Conectando a base de datos...",
                status="processing",
                is_complete=False
            )
            
            # Ejecutar el agente (los logs se capturarán automáticamente)
            result = await self.agent.run(prompt)
            
            # Enviar resultado final
            await self.gateway_notifier.send_completion_update(
                callback_url=callback_url,
                session_id=session_id,
                final_message=result
            )
            
            return result
            
        except Exception as e:
            await self.gateway_notifier.send_error_update(
                callback_url=callback_url,
                session_id=session_id,
                error_message=str(e)
            )
            raise
        finally:
            # Remover el handler personalizado
            mcp_logger.removeHandler(log_handler)
