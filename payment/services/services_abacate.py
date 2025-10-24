import logging
from typing import Any, Dict, Union


logger = logging.getLogger(__name__)


def norm_response(result: Any) -> Union[Dict[str, Any], str]:
    if isinstance(result, dict):
        return result

    try:
        if hasattr(result, "to_dict") and callable(getattr(result, "to_dict")):
            return result.to_dict()
    except Exception as exc:
        logger.exception("Erro ao chamar to_dict no resultado: %s", exc)

    try:
        if hasattr(result, "__dict__"):
            return vars(result)
    except Exception as exc:
        logger.exception("Erro ao acessar __dict__ do resultado: %s", exc)

    return str(result)