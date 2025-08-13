import asyncio
from dotenv import load_dotenv
from services.feedback_general import FeedbackGeneralService


async def main():
    # Carga de variables de entorno
    load_dotenv()

    # Crear servicio de feedback
    service = FeedbackGeneralService(config_file="postgres_mcp_crystaldba.json")
    
    try:    
        # Ejemplo de uso para coordinador
        print("\n=== FEEDBACK COORDINADOR ===")
        coordinador_query = """
            Dime como le fue a la clase con id 5
        """
        
        coordinador_result = await service.feedback_general_coordinador(coordinador_query)
        print("Resultado coordinador:")
        print(coordinador_result)
        
    except Exception as e:
        print(f"Error durante la ejecución: {e}")
        print("Tipo de error:", type(e).__name__)
    finally:
        # Cerrar servicio
        await service.close()


if __name__ == "__main__":
    asyncio.run(main())
