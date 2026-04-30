import os
import time
from typing import Dict, Any, Tuple
import tenacity
from tenacity import retry, stop_after_attempt, wait_exponential, wait_fixed, retry_if_exception_type
from dotenv import load_dotenv

import openai
from openai import OpenAI
import anthropic

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import google.generativeai as genai

load_dotenv()

class LLMProviderError(Exception): pass
class RateLimitError(LLMProviderError): pass
class ServerError(LLMProviderError): pass
class AuthError(LLMProviderError): pass
class TokenLimitError(LLMProviderError): pass
class EmptyResponseError(LLMProviderError): pass
class NetworkTimeoutError(LLMProviderError): pass

class LLMProvider:
    def __init__(self, model_id: str, temperature: float = 0.0, top_p: float = 1.0, max_tokens: int = 4096):
        self.model_id = model_id
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens

    def generate(self, prompt: str) -> Tuple[str, float, int, int]:
        """
        Returns: (response_text, api_time_s, input_tokens, output_tokens)
        Raises specific LLMProviderError subclasses on failure.
        """
        raise NotImplementedError()

class OpenAIProvider(LLMProvider):
    def __init__(self, model_id: str, temperature: float = 0.0, top_p: float = 1.0, max_tokens: int = 4096, api_key: str = None, base_url: str = None):
        super().__init__(model_id, temperature, top_p, max_tokens)
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise AuthError("OpenAI API key missing")
        self.client = OpenAI(api_key=key, base_url=base_url)

    def generate(self, prompt: str) -> Tuple[str, float, int, int]:
        start_time = time.time()
        try:
            # Note: For deep reasoning models (e.g. o-series, deepseek-reasoner), 
            # temperature/top_p might need to be omitted or set to default if the API rejects it.
            # We'll pass them but fall back if needed, or assume the user config handles it.
            # deepseek-reasoner supports standard chat completions.
            
            kwargs = {
                "model": self.model_id,
                "messages": [{"role": "user", "content": prompt}],
                "max_completion_tokens": self.max_tokens
            }
            
            # GPT-o models or DeepSeek reasoner might fail if temp is explicitly set to 0.0 sometimes,
            # but we follow strict protocol.
            if "o4" not in self.model_id and "reasoner" not in self.model_id:
                kwargs["temperature"] = self.temperature
                kwargs["top_p"] = self.top_p

            response = self.client.chat.completions.create(**kwargs)
            
            elapsed = time.time() - start_time
            content = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason if response.choices else None
            
            if not content or finish_reason != "stop":
                raise EmptyResponseError(f"Incomplete response returned from OpenAI/Compatible API. Finish reason: {finish_reason}")
                
            in_tokens = response.usage.prompt_tokens if response.usage else 0
            out_tokens = response.usage.completion_tokens if response.usage else 0
            
            return content, elapsed, in_tokens, out_tokens
            
        except openai.AuthenticationError as e:
            raise AuthError(str(e))
        except openai.RateLimitError as e:
            raise RateLimitError(str(e))
        except openai.InternalServerError as e:
            raise ServerError(str(e))
        except openai.APITimeoutError as e:
            raise NetworkTimeoutError(str(e))
        except openai.BadRequestError as e:
            if "token" in str(e).lower():
                raise TokenLimitError(str(e))
            raise LLMProviderError(str(e))
        except Exception as e:
            if isinstance(e, LLMProviderError):
                raise e
            raise LLMProviderError(str(e))

class DeepSeekProvider(OpenAIProvider):
    def __init__(self, model_id: str, temperature: float = 0.0, top_p: float = 1.0, max_tokens: int = 4096):
        super().__init__(
            model_id=model_id, 
            temperature=temperature, 
            top_p=top_p, 
            max_tokens=max_tokens, 
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com/v1"
        )

