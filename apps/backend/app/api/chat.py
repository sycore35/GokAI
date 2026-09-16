"""
GÖK SYSTEMS TECH — AI Chat & Multimodal Assistant API
Provides interactive project-aware conversation, streaming/retry, and code/file attachments.
"""

import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from gokai.apps.backend.app.core.database import get_db
from gokai.apps.backend.app.core.config import settings
from gokai.apps.backend.app.models.entities import (
    Conversation,
    ChatMessage,
    Project,
    MemoryEntry,
    ActivityLog,
)
from gokai.apps.backend.app.schemas.dtos import (
    ConversationCreate,
    ConversationResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    AttachmentItem,
)
from gokai.packages.model_router import ModelRouter, ModelMessage
from gokai.packages.shared.logger import get_logger

logger = get_logger("chat_api")
router = APIRouter(prefix="/chat", tags=["Chat"])

# Initialize singleton router with current settings
_router_instance = ModelRouter(
    gemini_api_key=settings.GEMINI_API_KEY,
    openai_api_key=settings.OPENAI_API_KEY,
    deepseek_api_key=settings.DEEPSEEK_API_KEY,
    nvidia_api_key=settings.NVIDIA_API_KEY,
    anthropic_api_key=settings.ANTHROPIC_API_KEY,
    openrouter_api_key=settings.OPENROUTER_API_KEY,
    default_provider=settings.DEFAULT_PROVIDER,
    default_model=settings.DEFAULT_MODEL,
)


def get_model_router() -> ModelRouter:
    # Refresh router keys from settings
    _router_instance.reconfigure(
        gemini_api_key=settings.GEMINI_API_KEY,
        openai_api_key=settings.OPENAI_API_KEY,
        deepseek_api_key=settings.DEEPSEEK_API_KEY,
        nvidia_api_key=settings.NVIDIA_API_KEY,
        anthropic_api_key=settings.ANTHROPIC_API_KEY,
        openrouter_api_key=settings.OPENROUTER_API_KEY,
        default_provider=settings.DEFAULT_PROVIDER,
        default_model=settings.DEFAULT_MODEL,
    )
    return _router_instance


