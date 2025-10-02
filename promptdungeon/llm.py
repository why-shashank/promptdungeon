from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

import httpx

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

try:
    import google.generativeai as genai  # type: ignore
except Exception:  # pragma: no cover
    genai = None  # type: ignore


Message = Dict[str, str]


class LLMProvider(ABC):
    @abstractmethod
    def complete(
        self, messages: List[Message], json_object: bool = False
    ) -> str:  # returns content
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set")
        if OpenAI is None:
            raise RuntimeError("openai package not installed")
        self.client = OpenAI(api_key=api_key)
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def complete(self, messages: List[Message], json_object: bool = False) -> str:
        # Prefer chat.completions with response_format for JSON enforcement when available
        try:
            kwargs = {}
            if json_object:
                kwargs["response_format"] = {"type": "json_object"}
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs,
            )
            content = resp.choices[0].message.content or ""
            return content
        except Exception:
            # Fallback to responses API if needed
            try:
                kwargs = {}
                if json_object:
                    kwargs["response_format"] = {"type": "json_object"}
                r = self.client.responses.create(
                    model=self.model,
                    input=messages,
                    **kwargs,
                )
                # Extract text content blocks
                parts = []
                for item in getattr(r, "output", []) or []:
                    if getattr(item, "type", None) == "message":
                        for c in getattr(item, "content", []) or []:
                            if getattr(c, "type", None) == "output_text":
                                parts.append(getattr(c, "text", ""))
                return "\n".join(parts).strip()
            except Exception as e:
                raise RuntimeError(f"OpenAI completion failed: {e}")


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY is not set")
        if genai is None:
            raise RuntimeError("google-generativeai package not installed")
        genai.configure(api_key=key)
        self.model_name = (
            model
            or os.getenv("GEMINI_MODEL")
            or os.getenv("LLM_MODEL")
            or "gemini-1.5-flash"
        )

    def complete(self, messages: List[Message], json_object: bool = False) -> str:
        system = (
            "\n".join([m["content"] for m in messages if m["role"] == "system"]) or ""
        )
        user = (
            "\n".join([m["content"] for m in messages if m["role"] != "system"]) or ""
        )
        generation_config = {}
        if json_object:
            # Hint the model to return strict JSON
            generation_config["response_mime_type"] = "application/json"
        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system or None,
                generation_config=generation_config or None,
            )
            resp = model.generate_content([user])
            text = getattr(resp, "text", None)
            if text is None and hasattr(resp, "candidates"):
                # Fallback extraction
                for cand in getattr(resp, "candidates", []) or []:
                    parts = []
                    for part in (
                        getattr(getattr(cand, "content", None), "parts", []) or []
                    ):
                        if hasattr(part, "text"):
                            parts.append(getattr(part, "text", ""))
                    if parts:
                        text = "\n".join(parts)
                        break
            return (text or "").strip()
        except Exception as e:
            raise RuntimeError(f"Gemini completion failed: {e}")


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = base_url or os.getenv(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        )
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.1:8b")

    def complete(self, messages: List[Message], json_object: bool = False) -> str:
        # Flatten messages into a single prompt with system header
        system = (
            "\n".join([m["content"] for m in messages if m["role"] == "system"]) or ""
        )
        user = (
            "\n".join([m["content"] for m in messages if m["role"] != "system"]) or ""
        )
        prompt = (system + "\n" + user).strip()
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            # Help nudge JSON; many Ollama models obey this prompt style well
            "options": {
                "temperature": 0.7,
            },
        }
        try:
            with httpx.Client(timeout=120) as client:
                r = client.post(f"{self.base_url}/api/generate", json=payload)
                r.raise_for_status()
                data = r.json()
                return data.get("response", "")
        except Exception as e:
            raise RuntimeError(f"Ollama completion failed: {e}")


def autodetect_provider(
    provider_hint: str = "auto", model_override: Optional[str] = None
) -> LLMProvider:
    hint = (provider_hint or "auto").lower()
    if hint == "openai":
        return OpenAIProvider(model=model_override)
    if hint == "ollama":
        return OllamaProvider(model=model_override)
    if hint == "gemini":
        return GeminiProvider(model=model_override)

    # auto
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIProvider(model=model_override)
    if os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
        return GeminiProvider(model=model_override)
    return OllamaProvider(model=model_override)
