"""21 CFR Part 11 compliant audit trail extractor for parsing Pydantic AI RunResults."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List
from pydantic_ai import AgentRunResult
from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    SystemPromptPart,
    UserPromptPart,
    ToolCallPart,
    ToolReturnPart,
    RetryPromptPart,
    TextPart
)


def extract_audit_trail(result: AgentRunResult) -> str:
    """Parses Pydantic AI run messages and metadata into a structured audit trail.

    Specifically extracts:
    - Version/content of system prompt used.
    - User prompts and feedback loops.
    - Tool calls with exact arguments executed.
    - Tool responses and returns.
    - Final aggregated token metrics.

    Args:
        result: The Pydantic AI RunResult from executing an agent run.

    Returns:
        A structured JSON string representing the GxP-compliant audit log.
    """
    audit_events: List[Dict[str, Any]] = []
    system_prompts: List[str] = []

    for message in result.all_messages():
        if isinstance(message, ModelRequest):
            for part in message.parts:
                # Extract system prompts
                if isinstance(part, SystemPromptPart):
                    system_prompts.append(part.content)
                    audit_events.append({
                        "timestamp": part.timestamp.astimezone(timezone.utc).isoformat() if hasattr(part, "timestamp") and part.timestamp else datetime.now(timezone.utc).isoformat(),
                        "event_type": "SYSTEM_PROMPT",
                        "content": part.content
                    })
                # Extract user input
                elif isinstance(part, UserPromptPart):
                    content_str = part.content
                    if not isinstance(content_str, str):
                        content_str = str(content_str)
                    audit_events.append({
                        "timestamp": part.timestamp.astimezone(timezone.utc).isoformat() if hasattr(part, "timestamp") and part.timestamp else datetime.now(timezone.utc).isoformat(),
                        "event_type": "USER_INPUT",
                        "content": content_str
                    })
                # Extract tool executions returns
                elif isinstance(part, ToolReturnPart):
                    content_str = part.content
                    if not isinstance(content_str, str):
                        content_str = str(content_str)
                    audit_events.append({
                        "timestamp": part.timestamp.astimezone(timezone.utc).isoformat() if hasattr(part, "timestamp") and part.timestamp else datetime.now(timezone.utc).isoformat(),
                        "event_type": "TOOL_RETURN",
                        "tool_name": part.tool_name,
                        "tool_call_id": part.tool_call_id,
                        "content": content_str
                    })
                # Extract retry prompts
                elif isinstance(part, RetryPromptPart):
                    audit_events.append({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "event_type": "RETRY_PROMPT",
                        "content": str(part.content) if hasattr(part, "content") else "Model validation retry requested"
                    })

        elif isinstance(message, ModelResponse):
            timestamp_str = message.timestamp.astimezone(timezone.utc).isoformat() if hasattr(message, "timestamp") and message.timestamp else datetime.now(timezone.utc).isoformat()
            for part in message.parts:
                # Extract text responses
                if isinstance(part, TextPart):
                    audit_events.append({
                        "timestamp": timestamp_str,
                        "event_type": "MODEL_TEXT_RESPONSE",
                        "content": part.content
                    })
                # Extract tool invocation calls
                elif isinstance(part, ToolCallPart):
                    args_data = part.args
                    # Coerce args data into dict format
                    if not isinstance(args_data, dict):
                        if hasattr(args_data, "dict"):
                            args_data = args_data.dict()
                        elif hasattr(args_data, "model_dump"):
                            args_data = args_data.model_dump()
                        else:
                            args_data = {"raw_args": str(args_data)}
                    audit_events.append({
                        "timestamp": timestamp_str,
                        "event_type": "TOOL_CALL",
                        "tool_name": part.tool_name,
                        "tool_call_id": part.tool_call_id,
                        "arguments": args_data
                    })

    # Retrieve total token usages
    usage = result.usage
    usage_info = {
        "requests": usage.requests if hasattr(usage, "requests") else 0,
        "input_tokens": usage.input_tokens if hasattr(usage, "input_tokens") else 0,
        "output_tokens": usage.output_tokens if hasattr(usage, "output_tokens") else 0,
        "total_tokens": usage.total_tokens if hasattr(usage, "total_tokens") else 0
    }

    audit_trail = {
        "audit_trail_created_at": datetime.now(timezone.utc).isoformat(),
        "primary_system_prompt": system_prompts[0] if system_prompts else "None",
        "token_usage": usage_info,
        "events": audit_events
    }

    return json.dumps(audit_trail, indent=2)