@router.get("/conversations", response_model=List[ConversationResponse])
def list_conversations(project_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Lists all chat conversations, optionally filtered by workspace project."""
    query = db.query(Conversation)
    if project_id:
        query = query.filter(Conversation.project_id == project_id)
    convs = query.order_by(Conversation.updated_at.desc()).all()

    results = []
    for c in convs:
        msg_count = db.query(ChatMessage).filter(ChatMessage.conversation_id == c.id).count()
        results.append(ConversationResponse(
            id=c.id,
            project_id=c.project_id,
            title=c.title,
            created_at=c.created_at,
            message_count=msg_count
        ))
    return results


@router.post("/conversations", response_model=ConversationResponse)
def create_conversation(payload: ConversationCreate, db: Session = Depends(get_db)):
    """Creates a new conversation session."""
    conv = Conversation(
        title=payload.title or "New Conversation",
        project_id=payload.project_id
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return ConversationResponse(
        id=conv.id,
        project_id=conv.project_id,
        title=conv.title,
        created_at=conv.created_at,
        message_count=0
    )


@router.get("/conversations/{conv_id}", response_model=List[ChatMessageResponse])
def get_conversation_messages(conv_id: str, db: Session = Depends(get_db)):
    """Returns all messages in a conversation."""
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msgs = db.query(ChatMessage).filter(ChatMessage.conversation_id == conv_id).order_by(ChatMessage.created_at.asc()).all()
    results = []
    for m in msgs:
        att_list = []
        try:
            raw = json.loads(m.attachments_json or "[]")
            att_list = [AttachmentItem(**item) for item in raw]
        except Exception:
            pass

        results.append(ChatMessageResponse(
            id=m.id,
            conversation_id=m.conversation_id,
            role=m.role,
            content=m.content,
            attachments=att_list,
            provider=m.provider,
            model=m.model,
            created_at=m.created_at
        ))
    return results


@router.delete("/conversations/{conv_id}")
def delete_conversation(conv_id: str, db: Session = Depends(get_db)):
    """Deletes a conversation and its messages."""
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conv)
    db.commit()
    return {"status": "deleted", "id": conv_id}


@router.post("/conversations/{conv_id}/messages", response_model=ChatMessageResponse)
async def send_chat_message(conv_id: str, payload: ChatMessageCreate, db: Session = Depends(get_db)):
    """Sends a message, constructs project-aware context with attachments, and returns AI response."""
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Serialize attachments
    attachments_data = [a.model_dump() for a in payload.attachments]
    user_msg = ChatMessage(
        conversation_id=conv_id,
        role="user",
        content=payload.content,
        attachments_json=json.dumps(attachments_data),
        created_at=datetime.now(timezone.utc)
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # Auto-update conversation title from first user message if default
    if conv.title in ("New Conversation", "Yeni Sohbet") and payload.content:
        conv.title = (payload.content[:35] + "...") if len(payload.content) > 35 else payload.content
        conv.updated_at = datetime.now(timezone.utc)
        db.commit()

    # Build Project Context
    system_context = (
        "You are GökAI — an autonomous AI software engineering expert developed by GÖK SYSTEMS TECH.\n"
        "You provide precise, clean, production-grade software engineering guidance, code generation, "
        "and architectural reasoning.\n"
    )

    if conv.project_id:
        proj = db.query(Project).filter(Project.id == conv.project_id).first()
        if proj:
            system_context += f"\nActive Workspace Project: '{proj.name}' (Stack: {proj.default_stack})\n"
            # Fetch project memory entries
            memories = db.query(MemoryEntry).filter(MemoryEntry.project_id == proj.id).limit(10).all()
            if memories:
                system_context += "Project Memory & Architecture Decisions:\n"
                for m in memories:
                    system_context += f"- [{m.key}]: {m.content}\n"

    # Assemble conversation history
    history = db.query(ChatMessage).filter(ChatMessage.conversation_id == conv_id).order_by(ChatMessage.created_at.asc()).all()

    model_messages = [ModelMessage(role="system", content=system_context)]

    for m in history:
        msg_text = m.content
        # Append text / code attachment content into prompt context
        if m.attachments_json:
            try:
                atts = json.loads(m.attachments_json)
                for att in atts:
                    if att.get("type") in ("code", "file") and att.get("content"):
                        msg_text += f"\n\n--- Attachment: {att.get('name')} ---\n{att.get('content')}\n--- End Attachment ---"
                    elif att.get("type") == "image":
                        msg_text += f"\n[User attached image: {att.get('name')}]"
            except Exception:
                pass

        model_messages.append(ModelMessage(
            role=m.role if m.role in ("user", "assistant") else "user",
            content=msg_text
        ))

    router_service = get_model_router()

    try:
        completion = await router_service.generate_completion(
            messages=model_messages,
            preferred_provider=settings.DEFAULT_PROVIDER,
            preferred_model=settings.DEFAULT_MODEL,
            temperature=0.3
        )

        ai_msg = ChatMessage(
            conversation_id=conv_id,
            role="assistant",
            content=completion.content,
            provider=completion.provider,
            model=completion.model,
            tokens=completion.output_tokens,
            created_at=datetime.now(timezone.utc)
        )
        db.add(ai_msg)
        conv.updated_at = datetime.now(timezone.utc)

        # Log activity
        db.add(ActivityLog(
            project_id=conv.project_id,
            actor=f"{completion.provider}:{completion.model}",
            action="CHAT_COMPLETION",
            message=f"Answered query in conversation '{conv.title}' ({completion.output_tokens} tokens)",
            level="SUCCESS"
        ))

        db.commit()
        db.refresh(ai_msg)

        return ChatMessageResponse(
            id=ai_msg.id,
            conversation_id=ai_msg.conversation_id,
            role=ai_msg.role,
            content=ai_msg.content,
            attachments=[],
            provider=ai_msg.provider,
            model=ai_msg.model,
            created_at=ai_msg.created_at
        )

    except Exception as ex:
        logger.error(f"Chat generation error: {ex}")
        # Save error message as assistant response so user has clear context
        err_msg = ChatMessage(
            conversation_id=conv_id,
            role="assistant",
            content=f"⚠️ Model generation failed: {str(ex)}. Please check your AI provider credentials in Settings.",
            provider=settings.DEFAULT_PROVIDER,
            model=settings.DEFAULT_MODEL,
            created_at=datetime.now(timezone.utc)
        )
        db.add(err_msg)
        db.commit()
        db.refresh(err_msg)

        return ChatMessageResponse(
            id=err_msg.id,
            conversation_id=err_msg.conversation_id,
            role=err_msg.role,
            content=err_msg.content,
            attachments=[],
            provider=err_msg.provider,
            model=err_msg.model,
            created_at=err_msg.created_at
        )
