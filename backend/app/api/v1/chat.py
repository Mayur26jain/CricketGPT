from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db, AsyncSessionLocal
from app.api.deps import get_current_user
from app.models.user import Conversation, Message, Bookmark, User
from app.schemas.chat import (
    ConversationResponse, 
    ConversationCreate, 
    MessageResponse, 
    MessageCreate, 
    BookmarkResponse, 
    BookmarkCreate
)
from app.agents.graph import cricket_graph
from typing import List
import json
import asyncio

router = APIRouter()

@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .options(selectinload(Conversation.messages))
        .order_by(Conversation.updated_at.desc())
    )
    return list(result.scalars().all())

@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    conv_in: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    db_conv = Conversation(
        user_id=current_user.id,
        title=conv_in.title
    )
    db.add(db_conv)
    await db.commit()
    await db.refresh(db_conv)
    
    # Reload with empty message list to satisfy schema
    result = await db.execute(
        select(Conversation)
        .filter(Conversation.id == db_conv.id)
        .options(selectinload(Conversation.messages))
    )
    return result.scalars().first()

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def list_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify ownership
    result_conv = await db.execute(
        select(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
    )
    if not result_conv.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    result = await db.execute(
        select(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    return list(result.scalars().all())

@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    msg_in: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify ownership
    result_conv = await db.execute(
        select(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
    )
    conv = result_conv.scalars().first()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Save User message
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=msg_in.content
    )
    db.add(user_msg)
    
    # Load history
    result_history = await db.execute(
        select(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    history_msgs = result_history.scalars().all()
    history = [{"role": m.role, "content": m.content} for m in history_msgs]
    
    # Run Agent Graph Orchestrator
    state_input = {
        "query": msg_in.content,
        "intent": None,
        "sql_query": None,
        "sql_results": None,
        "rag_documents": None,
        "live_api_data": None,
        "prediction_results": None,
        "chart_schema": None,
        "response": None,
        "history": history
    }
    
    agent_output = await cricket_graph.ainvoke(state_input)
    
    # Save Assistant message
    assistant_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=agent_output.get("response", "Could not process request."),
        visualization_data=agent_output.get("chart_schema")
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)
    
    return assistant_msg

@router.post("/bookmarks", response_model=BookmarkResponse)
async def create_bookmark(
    bookmark_in: BookmarkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Check if message exists
    result_msg = await db.execute(
        select(Message).filter(Message.id == bookmark_in.message_id)
    )
    if not result_msg.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    db_bookmark = Bookmark(
        user_id=current_user.id,
        message_id=bookmark_in.message_id,
        title=bookmark_in.title
    )
    db.add(db_bookmark)
    await db.commit()
    await db.refresh(db_bookmark)
    return db_bookmark

@router.get("/bookmarks", response_model=List[BookmarkResponse])
async def list_bookmarks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Bookmark).filter(Bookmark.user_id == current_user.id)
    )
    return list(result.scalars().all())

# WebSocket endpoint for real-time token/agent trace streaming
@router.websocket("/ws/{conversation_id}")
async def websocket_chat_endpoint(websocket: WebSocket, conversation_id: str):
    await websocket.accept()
    db = AsyncSessionLocal()
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            query = payload.get("query")
            
            # Send initial acknowledgement / trace
            await websocket.send_text(json.dumps({"type": "status", "content": "Routing query..."}))
            await asyncio.sleep(0.3)
            
            # Formulate user message
            user_msg = Message(
                conversation_id=conversation_id,
                role="user",
                content=query
            )
            db.add(user_msg)
            
            # Fetch history
            result_history = await db.execute(
                select(Message)
                .filter(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.asc())
            )
            history_msgs = result_history.scalars().all()
            history = [{"role": m.role, "content": m.content} for m in history_msgs]
            
            state_input = {
                "query": query,
                "intent": None,
                "sql_query": None,
                "sql_results": None,
                "rag_documents": None,
                "live_api_data": None,
                "prediction_results": None,
                "chart_schema": None,
                "response": None,
                "history": history
            }
            
            # Simulate intermediate agent logs for high-end UX
            agent_output = await cricket_graph.ainvoke(state_input)
            intent = agent_output.get("intent")
            
            await websocket.send_text(json.dumps({"type": "status", "content": f"Running {intent} sub-agent..."}))
            await asyncio.sleep(0.4)
            
            if intent == "SQL_STATISTICS" and agent_output.get("sql_query"):
                await websocket.send_text(json.dumps({
                    "type": "trace", 
                    "content": f"Formulated SQL: `{agent_output['sql_query'].strip()}`"
                }))
                await asyncio.sleep(0.3)
                
            # Stream response word-by-word to mock LLM streaming UI experience
            full_response = agent_output.get("response", "Could not retrieve response.")
            words = full_response.split(" ")
            
            await websocket.send_text(json.dumps({"type": "stream_start"}))
            current_buffer = ""
            for word in words:
                current_buffer += word + " "
                await websocket.send_text(json.dumps({"type": "chunk", "content": word + " "}))
                await asyncio.sleep(0.04) # smooth text animation speed
            
            # Save Assistant message
            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=full_response,
                visualization_data=agent_output.get("chart_schema")
            )
            db.add(assistant_msg)
            await db.commit()
            
            # Send completion signal with chart schema if present
            await websocket.send_text(json.dumps({
                "type": "completed", 
                "message_id": assistant_msg.id,
                "visualization_data": agent_output.get("chart_schema")
            }))
            
    except WebSocketDisconnect:
        print(f"WebSocket client disconnected from {conversation_id}")
    finally:
        await db.close()
