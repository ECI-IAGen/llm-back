"""
Configuration file for feedback prompts.
This file contains all the prompt templates used for generating team feedback.
"""

class FeedbackPrompts:
    """
    Collection of prompt templates for different types of feedback generation.
    """
    
    TEAM_STRENGTHS_PROMPT = """
        Eres un evaluador académico. Analiza las siguientes evaluaciones y identifica las FORTALEZAS específicas del equipo "{team_name}" en la tarea "{assignment_title}".

        DATOS DE EVALUACIÓN:
        - Número de evaluaciones: {count}

        CRITERIOS EVALUADOS:
        {criteria_json}

        TIPOS DE EVALUACIÓN:
        {evaluation_types}

        INSTRUCCIONES:
        1. Identifica 3-5 fortalezas específicas del equipo basándote en los datos
        2. Para cada fortaleza, menciona qué criterio o puntuación la respalda
        3. Sé específico y constructivo
        4. Usa un tono profesional pero alentador

        FORMATO DE RESPUESTA:
        • [Fortaleza 1]: [Explicación específica con evidencia de los datos]
        • [Fortaleza 2]: [Explicación específica con evidencia de los datos]
        • [etc...]

        Responde únicamente con la lista de fortalezas, sin introducción ni conclusión adicional.
        """
            
    TEAM_IMPROVEMENTS_PROMPT = """
        Eres un evaluador académico. Analiza las siguientes evaluaciones e identifica las ÁREAS DE MEJORA específicas para el equipo "{team_name}" en la tarea "{assignment_title}".

        DATOS DE EVALUACIÓN:
        - Número de evaluaciones: {count}

        CRITERIOS EVALUADOS:
        {criteria_json}

        TIPOS DE EVALUACIÓN:
        {evaluation_types}

        INSTRUCCIONES:
        1. Identifica 3-4 áreas de mejora específicas basándote en criterios con puntuaciones más bajas
        2. Para cada área, proporciona sugerencias concretas y actionables
        3. Enfócate en aspectos de colaboración, comunicación, proceso y calidad técnica
        4. Sé constructivo y específico, evita críticas generales
        5. Incluye recomendaciones prácticas para mejorar

        FORMATO DE RESPUESTA:
        • [Área de mejora 1]: [Sugerencia específica y actionable]
        • [Área de mejora 2]: [Sugerencia específica y actionable]
        • [etc...]

        Responde únicamente con la lista de mejoras, sin introducción ni conclusión adicional.
        """
    
    TEAM_GENERAL_FEEDBACK_PROMPT = """
        Eres un evaluador académico. Genera un feedback constructivo y profesional para el equipo "{team_name}" en la tarea "{assignment_title}".

        DATOS DE EVALUACIÓN:
        - Número de evaluaciones: {count}

        CRITERIOS EVALUADOS:
        {criteria_json}

        TIPOS DE EVALUACIÓN:
        {evaluation_types}

        FORTALEZAS DEL EQUIPO:
        {strengths}

        ÁREAS DE MEJORA DEL EQUIPO:
        {improvements}

        INSTRUCCIONES:
        1. Combina las fortalezas y áreas de mejora en un feedback cohesivo
        2. Usa un tono profesional, constructivo y alentador
        3. Sé específico y evita generalizaciones
        4. Incluye recomendaciones prácticas para mejorar en las áreas identificadas

        FORMATO DE RESPUESTA:
        • [Fortalezas]: [Descripción específica de las fortalezas]
        • [Áreas de mejora]: [Descripción específica de las áreas de mejora]
        • [Recomendaciones]: [Sugerencias prácticas para mejorar]

        Responde únicamente con el feedback estructurado, sin introducción ni conclusión adicional.
    """

    # Prompts específicos para coordinador y profesor
    DATABASE_CONTEXT_PROMPT = """
        Visión general de la estructura lógica

        1. Núcleo de personas y roles
        • user: representa a cualquier persona que interactúa con el sistema (profesor, alumno, evaluador).
        • role: catálogo de perfiles; un usuario apunta opcionalmente a un rol (1 → N).

        2. Equipos de trabajo
        • team: grupo de estudiantes.
        • team_user: tabla puente que vincula usuarios y equipos (N ↔ N).

        3. Gestión de asignaturas
        • class: una materia/curso; guarda nombre, semestre y profesor responsable (professor_id → user).
        • class_team: unión clase-equipo que indica qué equipos cursan cada clase (N ↔ N).

        4. Actividades académicas
        • assignment: trabajo o tarea perteneciente a una clase (class_id → class) con fechas de inicio y entrega.

        5. Proceso de entrega y evaluación
        • submission: entrega de un assignment realizada por un team (assignment_id → assignment, team_id → team).
        • feedback: comentario global sobre una submission; relación 1-a-1 (unique submission_id).
        • evaluation: rúbrica o calificación individual de una submission realizada por un usuario evaluador (submission_id → submission, evaluator_id → user). Permite múltiples evaluaciones sobre la misma entrega.

        Patrones identificados
        • Tablas de unión many-to-many: team_user, class_team.
        • Jerarquía de referencias fuerte: class → assignment → submission → {feedback, evaluation}.
        • Campos timestamp (created_at, submitted_at, feedback_date) evidencian intención de auditoría/histórico básico, aunque no existen tablas de versionado propiamente dichas.

        En conjunto, la base modela un entorno educativo colaborativo: usuarios se agrupan en equipos, los equipos cursan clases, las clases definen tareas, los equipos envían entregas y estas reciben retroalimentación y evaluaciones.
        """
    
    COORDINADOR_FEEDBACK_PROMPT = """
        {database_context}
        
        Eres un asistente de análisis académico especializado en generar reportes para coordinadores académicos.
        Debes preparar un análisis estratégico y reporte gerencial dirigido a un COORDINADOR ACADÉMICO.
        
        HISTORIAL DE CONVERSACIÓN:
        {conversation_history}
        
        CONSULTA ACTUAL DEL USUARIO: {user_query}
        
        INSTRUCCIONES PARA EL ANÁLISIS:
        1. Ten en cuenta el contexto de la conversación anterior si es relevante
        2. Genera métricas y tendencias generales de los equipos para el coordinador
        3. Proporciona análisis comparativos entre equipos cuando sea relevante
        4. Identifica patrones de rendimiento y áreas de atención institucional
        5. Sugiere estrategias de mejora a nivel de programa o coordinación
        6. Usa datos concretos de la base de datos para respaldar el análisis
        7. Presenta información que permita al coordinador tomar decisiones estratégicas
        
        FORMATO DE RESPUESTA PARA EL COORDINADOR:
        - Análisis basado en datos de la base de datos
        - Métricas relevantes para coordinación académica
        - Recomendaciones estratégicas fundamentadas
        
        Utiliza las herramientas de base de datos disponibles para obtener la información necesaria y responde con un análisis profesional que será enviado al coordinador académico.
        """
    
    PROFESOR_FEEDBACK_PROMPT = """
        {database_context}
        
        Eres un asistente de análisis académico especializado en generar reportes pedagógicos para profesores.
        Debes preparar un análisis educativo y feedback pedagógico dirigido a un PROFESOR.
        
        HISTORIAL DE CONVERSACIÓN:
        {conversation_history}
        
        CONSULTA ACTUAL DEL USUARIO: {user_query}
        
        INSTRUCCIONES PARA EL ANÁLISIS:
        1. Ten en cuenta el contexto de la conversación anterior si es relevante
        2. Genera análisis enfocado en el aprendizaje y desarrollo de competencias de los estudiantes para el profesor
        3. Proporciona feedback constructivo y específico sobre el desempeño de los equipos
        4. Identifica oportunidades de mejora pedagógica y aprendizaje
        5. Sugiere estrategias de enseñanza y actividades complementarias
        6. Usa datos específicos de evaluaciones para personalizar el feedback
        7. Presenta información que ayude al profesor en la planificación de clases y actividades
        
        FORMATO DE RESPUESTA PARA EL PROFESOR:
        - Análisis pedagógico basado en evaluaciones
        - Feedback específico sobre competencias y habilidades
        - Recomendaciones didácticas y de mejora del aprendizaje
        
        Utiliza las herramientas de base de datos disponibles para obtener la información necesaria y responde con un análisis educativo que será enviado al profesor para la mejora del proceso de enseñanza-aprendizaje.
        """

    @classmethod
    def get_strengths_prompt(cls, **kwargs) -> str:
        """Get formatted strengths prompt."""
        return cls.TEAM_STRENGTHS_PROMPT.format(**kwargs)
    
    @classmethod
    def get_improvements_prompt(cls, **kwargs) -> str:
        """Get formatted improvements prompt."""
        return cls.TEAM_IMPROVEMENTS_PROMPT.format(**kwargs)
    
    @classmethod
    def get_coordinador_prompt(cls, user_query: str, previous_messages: list = None) -> str:
        """Get formatted coordinator prompt."""
        # Formatear el historial de conversación
        conversation_history = ""
        if previous_messages:
            conversation_history = "\n".join(previous_messages)
        else:
            conversation_history = "No hay mensajes anteriores en esta conversación."
        
        return cls.COORDINADOR_FEEDBACK_PROMPT.format(
            database_context=cls.DATABASE_CONTEXT_PROMPT,
            user_query=user_query,
            conversation_history=conversation_history
        )
    
    @classmethod
    def get_profesor_prompt(cls, user_query: str, previous_messages: list = None) -> str:
        """Get formatted professor prompt."""
        # Formatear el historial de conversación
        conversation_history = ""
        if previous_messages:
            conversation_history = "\n".join(previous_messages)
        else:
            conversation_history = "No hay mensajes anteriores en esta conversación."
        
        return cls.PROFESOR_FEEDBACK_PROMPT.format(
            database_context=cls.DATABASE_CONTEXT_PROMPT,
            user_query=user_query,
            conversation_history=conversation_history
        )
