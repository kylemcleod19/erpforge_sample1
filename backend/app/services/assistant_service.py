import json
import logging
import uuid
from collections.abc import Generator

import anthropic
from sqlalchemy.orm import Session

from app.config import settings
from app.models.assistant import AssistantConversation, AssistantMessage
from app.models.user import User
from app.schemas.assistant import PageContext
from app.services.assistant_tools import TOOL_DEFINITIONS, execute_tool, get_app_state_for_prompt

logger = logging.getLogger(__name__)

IDENTITY_PROMPT = """You are ERPForge Assistant, an AI copilot embedded in a manufacturing ERP application.
You help users understand ERP concepts, navigate workflows, and perform actions.

IMPORTANT RULES:
- ALWAYS describe what you're about to do and ask for explicit confirmation before using any tool that creates or modifies data.
- For read-only tools (list_products, get_app_state_summary) you may call them without asking first.
- For navigate_user, you may suggest navigation without asking.
- Be concise and use manufacturing terminology naturally.
- Guide users step by step through workflows rather than doing everything at once.
- When the system is empty, proactively suggest starting with products/components as the foundation."""

ROLE_GUIDANCE = {
    "admin": "This user is an admin with full visibility. Help with any workflow or module.",
    "engineer": "This user is an engineer. Focus on Products, BOMs, Stations, Routings, Work Orders, and Inventory. The typical engineering flow is: Create Products/Components -> Define BOMs -> Set up Stations -> Create Routings -> Work orders auto-create from orders.",
    "sales": "This user is in sales. Focus on Quotes, Orders, Shipping, and Invoices. The typical sales flow is: Create Quote -> Add Line Items -> Review -> Approve -> Send -> Mark Won -> Convert to Order -> Ship -> Invoice auto-generates.",
}


def _build_system_prompt(user: User, page_context: PageContext | None, db: Session) -> str:
    parts = [IDENTITY_PROMPT]

    # User context
    parts.append(f"\nCurrent user: {user.display_name} (role: {user.role})")
    parts.append(ROLE_GUIDANCE.get(user.role, ""))

    # Page context
    if page_context and page_context.current_page:
        parts.append(f"\nThe user is currently on page: {page_context.current_page}")

    # App state
    app_state = get_app_state_for_prompt(db)
    parts.append(f"\nCurrent application state:\n{app_state}")

    return "\n".join(parts)


