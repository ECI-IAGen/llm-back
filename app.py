from fastapi import FastAPI, HTTPException, BackgroundTasks
from models import (
    EvaluationDTO,
    FeedbackRequest,
    FeedbackResponse,
    FeedbackTypesResponse,
    FeedbackTypeInfo,
    LLMChatRequest,
    ChatMessageResponse
)
from services import FeedbackEquipo
from services.feedback_general import FeedbackGeneralService
import asyncio

app = FastAPI(
    title="GitHub Java Code Analyzer API",
    description="API para análisis de código Java en repositorios de GitHub usando Checkstyle y LLM",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Endpoint de salud de la API"""
    return {
        "message": "GitHub Java Code Analyzer API",
        "status": "active",
        "endpoints": [
            "/feedback/coordinador",
            "/feedback/profesor", 
            "/feedback/equipo",
            "/feedback/coordinador/chat",
            "/feedback/profesor/chat",
            "/feedback/types"
        ]
    }

@app.post("/feedback/coordinador", response_model=FeedbackResponse)
async def generate_coordinator_feedback(request: FeedbackRequest) -> FeedbackResponse:
    """
    Generar feedback específico para coordinadores académicos.
    
    Args:
        request: Request con el mensaje/consulta del coordinador
        
    Returns:
        Response con el análisis estratégico y feedback generado
    """
    try:
        # Crear servicio de feedback
        service = FeedbackGeneralService(config_file="postgres_mcp_crystaldba.json")
        
        # Generar feedback para coordinador
        result = await service.feedback_general_coordinador(request.message)
        
        # Cerrar conexiones
        await service.close()
        
        return FeedbackResponse(response=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando feedback para coordinador: {str(e)}")

@app.post("/feedback/profesor", response_model=FeedbackResponse)
async def generate_teacher_feedback(request: FeedbackRequest) -> FeedbackResponse:
    """
    Generar feedback específico para profesores.
    
    Args:
        request: Request con el mensaje/consulta del profesor
        
    Returns:
        Response con el análisis pedagógico y feedback generado
    """
    try:
        # Crear servicio de feedback
        service = FeedbackGeneralService(config_file="postgres_mcp_crystaldba.json")
        
        # Generar feedback para profesor
        result = await service.feedback_general_profesor(request.message)
        
        # Cerrar conexiones
        await service.close()
        
        return FeedbackResponse(response=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando feedback para profesor: {str(e)}")

@app.post("/feedback/coordinador/chat", response_model=ChatMessageResponse)
async def generate_coordinator_feedback_async(request: LLMChatRequest, 
                                            background_tasks: BackgroundTasks) -> ChatMessageResponse:
    """
    Generar feedback asíncrono para coordinadores con streaming en tiempo real.
    
    Args:
        request: Request con datos de chat y callback URL
        background_tasks: Tareas en background de FastAPI
        
    Returns:
        Response inicial confirmando que el procesamiento ha iniciado
    """
    try:
        # Respuesta inmediata para confirmar recepción
        response = ChatMessageResponse.status_message(
            session_id=request.sessionId,
            message="Mensaje recibido, iniciando análisis..."
        )
        
        # Agregar tarea en background para el procesamiento real
        background_tasks.add_task(
            _process_coordinador_feedback_async,
            request.message,
            request.sessionId,
            request.callbackUrl
        )
        
        return response
        
    except Exception as e:
        return ChatMessageResponse.error_message(
            session_id=request.sessionId,
            message=f"Error iniciando procesamiento: {str(e)}"
        )

@app.post("/feedback/profesor/chat", response_model=ChatMessageResponse)
async def generate_teacher_feedback_async(request: LLMChatRequest,
                                        background_tasks: BackgroundTasks) -> ChatMessageResponse:
    """
    Generar feedback asíncrono para profesores con streaming en tiempo real.
    
    Args:
        request: Request con datos de chat y callback URL
        background_tasks: Tareas en background de FastAPI
        
    Returns:
        Response inicial confirmando que el procesamiento ha iniciado
    """
    try:
        # Respuesta inmediata para confirmar recepción
        response = ChatMessageResponse.status_message(
            session_id=request.sessionId,
            message="Mensaje recibido, iniciando análisis..."
        )
        
        # Agregar tarea en background para el procesamiento real
        background_tasks.add_task(
            _process_profesor_feedback_async,
            request.message,
            request.sessionId,
            request.callbackUrl
        )
        
        return response
        
    except Exception as e:
        return ChatMessageResponse.error_message(
            session_id=request.sessionId,
            message=f"Error iniciando procesamiento: {str(e)}"
        )

@app.post("/feedback/equipo", response_model=dict)
async def generate_team_feedback(request_data: dict) -> dict:
    """
    Generate feedback from team perspective.
    
    Args:
        request_data: Dictionary containing submission and evaluations
        
    Returns:
        Generated feedback DTO as dictionary
    """
    try:
        # Extract submission and evaluations from request
        if "submission" not in request_data or "evaluations" not in request_data:
            raise HTTPException(status_code=400, detail="Request must contain 'submission' and 'evaluations' fields")
        
        # Convert submission dictionary to SubmissionDTO
        from models.submission import SubmissionDTO
        
        # Map camelCase fields to snake_case for SubmissionDTO
        submission_data = request_data["submission"]
        mapped_submission = {
            "id": submission_data.get("id"),
            "assignment_id": submission_data.get("assignmentId"),
            "assignment_title": submission_data.get("assignmentTitle"),
            "team_id": submission_data.get("teamId"),
            "team_name": submission_data.get("teamName"),
            "submitted_at": submission_data.get("submittedAt"),
            "file_url": submission_data.get("fileUrl"),
            "class_id": submission_data.get("classId"),
            "class_name": submission_data.get("className")
        }
        
        submission_dto = SubmissionDTO(**mapped_submission)
        
        # Convert dictionaries to EvaluationDTO objects
        evaluation_dtos = []
        for eval_data in request_data["evaluations"]:
            # Map camelCase fields to snake_case for EvaluationDTO
            mapped_evaluation = {
                "id": eval_data.get("id"),
                "submission_id": eval_data.get("submissionId"),
                "evaluator_id": eval_data.get("evaluatorId"),
                "evaluator_name": eval_data.get("evaluatorName"),
                "evaluation_type": eval_data.get("evaluationType"),
                "score": eval_data.get("score"),
                "criteria_json": eval_data.get("criteriaJson"),
                "created_at": eval_data.get("createdAt"),
                "evaluation_date": eval_data.get("evaluationDate"),
                "team_name": eval_data.get("teamName"),
                "assignment_title": eval_data.get("assignmentTitle"),
                "class_id": eval_data.get("classId"),
                "class_name": eval_data.get("className")
            }
            
            evaluation_dto = EvaluationDTO(**mapped_evaluation)
            evaluation_dtos.append(evaluation_dto)
        
        if not evaluation_dtos:
            raise HTTPException(status_code=400, detail="No evaluations provided")
        
        # Create feedback maker and generate feedback
        feedback_maker = FeedbackEquipo()
        feedback = await feedback_maker.make_feedback(submission_dto, evaluation_dtos)
        
        return feedback.to_dict()
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating team feedback: {str(e)}")


# Additional utility endpoint
@app.get("/feedback/types", response_model=FeedbackTypesResponse)
async def get_feedback_types() -> FeedbackTypesResponse:
    """
    Get available feedback types.
    
    Returns:
        List of available feedback types with descriptions
    """
    feedback_types = [
        FeedbackTypeInfo(
            type="coordinador",
            endpoint="/feedback/coordinador",
            description="Feedback estratégico y análisis para coordinadores académicos",
            input={"message": "str - Consulta o petición del coordinador"},
            output={"response": "str - Análisis estratégico personalizado"}
        ),
        FeedbackTypeInfo(
            type="coordinador-chat",
            endpoint="/feedback/coordinador/chat",
            description="Feedback estratégico asíncrono con streaming en tiempo real",
            input={"sessionId": "str", "message": "str", "userRole": "coordinador", "callbackUrl": "str"},
            output={"sessionId": "str", "message": "str", "messageType": "status", "isComplete": "bool"}
        ),
        FeedbackTypeInfo(
            type="profesor", 
            endpoint="/feedback/profesor",
            description="Feedback pedagógico y análisis para profesores",
            input={"message": "str - Consulta o petición del profesor"},
            output={"response": "str - Análisis pedagógico personalizado"}
        ),
        FeedbackTypeInfo(
            type="profesor-chat",
            endpoint="/feedback/profesor/chat",
            description="Feedback pedagógico asíncrono con streaming en tiempo real",
            input={"sessionId": "str", "message": "str", "userRole": "profesor", "callbackUrl": "str"},
            output={"sessionId": "str", "message": "str", "messageType": "status", "isComplete": "bool"}
        ),
        FeedbackTypeInfo(
            type="equipo",
            endpoint="/feedback/equipo", 
            description="Feedback colaborativo y de dinámicas de equipo",
            input={"submission": "object", "evaluations": "array"},
            output={"feedback": "object - Feedback estructurado para el equipo"}
        )
    ]
    
    return FeedbackTypesResponse(feedback_types=feedback_types)

# Funciones de procesamiento asíncrono
async def _process_coordinador_feedback_async(message: str, session_id: str, callback_url: str):
    """
    Procesar feedback de coordinador de forma asíncrona con streaming.
    
    Args:
        message: Mensaje del coordinador
        session_id: ID de la sesión
        callback_url: URL para enviar actualizaciones
    """
    service = None
    try:
        # Crear servicio de feedback
        service = FeedbackGeneralService(config_file="postgres_mcp_crystaldba.json")
        
        # Generar feedback con streaming
        result = await service.feedback_coordinador_streaming(
            user_query=message,
            session_id=session_id,
            callback_url=callback_url
        )

        print("ENVIANDO NOTIFICACIÓN FINAL")
        await service.gateway_notifier.send_update(
            callback_url=callback_url,
            session_id=session_id,
            message=result,
            status="completed",
            is_complete=True
        )

        print(f"✅ Feedback completado para sesión {session_id}")
        
    except Exception as e:
        print(f"❌ Error en procesamiento asíncrono coordinador: {e}")
        
        # Si hay error y aún tenemos el servicio, intentar enviar notificación de error
        if service and service.gateway_notifier:
            try:
                await service.gateway_notifier.send_update(
                    callback_url=callback_url,
                    session_id=session_id,
                    message=str(e),
                    status="error",
                    is_complete=True
                )
            except:
                pass  # Falló la notificación de error, pero no podemos hacer más
    finally:
        if service:
            await service.close()

async def _process_profesor_feedback_async(message: str, session_id: str, callback_url: str):
    """
    Procesar feedback de profesor de forma asíncrona con streaming.
    
    Args:
        message: Mensaje del profesor
        session_id: ID de la sesión
        callback_url: URL para enviar actualizaciones
    """
    service = None
    try:
        # Crear servicio de feedback
        service = FeedbackGeneralService(config_file="postgres_mcp_crystaldba.json")
        
        # Generar feedback con streaming
        result = await service.feedback_profesor_streaming(
            user_query=message,
            session_id=session_id,
            callback_url=callback_url
        )
        
        print(f"✅ Feedback completado para sesión {session_id}")
        
    except Exception as e:
        print(f"❌ Error en procesamiento asíncrono profesor: {e}")
        
        # Si hay error y aún tenemos el servicio, intentar enviar notificación de error
        if service and service.gateway_notifier:
            try:
                await service.gateway_notifier.send_error_update(
                    callback_url=callback_url,
                    session_id=session_id,
                    error_message=str(e)
                )
            except:
                pass  # Falló la notificación de error, pero no podemos hacer más
    finally:
        if service:
            await service.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8001)