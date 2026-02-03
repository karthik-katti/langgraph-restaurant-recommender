import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


def _dump(obj):
    return obj.model_dump() if hasattr(obj, "model_dump") else obj


def _coerce(raw: str, typ: str) -> Any:
    if typ == "integer":
        return int(raw)
    if typ == "number":
        return float(raw)
    if typ == "boolean":
        return raw.strip().lower() in ("1", "true", "yes", "y", "on")
    if typ == "array":
        return [x.strip() for x in raw.split(",") if x.strip()]
    return raw


async def elicitation_callback(ctx, params) -> Dict[str, Any]:
    """
    Newer SDK calls: callback(ctx, params)
    Newer params fields are snake_case:
      - requested_schema (form mode)
      - url + elicitation_id (url mode)
    """
    # URL-mode elicitation
    print("----callback  came--------")
    if hasattr(params, "url"):
        print("\n=== ELICITATION (URL MODE) ===")
        print(getattr(params, "message", ""))
        print("URL:", params.url)
        print("elicitation_id:", getattr(params, "elicitation_id", None))
        input("Press Enter to ACCEPT (Ctrl+C to abort)… ")
        return {"action": "accept"}

    # Form-mode elicitation
    print("\n=== ELICITATION (FORM MODE) ===")
    print(getattr(params, "message", ""))

    schema = getattr(params, "requested_schema", None)
    if schema is None:
        # fall back just in case
        schema = getattr(params, "requestedSchema", None)

    schema = _dump(schema)
    print("Requested schema:")
    print(json.dumps(schema, indent=2))

    props = schema.get("properties", {}) if isinstance(schema, dict) else {}
    required = set(schema.get("required", [])) if isinstance(schema, dict) else set()

    content: Dict[str, Any] = {}
    for name, ps in props.items():
        typ = ps.get("type", "string")
        default = ps.get("default", None)
        title = ps.get("title", name)

        prompt = f"{title} ({typ})"
        if name in required:
            prompt += " [required]"
        if default is not None:
            prompt += f" [default={default}]"
        prompt += ": "

        while True:
            raw = input(prompt).strip()
            if raw == "" and default is not None:
                content[name] = default
                break
            if raw == "" and name not in required:
                break
            if raw == "" and name in required:
                print("Required.")
                continue
            try:
                content[name] = _coerce(raw, typ)
                break
            except Exception as e:
                print(f"Invalid value for type '{typ}': {e}")

    return {"action": "accept", "content": content}


async def prompt_for_tool_args(tool) -> Dict[str, Any]:
    """
    Reads tool.input_schema (snake_case) if present; falls back to inputSchema.
    Prompts for required properties.
    """
    schema = getattr(tool, "input_schema", None)
    if schema is None:
        schema = getattr(tool, "inputSchema", None)
    schema = _dump(schema) if schema is not None else {}

    props = schema.get("properties", {}) if isinstance(schema, dict) else {}
    required = set(schema.get("required", [])) if isinstance(schema, dict) else set()

    if not props:
        return {}

    print("\nTool input schema:")
    print(json.dumps(schema, indent=2))

    args: Dict[str, Any] = {}
    for name, ps in props.items():
        typ = ps.get("type", "string")
        default = ps.get("default", None)

        prompt = f"{name} ({typ})"
        if name in required:
            prompt += " [required]"
        if default is not None:
            prompt += f" [default={default}]"
        prompt += ": "

        while True:
            raw = input(prompt).strip()
            if raw == "" and default is not None:
                args[name] = default
                break
            if raw == "" and name not in required:
                break
            if raw == "" and name in required:
                print("Required.")
                continue
            try:
                args[name] = _coerce(raw, typ)
                break
            except Exception as e:
                print(f"Invalid value for type '{typ}': {e}")

    return args


async def main():
    # IMPORTANT: run from repo root
    repo_root = Path(__file__).resolve().parent
    server_file ="elicitation.py"


    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_file)],
        env=os.environ.copy(),
        cwd=str(repo_root),
    )

    async with stdio_client(server_params, errlog=sys.stderr) as (read, write):
        async with ClientSession(read, write, elicitation_callback=elicitation_callback) as session:
            await session.initialize()

            tools = await session.list_tools()
            if not tools.tools:
                print("No tools exposed by server.")
                return

            print("\nTools:")
            for i, t in enumerate(tools.tools, 1):
                print(f"  {i}. {t.name}")

            choice = input(f"\nPick a tool [1-{len(tools.tools)}] (default 1): ").strip()
            idx = int(choice) if choice else 1
            tool = tools.tools[idx - 1]

            tool_args = await prompt_for_tool_args(tool)
            print(f"\nCalling {tool.name} with args: {tool_args}\n")

            result = await session.call_tool(tool.name, tool_args)

            # snake_case in your SDK
            print("is_error:", result.is_error)
            for block in result.content:
                print(json.dumps(_dump(block), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