def _get_or_create_conversation(
    conversation_id: str | None, user: User, db: Session
) -> AssistantConversation:
    if conversation_id:
        conv = db.query(AssistantConversation).filter(
            AssistantConversation.id == conversation_id,
            AssistantConversation.user_id == user.id,
        ).first()
        if conv:
            return conv

    conv = AssistantConversation(
        id=str(uuid.uuid4()),
        user_id=user.id,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def _save_message(conversation_id: str, role: str, content: str, db: Session) -> None:
    msg = AssistantMessage(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        role=role,
        content=content,
    )
    db.add(msg)
    db.commit()


def _load_message_history(conversation_id: str, db: Session) -> list[dict]:
    messages = (
        db.query(AssistantMessage)
        .filter(AssistantMessage.conversation_id == conversation_id)
        .order_by(AssistantMessage.created_at)
        .all()
    )

    api_messages = []
    for msg in messages:
        if msg.role == "user":
            api_messages.append({"role": "user", "content": msg.content})
        elif msg.role == "assistant":
            api_messages.append({"role": "assistant", "content": msg.content})
        elif msg.role == "tool_use":
            data = json.loads(msg.content)
            api_messages.append({
                "role": "assistant",
                "content": [{"type": "tool_use", "id": data["id"], "name": data["name"], "input": data["input"]}],
            })
        elif msg.role == "tool_result":
            data = json.loads(msg.content)
            api_messages.append({
                "role": "user",
                "content": [{"type": "tool_result", "tool_use_id": data["tool_use_id"], "content": data["content"]}],
            })
    return api_messages


def chat_stream(
    message: str,
    conversation_id: str | None,
    page_context: PageContext | None,
    user: User,
    db: Session,
) -> Generator[str, None, None]:
    """Stream SSE events for a chat message. Yields 'data: ...\n\n' formatted strings."""

    if not settings.anthropic_api_key:
        yield _sse({"type": "error", "content": "Anthropic API key not configured. Set ANTHROPIC_API_KEY in your environment."})
        yield _sse({"type": "done", "conversation_id": ""})
        return

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    # Get or create conversation
    conv = _get_or_create_conversation(conversation_id, user, db)

    # Save user message
    _save_message(conv.id, "user", message, db)

    # Set title from first message
    if not conv.title:
        conv.title = message[:100]
        db.commit()

    # Build messages for API
    system_prompt = _build_system_prompt(user, page_context, db)
    api_messages = _load_message_history(conv.id, db)

    # Tool use loop
    max_iterations = 10
    for _ in range(max_iterations):
        # Collect the full response first (for tool use handling)
        full_text = ""
        tool_uses = []

        try:
            with client.messages.stream(
                model=settings.anthropic_model,
                max_tokens=4096,
                system=system_prompt,
                messages=api_messages,
                tools=TOOL_DEFINITIONS,
            ) as stream:
                for event in stream:
                    if event.type == "content_block_start":
                        if hasattr(event.content_block, "text"):
                            pass  # text block starting
                        elif hasattr(event.content_block, "name"):
                            # Tool use block starting
                            tool_uses.append({
                                "id": event.content_block.id,
                                "name": event.content_block.name,
                                "input_json": "",
                            })
                    elif event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            full_text += event.delta.text
                            yield _sse({"type": "text", "content": event.delta.text})
                        elif hasattr(event.delta, "partial_json"):
                            if tool_uses:
                                tool_uses[-1]["input_json"] += event.delta.partial_json

        except anthropic.APIError as e:
            logger.error("Anthropic API error: %s", e)
            yield _sse({"type": "error", "content": f"AI service error: {str(e)}"})
            yield _sse({"type": "done", "conversation_id": conv.id})
            return

        # If there are no tool uses, we're done
        if not tool_uses:
            if full_text:
                _save_message(conv.id, "assistant", full_text, db)
            break

        # Handle tool uses
        # First save any text that came before tools
        if full_text:
            _save_message(conv.id, "assistant", full_text, db)

        # Build the assistant message with both text and tool_use blocks
        assistant_content = []
        if full_text:
            assistant_content.append({"type": "text", "text": full_text})

        tool_results_content = []
        for tu in tool_uses:
            try:
                tool_input = json.loads(tu["input_json"]) if tu["input_json"] else {}
            except json.JSONDecodeError:
                tool_input = {}

            # Save tool_use message
            _save_message(conv.id, "tool_use", json.dumps({
                "id": tu["id"], "name": tu["name"], "input": tool_input,
            }), db)

            assistant_content.append({
                "type": "tool_use",
                "id": tu["id"],
                "name": tu["name"],
                "input": tool_input,
            })

            # Execute tool
            yield _sse({"type": "tool_use", "tool": tu["name"], "input": tool_input})
            result = execute_tool(tu["name"], tool_input, db, user)
            yield _sse({"type": "tool_result", "tool": tu["name"], "content": result})

            # Save tool_result message
            _save_message(conv.id, "tool_result", json.dumps({
                "tool_use_id": tu["id"], "content": result,
            }), db)

            tool_results_content.append({
                "type": "tool_result",
                "tool_use_id": tu["id"],
                "content": result,
            })

        # Add to api_messages for the next iteration
        api_messages.append({"role": "assistant", "content": assistant_content})
        api_messages.append({"role": "user", "content": tool_results_content})

        # Reset for next iteration
        full_text = ""
        tool_uses = []

    yield _sse({"type": "done", "conversation_id": conv.id})


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"
