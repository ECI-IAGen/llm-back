"""
Cliente simplificado para DeepSeek API con soporte MCP
"""
import asyncio
import json
import re
import httpx
from typing import Dict, Any, Optional, List
from src.config import Config, Colors


class DeepSeekClient:
    """Cliente para interactuar con la API de DeepSeek"""
    
    def __init__(self, config: Config):
        self.config = config
        self.base_url = "https://api.deepseek.com/v1"
        self.headers = {
            "Authorization": f"Bearer {config.deepseek_api_key}",
            "Content-Type": "application/json"
        }
        self.mcp_client = None
        self.tools_available = False
        
    async def chat_completion(self, 
                            messages: List[Dict[str, str]], 
                            model: str = "deepseek-chat",
                            temperature: float = 0.7,
                            max_tokens: int = 2000) -> Optional[str]:
        """
        Envía una consulta a DeepSeek y retorna la respuesta
        
        Args:
            messages: Lista de mensajes en formato OpenAI
            model: Modelo a usar
            temperature: Creatividad de la respuesta
            max_tokens: Máximo número de tokens en la respuesta
            
        Returns:
            Respuesta del modelo o None si hay error
        """
        try:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=60.0  # Aumentado a 60 segundos
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                elif response.status_code == 429:
                    print(f"{Colors.WARNING}⏳ Rate limit alcanzado, esperando 5 segundos...{Colors.ENDC}")
                    await asyncio.sleep(5)
                    return None
                else:
                    print(f"{Colors.FAIL}❌ Error DeepSeek: {response.status_code} - {response.text}{Colors.ENDC}")
                    return None
                    
        except httpx.TimeoutException:
            print(f"{Colors.WARNING}⏰ Timeout al conectar con DeepSeek - reintentando con contexto reducido...{Colors.ENDC}")
            return None
        except Exception as e:
            print(f"{Colors.FAIL}❌ Error inesperado con DeepSeek: {e}{Colors.ENDC}")
            return None
    
    def set_mcp_client(self, mcp_client):
        """
        Establece el cliente MCP para que DeepSeek pueda usar herramientas
        
        Args:
            mcp_client: Cliente MCP de GitHub
        """
        self.mcp_client = mcp_client
        self.tools_available = mcp_client.connected if mcp_client else False
    
    async def chat_with_tools(self, 
                            user_message: str,
                            conversation_history: List[Dict[str, str]],
                            model: str = "deepseek-chat",
                            temperature: float = 0.7,
                            max_tokens: int = 2000) -> Optional[str]:
        """
        Chat con DeepSeek que puede elegir usar herramientas MCP cuando lo considere necesario
        """
        # Crear mensajes para DeepSeek
        messages = conversation_history.copy()
        
        # Si tenemos herramientas disponibles, informar a DeepSeek
        if self.tools_available and self.mcp_client:
            tools_info = await self.mcp_client.create_tools_context()
            available_tools = self.mcp_client.get_available_tools_list()
            
            system_prompt = f"""Eres un asistente de programación inteligente con acceso a herramientas de GitHub.

                            {tools_info}

                            IMPORTANTE: 
                            - Si necesitas información específica de GitHub para responder al usuario, puedes usar estas herramientas
                            - Para usar una herramienta, responde con este formato JSON:

                            {{
                                "tool_request": {{
                                    "tool_name": "nombre_de_la_herramienta",
                                    "arguments": {{
                                        "param1": "valor1",
                                        "param2": "valor2",
                                        "paramN": "valorN"
                                        // ... puedes agregar tantos parámetros como necesites
                                    }}
                                }},
                                "reason": "Por qué necesitas usar esta herramienta"
                            }}

                            - Si ya tienes información suficiente o se te dice que NO uses más herramientas, responde directamente
                            - Si no necesitas herramientas, simplemente responde normalmente"""
                                        
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user", 
            "content": user_message
        })
        
        # Primera respuesta de DeepSeek
        response = await self.chat_completion(messages, model, temperature, max_tokens)
        
        if not response:
            return None
            
        # Procesar herramientas de forma autónoma
        if self.tools_available and self._is_tool_request(response):
            return await self._process_tools_autonomously(response, messages, user_message, model, temperature, max_tokens, 10)
        
        return response
    
    async def _process_tools_autonomously(self, 
                                        response: str, 
                                        messages: List[Dict[str, str]], 
                                        original_question: str,
                                        model: str, 
                                        temperature: float, 
                                        max_tokens: int,
                                        max_iterations: int = 10) -> str:
        """
        Procesa todas las herramientas de forma completamente autónoma con múltiples iteraciones
        """
        print(f"{Colors.CYAN}🔧 DeepSeek eligió usar herramientas de GitHub...{Colors.ENDC}")
        
        current_response = response
        all_tool_results = []
        iteration = 0
        
        while iteration < max_iterations and self._is_tool_request(current_response):
            iteration += 1
            print(f"{Colors.CYAN}🔄 Iteración {iteration}/{max_iterations}{Colors.ENDC}")

            #imprimir respuesta actual
            print(f"{Colors.YELLOW}🤖 Respuesta actual de DeepSeek: {current_response}")
            
            # Extraer todas las solicitudes de herramientas
            tool_requests = self._parse_all_tool_requests(current_response)
            
            if not tool_requests:
                break
            
            # Ejecutar todas las herramientas secuencialmente
            iteration_results = []
            for i, tool_request in enumerate(tool_requests):
                print(f"{Colors.YELLOW}⚙️  Ejecutando herramienta {i+1}/{len(tool_requests)}: {tool_request['tool_name']}{Colors.ENDC}")
                
                result = await self.mcp_client.execute_tool_request(
                    tool_request["tool_name"], 
                    tool_request["arguments"]
                )
                
                # Limitar el tamaño del resultado para evitar timeouts
                result_str = json.dumps(result, indent=2)
                if len(result_str) > 5000:  # Truncar resultados muy largos
                    result_str = result_str[:5000] + "\n... (resultado truncado por tamaño)"
                    result = {"truncated_result": result_str, "original_length": len(json.dumps(result))}
                
                # Usar el LLM para determinar si es un error o éxito
                is_error = await self._llm_evaluate_result(tool_request, result)
                
                if not is_error:
                    print(f"{Colors.GREEN}✅ Resultado de {tool_request['tool_name']}: {result_str}{Colors.ENDC}")
                else:
                    print(f"{Colors.RED}💥 Error detectado por LLM en {tool_request['tool_name']}: {result_str}{Colors.ENDC}")
                
                iteration_results.append({
                    "tool": tool_request["tool_name"],
                    "arguments": tool_request["arguments"],
                    "result": result,
                    "has_error": is_error
                })
            
            all_tool_results.extend(iteration_results)
            
            # Verificar si hay errores en esta iteración
            errors_found = [r for r in iteration_results if r.get("has_error", False)]
            successful_results = [r for r in iteration_results if not r.get("has_error", False)]
            
            # Continuar hasta el máximo de iteraciones o hasta que DeepSeek decida parar
            # Crear contexto simplificado para la siguiente iteración
            if errors_found and iteration < max_iterations:
                # Hay errores, pedirle al LLM que los solucione
                error_context = ""
                for error in errors_found:
                    error_context += f"- Error en '{error['tool']}' con argumentos {error['arguments']}: {error['result']}\n"
                
                success_context = ""
                if successful_results:
                    success_context = f"Herramientas exitosas: {', '.join([r['tool'] for r in successful_results])}\n"
                
                follow_up_messages = messages.copy()
                follow_up_messages.append({
                    "role": "assistant",
                    "content": f"He ejecutado herramientas en la iteración {iteration} pero encontré algunos errores."
                })
                follow_up_messages.append({
                    "role": "user", 
                    "content": f"""ERRORES DETECTADOS POR IA:
                    {error_context}
                    {success_context}
                    Pregunta original: {original_question}

                    Los errores anteriores fueron identificados automáticamente. Analiza cada error específico y:

                    1. Si faltan parámetros requeridos (como "missing required parameter: path"), agrega los parámetros faltantes
                    2. Si hay problemas de formato o sintaxis, corrige la estructura de la llamada
                    3. Si es un error de permisos/acceso, intenta una herramienta alternativa 
                    4. Si es un error de nombre de repositorio/usuario, verifica el nombre correcto
                    5. Si es un error de API, intenta con una consulta más específica

                    EJEMPLOS DE CORRECCIÓN:
                    - Si falta "path": agrega "path": "/" para ver el directorio raíz
                    - Si falta "owner"/"repo": usa search_repositories primero para encontrar el repositorio correcto
                    - Si hay error 404: verifica que el repositorio/usuario existe

                    IMPORTANTE: 
                    - Aprende específicamente de cada error y corrígelo
                    - Usa el formato JSON para nuevas herramientas
                    - Si ya tienes suficiente información exitosa, responde "LISTO"
                    - No repitas exactamente los mismos errores

                    ¿Qué herramienta vas a usar para solucionar estos errores específicos o ya puedes responder?"""
                })
                
                print(f"{Colors.RED}🔍 Enviando errores a DeepSeek para que los solucione...{Colors.ENDC}")
                current_response = await self.chat_completion(follow_up_messages, model, temperature, 700)
                
            elif successful_results:
                # Solo hubo resultados exitosos, continuar normalmente
                iteration_context = f"Ejecuté {len(iteration_results)} herramienta(s): {', '.join([r['tool'] for r in iteration_results])}"
                
                follow_up_messages = messages.copy()
                follow_up_messages.append({
                    "role": "assistant",
                    "content": f"He ejecutado las herramientas de la iteración {iteration}."
                })
                follow_up_messages.append({
                    "role": "user",
                    "content": f"""Resultados: {iteration_context}

                    Pregunta original: {original_question}

                    ¿Necesitas ejecutar más herramientas específicas, o ya puedes responder?
                    Si necesitas otra herramienta, úsala con formato JSON.
                    Si ya tienes suficiente, responde "LISTO"."""
                })
                
                print(f"{Colors.YELLOW}🤔 Consultando a DeepSeek si necesita más herramientas...{Colors.ENDC}")
                current_response = await self.chat_completion(follow_up_messages, model, temperature, 500)
                
            else:
                # Solo hubo errores, intentar que el LLM encuentre una solución alternativa
                error_context = "Todas las herramientas fallaron:\n"
                for error in errors_found:
                    error_context += f"- {error['tool']}: {error['result']}\n"
                
                follow_up_messages = messages.copy()
                follow_up_messages.append({
                    "role": "user",
                    "content": f"""{error_context}

                    Pregunta original: {original_question}

                    Todas las herramientas anteriores fallaron. Por favor:
                    1. Analiza los errores y encuentra una estrategia diferente
                    2. Usa herramientas alternativas o con parámetros diferentes
                    3. Si crees que puedes responder parcialmente con información general, responde "LISTO"
                    
                    ¿Qué herramienta alternativa vas a probar?"""
                })
                
                print(f"{Colors.RED}🚨 Todas las herramientas fallaron, pidiendo estrategia alternativa...{Colors.ENDC}")
                current_response = await self.chat_completion(follow_up_messages, model, temperature, 600)
            
            if not current_response or "LISTO" in current_response.upper():
                break
            
            # Si hay timeout en la respuesta, intentar una vez más con contexto simplificado
            if current_response is None and iteration < max_iterations:
                print(f"{Colors.WARNING}⚠️  Timeout detectado, intentando con contexto simplificado...{Colors.ENDC}")
                simple_messages = [
                    {
                        "role": "user",
                        "content": f"""Pregunta original: {original_question}
                        
Iteración {iteration} completada. ¿Necesitas más herramientas específicas (formato JSON) o puedes responder "LISTO"?"""
                    }
                ]
                current_response = await self.chat_completion(simple_messages, model, 0.3, 300)
                
                if not current_response:
                    print(f"{Colors.RED}💥 Timeout persistente, finalizando iteraciones...{Colors.ENDC}")
                    break
            
            # Añadir delay entre iteraciones para evitar rate limiting
            await asyncio.sleep(2)
        
        # Crear respuesta final con todos los resultados (limitado)
        if all_tool_results:
            # Separar resultados exitosos de errores
            successful_tools = [r for r in all_tool_results if not r.get("has_error", False)]
            failed_tools = [r for r in all_tool_results if r.get("has_error", False)]
            
            # Crear un resumen conciso de los resultados
            results_summary = f"Herramientas ejecutadas: {len(all_tool_results)} (✅ {len(successful_tools)} exitosas, ❌ {len(failed_tools)} fallidas)\n"
            
            # Mostrar resultados exitosos
            if successful_tools:
                results_summary += "\n🟢 RESULTADOS EXITOSOS:\n"
                for i, tool_result in enumerate(successful_tools[:3]):  # Solo mostrar las primeras 3
                    result_preview = str(tool_result['result'])[:1000]  # Limitar cada resultado
                    results_summary += f"{i+1}. {tool_result['tool']}: {result_preview}...\n"
            
            # Mostrar errores si los hay
            if failed_tools:
                results_summary += "\n🔴 ERRORES ENCONTRADOS:\n"
                for i, tool_result in enumerate(failed_tools[:2]):  # Solo mostrar los primeros 2 errores
                    error_preview = str(tool_result['result'])[:500]  # Limitar cada error
                    results_summary += f"{i+1}. {tool_result['tool']}: {error_preview}...\n"
            
            # Mensaje final optimizado
            final_messages = messages.copy()
            final_context = f"""Basándote en estos resultados de GitHub:

{results_summary}

Responde la pregunta original: {original_question}

INSTRUCCIONES:
- Si tienes resultados exitosos, úsalos para responder completamente
- Si solo tienes errores, explica qué se intentó hacer y por qué no funcionó
- Si tienes una mezcla, responde con la información disponible y menciona las limitaciones
- Sé conciso pero completo
- Proporciona información relevante basada en los resultados obtenidos

IMPORTANTE: NO uses más herramientas. Responde directamente con la información disponible."""
            
            final_messages.append({
                "role": "user",
                "content": final_context
            })
            
            # Respuesta final con contexto reducido
            print(f"{Colors.CYAN}💭 Generando respuesta final (✅ {len(successful_tools)} éxitos, ❌ {len(failed_tools)} errores)...{Colors.ENDC}")
            final_response = await self.chat_completion(final_messages, model, temperature, 1500)
            
            if final_response:
                # Asegurar que no se procesen más herramientas en la respuesta final
                if self._is_tool_request(final_response):
                    # Si DeepSeek aún quiere usar herramientas, dar una respuesta basada en los datos ya obtenidos
                    if successful_tools:
                        return f"""Basándome en los {len(successful_tools)} resultados exitosos de GitHub obtenidos, he ejecutado las herramientas necesarias. Los resultados incluyen información relevante para responder tu consulta. {len(failed_tools)} herramientas fallaron pero se obtuvieron datos suficientes del análisis."""
                    else:
                        return f"""Se intentaron ejecutar {len(all_tool_results)} herramientas de GitHub, pero todas fallaron con errores. Los errores más comunes fueron problemas de acceso, parámetros incorrectos o recursos no encontrados. Es posible que necesites verificar los nombres de repositorios, usuarios o permisos de acceso."""
                return final_response
            else:
                if successful_tools:
                    return f"Ejecuté {len(successful_tools)} herramientas de GitHub exitosamente (y {len(failed_tools)} fallaron), pero hubo un timeout al generar la respuesta final. Los resultados exitosos están disponibles."
                else:
                    return f"Se intentaron ejecutar {len(all_tool_results)} herramientas de GitHub pero todas fallaron. Los errores incluyen problemas de acceso, parámetros incorrectos o recursos no encontrados."
        
        return current_response or "No se pudieron ejecutar las herramientas por timeout."
    
    def _is_tool_request(self, response: str) -> bool:
        """Verifica si la respuesta contiene una solicitud de herramienta"""
        try:
            # Buscar tanto formato normal como bloques de código
            return ("tool_request" in response and "{" in response and "}" in response) or "```json" in response
        except:
            return False
    
    def _parse_tool_request(self, response: str) -> Optional[Dict[str, Any]]:
        """Extrae la solicitud de herramienta de la respuesta"""
        try:
            # Buscar el JSON en la respuesta
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                parsed = json.loads(json_str)
                if "tool_request" in parsed:
                    return parsed["tool_request"]
        except:
            pass
        return None
    
    def _parse_all_tool_requests(self, response: str) -> List[Dict[str, Any]]:
        """Extrae todas las solicitudes de herramientas de la respuesta"""
        tool_requests = []
        
        try:
            # Método 1: Buscar bloques de código JSON
            lines = response.split('\n')
            current_json = ""
            in_json_block = False
            
            for line in lines:
                if '```json' in line.lower():
                    in_json_block = True
                    current_json = ""
                    continue
                elif '```' in line and in_json_block:
                    in_json_block = False
                    # Procesar el JSON acumulado
                    if current_json.strip():
                        try:
                            parsed = json.loads(current_json.strip())
                            if "tool_request" in parsed:
                                tool_requests.append(parsed["tool_request"])
                        except json.JSONDecodeError:
                            pass
                    current_json = ""
                elif in_json_block:
                    current_json += line + "\n"
            
            # Método 2: Buscar objetos JSON completos separados (como en el terminal)
            if not tool_requests:
                # Usar regex para encontrar objetos JSON completos
                json_pattern = r'\{(?:[^{}]|{[^{}]*})*\}'
                matches = re.findall(json_pattern, response, re.DOTALL)
                
                for match in matches:
                    try:
                        parsed = json.loads(match)
                        if "tool_request" in parsed:
                            tool_requests.append(parsed["tool_request"])
                    except json.JSONDecodeError:
                        continue
            
            # Método 3: Fallback al método original
            if not tool_requests:
                tool_request = self._parse_tool_request(response)
                if tool_request:
                    tool_requests.append(tool_request)
                    
        except Exception as e:
            print(f"{Colors.WARNING}⚠️  Error parseando herramientas: {e}{Colors.ENDC}")
        
        return tool_requests
    
    async def _llm_evaluate_result(self, tool_request: Dict[str, Any], result: Any) -> bool:
        """
        Usa el LLM para determinar si el resultado de una herramienta es un error o éxito
        
        Args:
            tool_request: La solicitud de herramienta original
            result: El resultado obtenido
            
        Returns:
            True si es un error, False si es éxito
        """
        try:
            # Crear contexto para evaluación
            evaluation_prompt = f"""Analiza este resultado de herramienta GitHub y determina si es un ERROR o ÉXITO:

HERRAMIENTA USADA: {tool_request['tool_name']}
ARGUMENTOS: {json.dumps(tool_request['arguments'], indent=2)}
RESULTADO: {json.dumps(result, indent=2)[:1000]}

CRITERIOS:
- ERROR si: contiene mensajes de error, parámetros faltantes, recursos no encontrados, permisos denegados, formato incorrecto
- ÉXITO si: devuelve datos válidos, listas, objetos con información útil

Responde SOLO con una palabra: "ERROR" o "EXITO" """

            messages = [{"role": "user", "content": evaluation_prompt}]
            
            # Usar temperatura baja para respuesta consistente
            evaluation_response = await self.chat_completion(messages, temperature=0.1, max_tokens=10)
            
            if evaluation_response:
                response_clean = evaluation_response.strip().upper()
                is_error = "ERROR" in response_clean
                
                print(f"{Colors.CYAN}🔍 LLM evaluó resultado como: {'ERROR' if is_error else 'ÉXITO'}{Colors.ENDC}")
                return is_error
            else:
                # Fallback a detección manual si el LLM no responde
                print(f"{Colors.WARNING}⚠️  LLM no pudo evaluar, usando detección manual{Colors.ENDC}")
                if isinstance(result, dict):
                    return "error" in result or "missing" in str(result).lower() or "not found" in str(result).lower()
                return False
                
        except Exception as e:
            print(f"{Colors.WARNING}⚠️  Error en evaluación LLM, usando fallback: {e}{Colors.ENDC}")
            # Fallback mejorado
            result_str = str(result).lower()
            error_indicators = ["error", "missing", "not found", "denied", "forbidden", "invalid", "failed", "unable"]
            return any(indicator in result_str for indicator in error_indicators)
