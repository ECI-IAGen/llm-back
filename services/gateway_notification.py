"""
Servicio para comunicación HTTP con el API Gateway
"""
import asyncio
import httpx
from typing import Optional
from models.chat_models import LLMStreamingRequest, ChatMessageResponse
from datetime import datetime
import logging

# Configurar logging
logger = logging.getLogger(__name__)


class GatewayNotificationService:
    """
    Servicio para enviar notificaciones HTTP al API Gateway
    """
    
    def __init__(self, timeout: int = 10):
        """
        Inicializar el servicio de notificaciones.
        
        Args:
            timeout: Timeout para requests HTTP en segundos
        """
        self.timeout = timeout
        self.client = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Obtener cliente HTTP reutilizable"""
        if self.client is None or self.client.is_closed:
            self.client = httpx.AsyncClient(timeout=self.timeout)
        return self.client
    
    async def send_update(self, callback_url: str, session_id: str, message: str, 
                         status: str = "processing", is_complete: bool = False) -> bool:
        """
        Enviar actualización al gateway.
        
        Args:
            callback_url: URL del callback del gateway
            session_id: ID de la sesión
            message: Mensaje de actualización
            status: Estado del procesamiento
            is_complete: Si el procesamiento está completo
            
        Returns:
            bool: True si se envió exitosamente, False en caso contrario
        """
        if message.startswith("🎉 Agent execution complete") or message.startswith("✅ Agent finished"):
            return True  # No enviar actualizaciones si ya está completo
        try:
            client = await self._get_client()
            
            # Crear request de streaming
            streaming_request = LLMStreamingRequest(
                sessionId=session_id,
                partialMessage=message,
                status=status,
                isComplete=is_complete
            )
            
            print(streaming_request.model_dump(by_alias=True))
            
            # Enviar POST al gateway
            response = await client.post(
                callback_url,
                json=streaming_request.model_dump(by_alias=True),
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            logger.info(f"✅ Actualización enviada a gateway: {session_id} - {status}")
            return True
            
        except httpx.TimeoutException:
            logger.warning(f"⏰ Timeout enviando actualización para sesión {session_id}")
            return False
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Error HTTP enviando actualización: {e.response.status_code}")
            return False
        except Exception as e:
            logger.error(f"❌ Error enviando actualización para sesión {session_id}: {e}")
            return False
    
    async def close(self):
        """Cerrar cliente HTTP"""
        if self.client and not self.client.is_closed:
            await self.client.aclose()
            logger.info("✅ Cliente HTTP cerrado")


# Instancia global del servicio
gateway_notifier = GatewayNotificationService()
