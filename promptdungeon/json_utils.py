from __future__ import annotations

import ast
import json
import re
from typing import Any, Dict


def _strip_code_fences(text: str) -> str:
    s = text.strip()
    if s.startswith("```") and s.endswith("```"):
        # Remove first and last fence block
        s = re.sub(r"^```[a-zA-Z0-9_-]*\n", "", s)
        if s.endswith("```"):
            s = s[: -3]
    return s.strip()


def _extract_braced(text: str) -> str:
    # Extract the largest balanced {...} region
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and start < end:
        return text[start : end + 1]
    return text


def coerce_json(data: Any) -> Dict[str, Any]:
    """Coerce an LLM response into a JSON object.

    Strategy:
    - If it's already a dict, return it.
    - Try json.loads directly.
    - Strip code fences and extract the innermost {...}.
    - Try json.loads again.
    - Try ast.literal_eval to handle Python-like dicts.
    - As a last resort, return a dict with the text as narration.
    """
    if isinstance(data, dict):
        return data

    if not isinstance(data, str):
        return {"narration": str(data)}

    s = data.strip()

    # First, try strict JSON
    try:
        return json.loads(s)
    except Exception:
        pass

    # Remove code fences and extract brace block
    s2 = _strip_code_fences(s)
    s2 = _extract_braced(s2)

    try:
        return json.loads(s2)
    except Exception:
        pass

    # Heuristic: replace single quotes with double quotes for keys/strings (best-effort)
    # and fix common literals.
    s3 = s2
    # Replace unquoted keys like: key: value -> "key": value
    s3 = re.sub(r"(?m)(\{|,|\s)([A-Za-z_][A-Za-z0-9_\-]*)\s*:\s", r'\1"\2": ', s3)
    # Replace python literals with JSON ones
    s3 = s3.replace("None", "null").replace("True", "true").replace("False", "false")
    # Remove trailing commas before closing braces/brackets
    s3 = re.sub(r",\s*(?=[}\]])", "", s3)
    # Try to ensure quotes are double quotes for values too (best-effort)
    s3_try = s3
    try:
        return json.loads(s3_try)
    except Exception:
        pass

    # Aggressive fallback: convert all single quotes to double quotes
    s4 = s3.replace("'", '"')
    # Remove trailing commas again just in case
    s4 = re.sub(r",\s*(?=[}\]])", "", s4)
    try:
        return json.loads(s4)
    except Exception:
        pass

    # Try Python literal eval as a last parsing attempt
    for candidate in (s4, s3, s2):
        try:
            obj = ast.literal_eval(candidate)
            if isinstance(obj, dict):
                return obj  # type: ignore[return-value]
        except Exception:
            pass

    # Fallback - return stripped text as narration
    return {"narration": _strip_code_fences(s)}
