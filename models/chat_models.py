"""
Modelos para streaming y chat en tiempo real
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class LLMStreamingRequest(BaseModel):
    """Modelo para requests de streaming del LLM"""
    sessionId: str = Field(
        ...,
        description="ID de la sesión de chat",
        example="session123"
    )
    partialMessage: str = Field(
        ...,
        description="Mensaje parcial o actualización",
        example="Analizando datos..."
    )
    status: str = Field(
        ...,
        description="Estado del procesamiento",
        example="processing"
    )
    isComplete: bool = Field(
        ...,
        description="Indica si el procesamiento está completo",
        example=False
    )


class LLMChatRequest(BaseModel):
    """Modelo para requests de chat asíncrono"""
    sessionId: str = Field(
        ...,
        description="ID de la sesión de chat",
        example="session123"
    )
    message: str = Field(
        ...,
        description="Mensaje del usuario",
        min_length=1,
        max_length=2000,
        example="¿Cómo le fue a la clase con id 5?"
    )
    userRole: str = Field(
        ...,
        description="Rol del usuario: 'coordinador' o 'profesor'",
        example="coordinador"
    )
    previousMessages: List[str] = Field(
        default_factory=list,
        description="Lista de mensajes anteriores del historial de chat",
        example=["Usuario: ¿Cuántos equipos hay?", "Asistente: Hay 15 equipos registrados..."]
    )
    callbackUrl: str = Field(
        ...,
        description="URL donde el LLM enviará las actualizaciones",
        example="http://localhost:8080/api/chat/llm-update"
    )


class ChatMessageResponse(BaseModel):
    """Modelo para responses de mensajes de chat"""
    sessionId: str = Field(
        ...,
        description="ID de la sesión de chat",
        example="session123"
    )
    message: str = Field(
        ...,
        description="Mensaje de respuesta",
        example="Análisis completo del desempeño..."
    )
    messageType: str = Field(
        ...,
        description="Tipo de mensaje",
        example="assistant"
    )
    timestamp: datetime = Field(
        ...,
        description="Timestamp del mensaje",
        example="2025-08-04T10:30:00"
    )
    isComplete: bool = Field(
        ...,
        description="Indica si es el mensaje final",
        example=True
    )
    
    @classmethod
    def user_message(cls, session_id: str, message: str):
        """Crear mensaje de usuario"""
        return cls(
            sessionId=session_id,
            message=message,
            messageType="user",
            timestamp=datetime.now(),
            isComplete=False
        )
    
    @classmethod
    def assistant_message(cls, session_id: str, message: str, is_complete: bool = False):
        """Crear mensaje del asistente"""
        return cls(
            sessionId=session_id,
            message=message,
            messageType="assistant",
            timestamp=datetime.now(),
            isComplete=is_complete
        )
    
    @classmethod
    def status_message(cls, session_id: str, message: str):
        """Crear mensaje de estado"""
        return cls(
            sessionId=session_id,
            message=message,
            messageType="status",
            timestamp=datetime.now(),
            isComplete=False
        )
    
    @classmethod
    def error_message(cls, session_id: str, message: str):
        """Crear mensaje de error"""
        return cls(
            sessionId=session_id,
            message=message,
            messageType="error",
            timestamp=datetime.now(),
            isComplete=True
        )
