import json
import re
import ast
import logging
from typing import Any, Dict, Optional, Tuple

from pydantic import BaseModel, ValidationError

from routers.command.models import COMMAND_MODEL_MAP

logger = logging.getLogger(__name__)


def sanitize_json_string(raw: str) -> str:
    if not raw or not raw.strip():
        return raw

    s = raw.strip()

    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return raw

    s = re.sub(r",\s*([}\]])", r"\1", s)

    s = re.sub(r"\bTrue\b", "true", s)
    s = re.sub(r"\bFalse\b", "false", s)
    s = re.sub(r"\bNone\b", "null", s)

    s = re.sub(r"(?<!\\)'(?=(?:[^\"\\]*(?:\\.|\"[^\"\\]*\")?)*$)", '"', s)

    s = re.sub(r"(\w+)(?=\s*:)", r'"\1"', s)

    s = re.sub(r",\s*([}\]])", r"\1", s)

    return s


def try_json_parse(raw: str) -> Tuple[Optional[Any], bool]:
    sanitized = sanitize_json_string(raw)
    try:
        result = json.loads(sanitized)
        logger.debug("JSON parsing succeeded after sanitization")
        return result, True
    except json.JSONDecodeError as e:
        logger.debug(f"JSON parsing failed after sanitization: {e}")
        return sanitized, False


def try_literal_eval(sanitized: str) -> Tuple[Optional[Any], bool]:
    try:
        result = ast.literal_eval(sanitized)
        logger.debug("ast.literal_eval fallback succeeded")
        return result, True
    except (ValueError, SyntaxError, MemoryError, RecursionError) as e:
        logger.warning(f"ast.literal_eval also failed: {e}")
        return None, False


def validate_structured_response(
    command: str, parsed_data: Any
) -> Dict[str, Any]:
    model_class = COMMAND_MODEL_MAP.get(command)
    if model_class is None:
        return {
            "valid": True,
            "data": parsed_data,
            "error": None,
        }

    try:
        if isinstance(parsed_data, dict):
            validated = model_class(**parsed_data)
        else:
            validated = model_class(**{list(model_class.__fields__.keys())[0]: parsed_data})

        return {
            "valid": True,
            "data": validated.dict(),
            "error": None,
        }
    except ValidationError as e:
        errors = e.errors()
        logger.error(f"Model validation failed for {command}: {errors}")
        return {
            "valid": False,
            "data": None,
            "error": errors,
        }


def parse_command_response(command: str, raw_response: str) -> Dict[str, Any]:
    if not raw_response:
        return {
            "success": False,
            "command": command,
            "error": "Empty response from device",
        }

    if command in ("runshell", "sendsms", "changewallpaper", "makecall"):
        parsed, json_ok = try_json_parse(raw_response)
        if json_ok:
            if isinstance(parsed, str):
                lines = [line.strip() for line in parsed.split("\n") if line.strip()]
            elif isinstance(parsed, list):
                lines = [str(item) for item in parsed]
            elif isinstance(parsed, dict):
                lines = [f"{k}: {v}" for k, v in parsed.items()]
            else:
                lines = [str(parsed)]
        else:
            lines = [line.strip() for line in raw_response.split("\n") if line.strip()]
        return {
            "success": True,
            "command": command,
            "response": lines,
            "formatted": True,
        }

    parsed, json_ok = try_json_parse(raw_response)

    if not json_ok and isinstance(parsed, str):
        parsed, literal_ok = try_literal_eval(parsed)
        if literal_ok and isinstance(parsed, (dict, list, tuple)):
            try:
                parsed = json.loads(json.dumps(parsed, default=str))
                logger.info(f"ast.literal_eval -> json serialization succeeded for {command}")
            except (TypeError, ValueError) as e:
                logger.error(f"Failed to serialize literal_eval result for {command}: {e}")
                return {
                    "success": False,
                    "command": command,
                    "error": f"Unserializable data from device: {str(e)}",
                    "raw": raw_response,
                }
        else:
            return {
                "success": False,
                "command": command,
                "error": f"Unparseable response from device. Expected JSON or Python literal, got: {raw_response[:200]}",
                "raw": raw_response,
            }

    validation = validate_structured_response(command, parsed)
    if not validation["valid"]:
        return {
            "success": False,
            "command": command,
            "error": f"Response failed schema validation: {validation['error']}",
            "raw": raw_response,
        }

    return {
        "success": True,
        "command": command,
        "response": validation["data"],
        "formatted": True,
    }