class AnthropicProvider(LLMProvider):
    def __init__(self, model_id: str, temperature: float = 0.0, top_p: float = 1.0, max_tokens: int = 4096):
        super().__init__(model_id, temperature, top_p, max_tokens)
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise AuthError("Anthropic API key missing")
        self.client = anthropic.Anthropic(api_key=key)

    def generate(self, prompt: str) -> Tuple[str, float, int, int]:
        start_time = time.time()
        try:
            response = self.client.messages.create(
                model=self.model_id,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=min(self.max_tokens, 4096),
                temperature=self.temperature
            )
            elapsed = time.time() - start_time
            content = response.content[0].text if response.content else ""
            stop_reason = getattr(response, 'stop_reason', None)
            
            if not content or stop_reason != "end_turn":
                raise EmptyResponseError(f"Incomplete response from Anthropic. Stop reason: {stop_reason}")
                
            in_tokens = response.usage.input_tokens
            out_tokens = response.usage.output_tokens
            
            return content, elapsed, in_tokens, out_tokens
            
        except anthropic.AuthenticationError as e:
            raise AuthError(str(e))
        except anthropic.RateLimitError as e:
            raise RateLimitError(str(e))
        except anthropic.InternalServerError as e:
            raise ServerError(str(e))
        except anthropic.APITimeoutError as e:
            raise NetworkTimeoutError(str(e))
        except anthropic.BadRequestError as e:
            if "token" in str(e).lower():
                raise TokenLimitError(str(e))
            raise LLMProviderError(str(e))
        except Exception as e:
            if isinstance(e, LLMProviderError):
                raise e
            raise LLMProviderError(str(e))

class GeminiProvider(LLMProvider):
    def __init__(self, model_id: str, temperature: float = 0.0, top_p: float = 1.0, max_tokens: int = 4096):
        super().__init__(model_id, temperature, top_p, max_tokens)
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise AuthError("Gemini API key missing")
        genai.configure(api_key=key)
        self.model = genai.GenerativeModel(
            model_name=self.model_id,
            generation_config=genai.types.GenerationConfig(
                temperature=self.temperature,
                top_p=self.top_p,
                max_output_tokens=self.max_tokens,
            )
        )

    def generate(self, prompt: str) -> Tuple[str, float, int, int]:
        start_time = time.time()
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    top_p=self.top_p,
                    max_output_tokens=self.max_tokens,
                )
            )
            elapsed = time.time() - start_time
            
            try:
                text = response.text
            except ValueError:
                if response.candidates and response.candidates[0].content.parts:
                    text = response.candidates[0].content.parts[0].text
                else:
                    text = ""
                    
            finish_reason = response.candidates[0].finish_reason if response.candidates else None
            is_stop = False
            if finish_reason is not None:
                if hasattr(finish_reason, 'name'):
                    if finish_reason.name == 'STOP': is_stop = True
                    elif finish_reason.name == 'MAX_TOKENS': raise TokenLimitError(f"Gemini max tokens reached. Text: {text[:100]}...")
                elif hasattr(finish_reason, 'value'):
                    if finish_reason.value == 1: is_stop = True
                    elif finish_reason.value == 2: raise TokenLimitError(f"Gemini max tokens reached. Text: {text[:100]}...")
                else:
                    if finish_reason == 1: is_stop = True
                    elif finish_reason == 2: raise TokenLimitError(f"Gemini max tokens reached. Text: {text[:100]}...")
                    
            if not text or not is_stop:
                raise EmptyResponseError(f"Incomplete/Empty response from Gemini. Finish reason: {finish_reason}")
                
            in_tokens = self.model.count_tokens(prompt).total_tokens
            out_tokens = self.model.count_tokens(text).total_tokens if text else 0
            
            return text, elapsed, in_tokens, out_tokens
            
        except Exception as e:
            if isinstance(e, LLMProviderError):
                raise e
            error_str = str(e).lower()
            if "api_key" in error_str or "unauthenticated" in error_str or "forbidden" in error_str:
                raise AuthError(str(e))
            if "429" in error_str or "quota" in error_str:
                raise RateLimitError(str(e))
            if "500" in error_str or "503" in error_str:
                raise ServerError(str(e))
            if "timeout" in error_str or "connection" in error_str or "connect" in error_str:
                raise NetworkTimeoutError(str(e))
            raise LLMProviderError(str(e))

def get_provider(provider_name: str, model_id: str, temp: float, top_p: float, max_tokens: int) -> LLMProvider:
    provider_name = provider_name.lower()
    if provider_name == "openai":
        return OpenAIProvider(model_id, temp, top_p, max_tokens)
    elif provider_name == "deepseek":
        return DeepSeekProvider(model_id, temp, top_p, max_tokens)
    elif provider_name == "anthropic":
        return AnthropicProvider(model_id, temp, top_p, max_tokens)
    elif provider_name == "google":
        return GeminiProvider(model_id, temp, top_p, max_tokens)
    else:
        raise ValueError(f"Unknown provider: {provider_name}")
