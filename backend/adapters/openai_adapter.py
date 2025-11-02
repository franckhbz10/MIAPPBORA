"""
Adaptador para OpenAI API
Permite generar respuestas usando modelos de OpenAI (GPT-4o-mini, GPT-4o, etc.)
"""

import logging
from typing import List, Dict, Optional
from openai import AsyncOpenAI, OpenAIError, APITimeoutError, RateLimitError
from config.settings import settings

logger = logging.getLogger(__name__)


class OpenAIAdapter:
    """
    Adaptador para generar respuestas usando la API de OpenAI
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
        base_url: Optional[str] = None,
        organization: Optional[str] = None,
    ):
        """
        Inicializa el adaptador de OpenAI
        
        Args:
            api_key: API key de OpenAI (si no se provee, usa settings.OPENAI_API_KEY)
            model: Modelo a utilizar (default: settings.OPENAI_MODEL)
            temperature: Temperatura de generación (default: settings.OPENAI_TEMPERATURE)
            max_tokens: Máximo de tokens en la respuesta (default: settings.OPENAI_MAX_TOKENS)
            timeout: Timeout en segundos (default: settings.OPENAI_TIMEOUT)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.temperature = temperature if temperature is not None else settings.OPENAI_TEMPERATURE
        self.max_tokens = max_tokens or settings.OPENAI_MAX_TOKENS
        self.timeout = timeout or settings.OPENAI_TIMEOUT
        self.base_url = base_url or settings.OPENAI_BASE_URL
        self.organization = organization or settings.OPENAI_ORG
        
        if not self.api_key:
            logger.warning("⚠️ OPENAI_API_KEY no configurada. El adaptador no funcionará.")
            self.client = None
        else:
            client_kwargs = {
                "api_key": self.api_key,
                "timeout": self.timeout,
            }
            if self.base_url:
                client_kwargs["base_url"] = self.base_url
            if self.organization:
                client_kwargs["organization"] = self.organization

            self.client = AsyncOpenAI(**client_kwargs)
            logger.info(f"✅ OpenAI adapter inicializado con modelo: {self.model}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Genera una respuesta usando la API de Chat Completions (OpenAI)

        Args:
            messages: Lista de mensajes (role/content) en formato OpenAI
            temperature: Temperatura de generación (override del default)
            max_tokens: Máximo de tokens de salida (override del default)
            **kwargs: Parámetros adicionales para chat.completions.create

        Returns:
            str: Respuesta generada por el modelo

        Raises:
            ValueError: Si el cliente no está inicializado (falta API key)
            OpenAIError: Si hay un error en la API de OpenAI
        """
        if not self.client:
            raise ValueError("OpenAI client no inicializado. Verifica OPENAI_API_KEY en .env")

        try:
            # Parámetros finales (con overrides)
            final_temperature = temperature if temperature is not None else self.temperature
            final_max_tokens = max_tokens if max_tokens is not None else self.max_tokens

            logger.info(
                f"🤖 Llamando a OpenAI Chat Completions API ({self.model})..."
            )
            logger.debug(f"   Temperature: {final_temperature}, Max tokens: {final_max_tokens}")
            logger.debug(f"   Messages: {len(messages)} mensajes")

            # Llamada a la API estándar de Chat Completions
            # Nota: Algunos modelos nuevos requieren 'max_completion_tokens' en vez de 'max_tokens'
            completion_params = {
                "model": self.model,
                "messages": messages,
                "temperature": final_temperature,
            }
            
            # Usar el parámetro correcto según el modelo
            if final_max_tokens is not None:
                # gpt-4o y posteriores requieren max_completion_tokens
                if "gpt-4o" in self.model or "gpt-5" in self.model:
                    completion_params["max_completion_tokens"] = final_max_tokens
                else:
                    completion_params["max_tokens"] = final_max_tokens
            
            response = await self.client.chat.completions.create(
                **completion_params,
                **kwargs,
            )

            # Extraer el contenido de la respuesta
            if not response.choices or len(response.choices) == 0:
                logger.error("❌ OpenAI no devolvió choices en la respuesta")
                raise OpenAIError("La respuesta de OpenAI no contenía choices")

            answer = response.choices[0].message.content
            
            if not answer or not answer.strip():
                logger.error("❌ OpenAI devolvió una respuesta vacía")
                raise OpenAIError("La respuesta de OpenAI no contenía texto utilizable")

            # Log de uso de tokens
            if hasattr(response, 'usage') and response.usage:
                logger.info(
                    f"✅ OpenAI response | tokens: in={response.usage.prompt_tokens} "
                    f"out={response.usage.completion_tokens} total={response.usage.total_tokens}"
                )

            logger.info(f"✅ Respuesta generada ({len(answer)} chars): {answer[:100]}...")
            return answer.strip()

        except APITimeoutError as e:
            logger.error(f"⏱️ Timeout en OpenAI API: {e}")
            raise OpenAIError(f"Timeout al contactar OpenAI: {str(e)}")
        except RateLimitError as e:
            logger.error(f"🚫 Rate limit excedido en OpenAI: {e}")
            raise OpenAIError(f"Rate limit excedido: {str(e)}")
        except OpenAIError as e:
            logger.error(f"❌ Error de OpenAI API: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error inesperado en chat_completion: {e}", exc_info=True)
            raise OpenAIError(f"Error inesperado: {str(e)}")

    """
    # ============================================================================
    # CÓDIGO LEGACY COMENTADO: Responses API (solo para gpt-5 reasoning models)
    # ============================================================================
    # Este código está comentado porque:
    # 1. Los modelos estándar (gpt-4o-mini, gpt-3.5-turbo) usan Chat Completions API
    # 2. Solo modelos gpt-5-* reasoning soportan Responses API
    # 3. El código anterior ya maneja Chat Completions correctamente
    # ============================================================================
    
        try:
            # Soporte opcional para depuración: devolver respuesta cruda
            return_raw: bool = bool(kwargs.pop("return_raw", False))
            auto_expand_tokens: bool = bool(kwargs.pop("auto_expand_tokens", True))

            # Parámetros finales (con overrides)
            final_temperature = temperature if temperature is not None else self.temperature
            final_max_tokens = max_tokens if max_tokens is not None else self.max_tokens

            # Construir 'instructions' (primer system) y un único input de texto
            instructions: Optional[str] = None
            text_parts: List[str] = []
            for m in messages:
                role = m.get("role", "user")
                content = m.get("content", "")
                if role == "system" and instructions is None and isinstance(content, str):
                    instructions = content
                    continue
                # Representación simple de chat como texto plano
                role_tag = "USER" if role == "user" else ("ASSISTANT" if role == "assistant" else role.upper())
                text_parts.append(f"{role_tag}: {content}")

            final_input_text = "\n\n".join(text_parts) if text_parts else ""

            logger.info(
                f"🤖 Llamando a OpenAI Responses API ({self.model}) con input string de longitud {len(final_input_text)}..."
            )
            logger.debug(
                f"   Max Output Tokens: {final_max_tokens} (temperature omitido por compatibilidad)"
            )
            logger.debug(f"   Instructions: {instructions[:200] if instructions else 'None'}...")
            logger.debug(f"   Input text preview: {final_input_text[:300]}...")

            # Llamada a la API (Responses)
            request_kwargs = {
                "model": self.model,
                "input": final_input_text,
                "instructions": instructions,
                # Algunos modelos no soportan 'temperature' en Responses API
                "max_output_tokens": final_max_tokens,
            }
            # Para modelos reasoning (gpt-5*), reducir esfuerzo para liberar tokens a la salida visible
            if "gpt-5" in (self.model or "") and "reasoning" not in kwargs:
                request_kwargs["reasoning"] = {"effort": "low"}

            logger.debug(f"🔍 DEBUG request_kwargs: {request_kwargs}")

            response = await self.client.responses.create(
                **request_kwargs,
                **kwargs,
            )

            # Extraer el contenido de la respuesta
            answer: Optional[str] = None
            # DEBUG: Log respuesta cruda completa
            try:
                if hasattr(response, "model_dump"):
                    raw_response = response.model_dump()
                    logger.info(f"🔍 DEBUG OpenAI raw response: {raw_response}")
                else:
                    logger.info(f"🔍 DEBUG OpenAI response type: {type(response)}, dir: {dir(response)}")
            except Exception as e:
                logger.error(f"❌ Error dumping response: {e}")

            # 1) Atajo del SDK
            try:
                if hasattr(response, "output_text") and response.output_text:
                    answer = str(response.output_text).strip()
                    logger.info(f"✅ Respuesta extraída vía output_text: {answer[:100]}")
            except Exception as e:
                logger.debug(f"No hay output_text: {e}")
                answer = None

            # 2) Recorrido robusto de estructura output
            if not answer:
                try:
                    outputs = getattr(response, "output", None)
                    if outputs is None and hasattr(response, "model_dump"):
                        # Intentar volcar a dict si es pydantic
                        dumped = response.model_dump()  # type: ignore[attr-defined]
                        outputs = dumped.get("output")
                        logger.info(f"🔍 DEBUG outputs from model_dump: {outputs}")
                    texts: List[str] = []

                    def get_val(o, key):
                        return o.get(key) if isinstance(o, dict) else getattr(o, key, None)

                    if outputs:
                        for item in outputs:
                            itype = get_val(item, "type")
                            logger.info(f"🔍 DEBUG output item type: {itype}")
                            if itype == "message":
                                contents = get_val(item, "content") or []
                                logger.info(f"🔍 DEBUG message contents: {contents}")
                                for c in contents:
                                    ctype = get_val(c, "type")
                                    logger.info(f"🔍 DEBUG content type: {ctype}")
                                    if ctype in ("output_text", "text"):
                                        val = get_val(c, "text")
                                        if isinstance(val, str):
                                            texts.append(val)
                                            logger.info(f"✅ Texto encontrado: {val[:100]}")
                    answer = "\n".join(texts).strip() if texts else None
                    if answer:
                        logger.info(f"✅ Respuesta extraída vía output structure: {answer[:100]}")
                    else:
                        logger.warning("⚠️ No se encontró texto en la estructura output")
                except Exception as e:
                    logger.error(f"❌ Error en parsing de output: {e}")
                    answer = None

            # Log de uso de tokens (estructura nueva). En Responses API puede venir ausente.
            input_tokens = output_tokens = total_tokens = None
            try:
                usage = getattr(response, "usage", None)
                if usage is None and hasattr(response, "model_dump"):
                    dumped = response.model_dump()  # type: ignore[attr-defined]
                    usage = dumped.get("usage")
                if usage:
                    if isinstance(usage, dict):
                        input_tokens = usage.get("input_tokens") or usage.get("prompt_tokens")
                        output_tokens = usage.get("output_tokens") or usage.get("completion_tokens")
                        total_tokens = usage.get("total_tokens")
                    else:
                        input_tokens = getattr(usage, "input_tokens", None) or getattr(usage, "prompt_tokens", None)
                        output_tokens = getattr(usage, "output_tokens", None) or getattr(usage, "completion_tokens", None)
                        total_tokens = getattr(usage, "total_tokens", None)
            except Exception:
                pass

            # Información de estado y resumen de la respuesta para depuración
            try:
                status = getattr(response, "status", None)
                reason = None
                inc = getattr(response, "incomplete_details", None)
                if inc is None and hasattr(response, "model_dump"):
                    dumped = response.model_dump()  # type: ignore[attr-defined]
                    inc = dumped.get("incomplete_details")
                    status = status or dumped.get("status")
                if isinstance(inc, dict):
                    reason = inc.get("reason")
                else:
                    reason = getattr(inc, "reason", None)
                preview = (answer or "")[:160].replace("\n", " ")
                logger.info(
                    "✅ OpenAI response recibida | status=%s reason=%s | usage: in=%s out=%s total=%s | preview: %s",
                    status or "completed",
                    reason or "-",
                    input_tokens if input_tokens is not None else "-",
                    output_tokens if output_tokens is not None else "-",
                    total_tokens if total_tokens is not None else "-",
                    preview or "<vacía>",
                )
            except Exception:
                pass

            # Preparar volcado crudo para depuración si se solicita
            raw_dump = None
            if return_raw:
                try:
                    if hasattr(response, "model_dump_json"):
                        raw_dump = response.model_dump_json()  # type: ignore[attr-defined]
                    elif hasattr(response, "model_dump"):
                        raw_dump = response.model_dump()  # type: ignore[attr-defined]
                    elif isinstance(response, dict):
                        raw_dump = response
                    else:
                        raw_dump = str(response)
                except Exception:
                    raw_dump = str(response)

            # Si no hay texto y el modelo se quedó sin tokens por razonamiento, reintentar con más max_output_tokens
            if not answer and auto_expand_tokens:
                try:
                    # Obtener estado y razón de incompletitud
                    status = getattr(response, "status", None)
                    reason = None
                    inc = getattr(response, "incomplete_details", None)
                    if inc is None and hasattr(response, "model_dump"):
                        dumped = response.model_dump()  # type: ignore[attr-defined]
                        inc = dumped.get("incomplete_details")
                        status = status or dumped.get("status")
                    if isinstance(inc, dict):
                        reason = inc.get("reason")
                    else:
                        reason = getattr(inc, "reason", None)

                    if (status == "incomplete" and reason == "max_output_tokens") or (answer is None and usage):
                        # Subir presupuesto de salida con un salto significativo (x4) y mínimo 1024
                        new_max = min(max((final_max_tokens or 0) * 4, 1024), self.max_tokens or (final_max_tokens or 1024))
                        if new_max and (final_max_tokens is None or new_max > final_max_tokens):
                            logger.info(f"🔁 Reintentando con max_output_tokens={new_max} (ampliado por falta de tokens)")
                            request_kwargs["max_output_tokens"] = new_max
                            response = await self.client.responses.create(
                                **request_kwargs,
                                **kwargs,
                            )
                            # Re-extraer texto
                            answer = None
                            try:
                                if hasattr(response, "output_text") and response.output_text:
                                    answer = str(response.output_text).strip()
                            except Exception:
                                answer = None
                            if not answer:
                                try:
                                    outputs = getattr(response, "output", None)
                                    if outputs is None and hasattr(response, "model_dump"):
                                        dumped = response.model_dump()  # type: ignore[attr-defined]
                                        outputs = dumped.get("output")
                                    texts = []
                                    def get_val(o, key):
                                        return o.get(key) if isinstance(o, dict) else getattr(o, key, None)
                                    if outputs:
                                        for item in outputs:
                                            itype = get_val(item, "type")
                                            if itype == "message":
                                                contents = get_val(item, "content") or []
                                                for c in contents:
                                                    ctype = get_val(c, "type")
                                                    if ctype in ("output_text", "text"):
                                                        val = get_val(c, "text")
                                                        if isinstance(val, str):
                                                            texts.append(val)
                                    answer = "\n".join(texts).strip() if texts else None
                                except Exception:
                                    answer = None
                except Exception as _:
                    pass

            if return_raw:
                return {"text": answer, "raw": raw_dump}

            if not answer:
                raise OpenAIError("La respuesta de OpenAI no contenía texto utilizable")

            return answer

        except APITimeoutError as e:
            logger.error(f"⏱️ Timeout en OpenAI API: {e}")
            raise OpenAIError(f"Timeout al llamar a OpenAI API: {str(e)}")

        except RateLimitError as e:
            logger.error(f"🚫 Rate limit excedido en OpenAI API: {e}")
            raise OpenAIError(f"Rate limit excedido: {str(e)}")

        except OpenAIError as e:
            logger.error(f"❌ Error en OpenAI API: {e}")
            raise

        except Exception as e:
            logger.error(f"💥 Error inesperado en OpenAI adapter: {e}", exc_info=True)
            raise OpenAIError(f"Error inesperado: {str(e)}")
    """
    # FIN DEL CÓDIGO LEGACY COMENTADO
    # ============================================================================

    async def health_check(self) -> Dict[str, str]:
        """
        Verifica que el adaptador esté configurado correctamente
        
        Returns:
            Dict con el estado de salud del adaptador
        """
        if not self.client:
            return {
                "status": "unhealthy",
                "error": "OPENAI_API_KEY no configurada",
                "model": self.model
            }
        
        try:
            # Intenta hacer una llamada mínima usando Responses API
            await self.client.responses.create(
                model=self.model,
                input="ping",
                # Responses API requiere un mínimo de 16 tokens de salida
                max_output_tokens=16,
            )
            return {
                "status": "healthy",
                "model": self.model,
                "temperature": str(self.temperature),
                "max_tokens": str(self.max_tokens),
                "base_url": self.base_url or "default",
                "organization": self.organization or "default",
            }
        except Exception as e:
            logger.error(f"❌ Health check falló: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "model": self.model
            }

    async def list_models(self) -> Dict[str, object]:
        """Lista modelos disponibles para este API key/base URL."""
        if not self.client:
            raise ValueError("OpenAI client no inicializado")
        try:
            models = await self.client.models.list()
            ids = [m.id for m in models.data]
            return {"count": len(ids), "models": ids}
        except Exception as e:
            logger.error(f"❌ No se pudo listar modelos: {e}")
            raise


# Singleton para reutilizar el adaptador
_openai_adapter_instance: Optional[OpenAIAdapter] = None


def get_openai_adapter() -> OpenAIAdapter:
    """
    Obtiene la instancia singleton del adaptador de OpenAI
    """
    global _openai_adapter_instance
    if _openai_adapter_instance is None:
        _openai_adapter_instance = OpenAIAdapter()
    return _openai_adapter_instance
