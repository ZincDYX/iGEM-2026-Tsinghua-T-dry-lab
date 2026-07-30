from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable


JsonObject = dict[str, Any]
ToolHandler = Callable[[JsonObject], "McpToolResult"]


@dataclass(frozen=True)
class McpTool:
    name: str
    title: str
    description: str
    input_schema: JsonObject
    output_schema: JsonObject | None

    def as_protocol_dict(self) -> JsonObject:
        payload: JsonObject = {
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "inputSchema": self.input_schema,
        }
        if self.output_schema is not None:
            payload["outputSchema"] = self.output_schema
        return payload


@dataclass(frozen=True)
class McpToolResult:
    structured_content: JsonObject
    is_error: bool = False

    def as_protocol_dict(self) -> JsonObject:
        text = json.dumps(self.structured_content, ensure_ascii=False, indent=2)
        result: JsonObject = {
            "content": [{"type": "text", "text": text}],
            "structuredContent": self.structured_content,
        }
        if self.is_error:
            result["isError"] = True
        return result

    @classmethod
    def ok(cls, payload: JsonObject) -> "McpToolResult":
        return cls(structured_content=payload, is_error=False)

    @classmethod
    def error(cls, message: str, *, error_type: str = "tool_error") -> "McpToolResult":
        return cls(
            structured_content={"ok": False, "error": {"type": error_type, "message": message}},
            is_error=True,
        )
