import asyncio
from dotenv import load_dotenv
from mcp_use.agents.mcpagent import MCPAgent
from core.mcp_client import MCPClient
from core.mcp_server import MCPServer
from core.llm import LLMProvider, LLMFactory

async def main():
    # Carga de variables de entorno (por si pones token GitHub en .env)
    load_dotenv()

    # Crear servidor MCP con el archivo de configuración
    mcp_server = MCPServer(config_file="postgres_mcp_crystaldba.json")

    print("Servidor MCP creado")

    # Crear cliente MCP con conexión automática
    mcp_client = await MCPClient.create(mcp_server)

    print("Cliente MCP conectado")
    
    # Obtener todas las herramientas disponibles
    all_tools = await mcp_client.get_all_tools()
    
    # Obtener el cliente mcp_use subyacente
    client = mcp_client.get_client()

    llm = LLMFactory.create_llm(
        provider=LLMProvider.DEEPSEEK,
        model="deepseek-chat",
        temperature=1
    )

    # Definir herramientas específicas que quieres usar
    allowed_tools = [
    ]
    
    # Filtrar herramientas permitidas y restringidas
    allowed, restricted_tools = mcp_client.filter_allowed_tools(all_tools, allowed_tools)

    agent = MCPAgent(llm=llm, client=client, max_steps=50, 
                     disallowed_tools=[])

    try:
        result = await agent.run(
            """
            Tienes acceso de solo lectura a una base de datos. Tu tarea es generar un resumen general y conciso de su estructura lógica, útil como contexto inicial para futuros análisis.

            Describe:

            Las principales entidades (tablas) y qué representan en el dominio del sistema.

            Las relaciones clave entre tablas, destacando claves foráneas, dependencias fuertes y jerarquías importantes.

            Si aplica, identifica patrones comunes como tablas de unión (many-to-many), entidades auditables o entidades con datos históricos.

            El resultado debe ser breve, sin detallar todos los campos, enfocado en ayudar a entender cómo está organizada la información y qué rol cumple cada grupo de tablas dentro del sistema.

            No incluyas valores de ejemplo ni datos reales. Solo estructura y significado.
        """
        )
        print("Result:", result)
    except Exception as e:
        print(f"Error durante la ejecución del agente: {e}")
        print("Tipo de error:", type(e).__name__)
    finally:
        # Desconectar
        await mcp_client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
