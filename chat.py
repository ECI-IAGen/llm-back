"""
Chat con DeepSeek + GitHub MCP - Versión Simplificada
"""
import asyncio
import sys
from src.config import Config, Colors
from src.deepseek_client import DeepSeekClient
from src.github_mcp_client import GitHubMCPClient


class ChatInterface:
    """Chat que combina DeepSeek con herramientas MCP de GitHub"""
    
    def __init__(self, config: Config):
        self.config = config
        self.deepseek = DeepSeekClient(config)
        self.github_mcp = GitHubMCPClient(config)
        self.conversation_history = []
        self.mcp_connected = False
        
    def display_banner(self):
        """Muestra el banner de bienvenida"""
        print(f"\n{Colors.HEADER}{'='*50}")
        print(f"{Colors.BOLD}🤖 CHAT DEEPSEEK + GITHUB 🔧")
        print(f"{'='*50}{Colors.ENDC}")
        print(f"{Colors.CYAN}Usuario: {self.config.github_username}")
        print(f"✨ DeepSeek con herramientas GitHub automáticas")
        print(f"\nComandos:")
        print(f"  /help - Ayuda")
        print(f"  /tools - Ver herramientas")
        print(f"  /clear - Limpiar historial")
        print(f"  /quit - Salir{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*50}{Colors.ENDC}\n")
    
    def display_help(self):
        """Muestra la ayuda del sistema"""
        print(f"\n{Colors.BLUE}📋 CAPACIDADES DEL CHAT:")
        print(f"{Colors.GREEN}🔧 AUTOMÁTICO:")
        print(f"{Colors.CYAN}• Busca repositorios: 'busca mi repo Gomoku'")
        print(f"{Colors.CYAN}• Lee archivos: 'muestra el README de X'")
        print(f"{Colors.CYAN}• Analiza código: 'qué hace mi proyecto Y'")
        
        print(f"\n{Colors.BLUE}📋 COMANDOS:")
        print(f"{Colors.CYAN}/help{Colors.ENDC} - Esta ayuda")
        print(f"{Colors.CYAN}/tools{Colors.ENDC} - Ver herramientas disponibles")
        print(f"{Colors.CYAN}/clear{Colors.ENDC} - Limpiar historial")
        print(f"{Colors.CYAN}/quit{Colors.ENDC} - Salir")
        
        print(f"\n{Colors.GREEN}💡 EJEMPLOS:")
        print(f"{Colors.YELLOW}• 'Busca mi repositorio Gomoku'")
        print(f"{Colors.YELLOW}• 'Analiza mi proyecto VintageGame'")
        print(f"{Colors.YELLOW}• 'Qué repos tengo actualizados?'{Colors.ENDC}")
        print()
    
    async def setup_connections(self):
        """Configura las conexiones necesarias"""
        print(f"{Colors.CYAN}🔌 Configurando conexiones...{Colors.ENDC}")
        
        # Conectar GitHub MCP
        print(f"{Colors.CYAN}📡 Conectando a GitHub MCP...{Colors.ENDC}")
        success = await self.github_mcp.connect()
        
        if success:
            self.mcp_connected = True
            # Configurar DeepSeek para usar herramientas MCP
            self.deepseek.set_mcp_client(self.github_mcp)
            print(f"{Colors.GREEN}✅ GitHub MCP conectado correctamente{Colors.ENDC}")
        else:
            self.mcp_connected = False
            print(f"{Colors.WARNING}⚠️ No se pudo conectar GitHub MCP - continuando sin herramientas{Colors.ENDC}")
    
    async def show_available_tools(self):
        """Muestra las herramientas MCP disponibles"""
        if not self.mcp_connected:
            print(f"{Colors.RED}❌ No hay conexión MCP activa{Colors.ENDC}")
            return
        
        print(f"\n{Colors.BLUE}🔧 HERRAMIENTAS DISPONIBLES:")
        tools_context = self.github_mcp.create_tools_context()
        print(f"{Colors.CYAN}{tools_context}{Colors.ENDC}")
    
    def clear_conversation(self):
        """Limpia el historial de conversación"""
        self.conversation_history.clear()
        print(f"{Colors.GREEN}🧹 Historial de conversación limpiado{Colors.ENDC}")
    
    async def process_user_input(self, user_input: str) -> bool:
        """
        Procesa la entrada del usuario
        
        Args:
            user_input: Entrada del usuario
            
        Returns:
            True para continuar, False para salir
        """
        user_input = user_input.strip()
        
        # Comandos especiales
        if user_input.lower() == "/quit":
            return False
        elif user_input.lower() == "/help":
            self.display_help()
            return True
        elif user_input.lower() == "/clear":
            self.clear_conversation()
            return True
        elif user_input.lower() == "/tools":
            await self.show_available_tools()
            return True
        elif user_input.startswith("/"):
            print(f"{Colors.RED}❓ Comando desconocido. Usa /help para ver comandos.{Colors.ENDC}")
            return True
        
        # Procesar mensaje normal
        if not user_input:
            return True
        
        print(f"\n{Colors.BLUE}🤖 DeepSeek está procesando...{Colors.ENDC}")
        
        try:
            # Usar chat con herramientas MCP
            response = await self.deepseek.chat_with_tools(
                user_message=user_input,
                conversation_history=self.conversation_history
            )
            
            if response:
                print(f"\n{Colors.GREEN}🤖 DeepSeek:{Colors.ENDC}")
                print(f"{response}")
                
                # Actualizar historial
                self.conversation_history.append({"role": "user", "content": user_input})
                self.conversation_history.append({"role": "assistant", "content": response})
                
                # Mantener historial manejable (últimos 10 intercambios)
                if len(self.conversation_history) > 20:
                    self.conversation_history = self.conversation_history[-20:]
            else:
                print(f"{Colors.RED}❌ No se pudo obtener respuesta de DeepSeek{Colors.ENDC}")
                
        except Exception as e:
            print(f"{Colors.RED}❌ Error procesando mensaje: {str(e)}{Colors.ENDC}")
        
        return True
    
    async def run(self):
        """Ejecuta el bucle principal del chat"""
        try:
            self.display_banner()
            
            # Configurar conexiones
            await self.setup_connections()
            
            print(f"\n{Colors.GREEN}💬 ¡Chat listo! Puedes empezar a conversar.{Colors.ENDC}")
            print(f"{Colors.GREEN}✨ DeepSeek puede usar herramientas de GitHub automáticamente.{Colors.ENDC}")
            print(f"{Colors.CYAN}Escribe /help para ver todas las capacidades.{Colors.ENDC}\n")
            
            # Bucle principal
            while True:
                try:
                    user_input = input(f"{Colors.BOLD}👤 Tú: {Colors.ENDC}")
                    should_continue = await self.process_user_input(user_input)
                    
                    if not should_continue:
                        break
                        
                except KeyboardInterrupt:
                    print(f"\n{Colors.YELLOW}👋 ¡Hasta luego!{Colors.ENDC}")
                    break
                except EOFError:
                    break
                    
        except Exception as e:
            print(f"{Colors.RED}❌ Error fatal: {str(e)}{Colors.ENDC}")
            
        finally:
            # Limpiar conexiones
            if self.mcp_connected:
                await self.github_mcp.disconnect()
            print(f"{Colors.YELLOW}🔌 Conexiones cerradas{Colors.ENDC}")


async def main():
    """Función principal"""
    try:
        # Cargar configuración
        config = Config.from_env()
        
        # Crear e iniciar chat
        chat = ChatInterface(config)
        await chat.run()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}👋 ¡Hasta luego!{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.RED}❌ Error fatal: {str(e)}{Colors.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
