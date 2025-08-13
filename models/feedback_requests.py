"""
Modelos para requests y responses de feedback general
"""
from pydantic import BaseModel, Field
from typing import Optional


class FeedbackRequest(BaseModel):
    """Modelo para requests de feedback general"""
    message: str = Field(
        ..., 
        description="Mensaje o consulta del usuario",
        min_length=1,
        max_length=2000,
        example="¿Cómo le fue a la clase con id 5 en sus últimas evaluaciones?"
    )


class FeedbackResponse(BaseModel):
    """Modelo para responses de feedback general"""
    response: str = Field(
        ..., 
        description="Respuesta generada por el modelo de IA",
        example="Análisis detallado del desempeño de la clase..."
    )


class FeedbackTypeInfo(BaseModel):
    """Modelo para información de tipos de feedback"""
    type: str = Field(
        ...,
        description="Tipo de feedback",
        example="coordinador"
    )
    endpoint: str = Field(
        ...,
        description="Endpoint para el tipo de feedback",
        example="/feedback/coordinador"
    )
    description: str = Field(
        ...,
        description="Descripción del tipo de feedback",
        example="Feedback estratégico y análisis para coordinadores académicos"
    )
    input: dict = Field(
        ...,
        description="Estructura del input esperado",
        example={"message": "str - Consulta o petición del coordinador"}
    )
    output: dict = Field(
        ...,
        description="Estructura del output esperado",
        example={"response": "str - Análisis estratégico personalizado"}
    )


class FeedbackTypesResponse(BaseModel):
    """Modelo para response de tipos de feedback disponibles"""
    feedback_types: list[FeedbackTypeInfo] = Field(
        ...,
        description="Lista de tipos de feedback disponibles"
    )
