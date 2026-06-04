import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class CreationEngine:
    """
    A class for creating models and tools.
    """

    def __init__(self) -> None:
        self.templates: Dict[str, Callable[..., str]] = {}
        self._init_default_templates()
        logger.debug(f"{type(self).__name__}.__init__ completed")

    def _init_default_templates(self) -> None:
        def model_template(params: Dict[str, Any]) -> str:
            name = params.get("name", "MyModel")
            fields = params.get("fields", [])
            methods = params.get("methods", ["train", "evaluate"])
            field_defs = "\n    ".join(f"self.{f} = {f}" for f in fields) if fields else "pass"
            method_defs = []
            for m in methods:
                method_defs.append(f"\n    def {m}(self, *args, **kwargs):\n        return f\"{m} called on {name}\"")
            return f"""class {name}:
    def __init__(self, {', '.join(fields) if fields else '*args'}):
        {field_defs}{''.join(method_defs)}
"""

        def tool_template(params: Dict[str, Any]) -> str:
            name = params.get("name", "my_tool")
            desc = params.get("description", f"A tool for {name}")
            args = params.get("args", ["input_data"])
            arg_str = ", ".join(args)
            return f"""def {name}({arg_str}):
    \"\"\"{desc}\"\"\"
    return f"Processed {{input_data}} with {name}"
"""

        def api_template(params: Dict[str, Any]) -> str:
            route = params.get("route", "/api/endpoint")
            method = params.get("method", "GET")
            handler = params.get("handler", "handle_request")
            return f"""from fastapi import APIRouter

router = APIRouter()

@{router.get('{route}') if method == 'GET' else router.post('{route}')}
async def {handler}():
    return {{"status": "ok"}}
"""

        self.templates["model"] = model_template
        self.templates["tool"] = tool_template
        self.templates["api"] = api_template

    def register_template(self, name: str, template_func: Callable[..., str]) -> None:
        self.templates[name] = template_func

    def list_templates(self) -> List[str]:
        return list(self.templates.keys())

    def create(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Creates a model or tool that matches a query.

        Args:
            query: The query to create a model or tool for.
            params: Optional parameters for template rendering.

        Returns:
            A string containing the code for the model or tool, or None.
        """
        params = params or {}
        if "model" in query:
            if "name" not in params:
                params["name"] = query.replace("create", "").replace("model", "").strip() or "MyModel"
            return self._apply_template("model", params)
        elif "tool" in query:
            if "name" not in params:
                params["name"] = query.replace("create", "").replace("tool", "").strip() or "my_tool"
            return self._apply_template("tool", params)
        else:
            for tname in self.templates:
                if tname in query:
                    return self._apply_template(tname, params)
            return None

    def _apply_template(self, template_name: str, params: Dict[str, Any]) -> Optional[str]:
        template = self.templates.get(template_name)
        if template is None:
            logger.warning(f"Template '{template_name}' not found")
            return None
        return template(params)
