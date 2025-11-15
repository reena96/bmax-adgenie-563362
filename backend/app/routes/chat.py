"""
Chat interface routes.

This module will handle chat-related operations including:
- Sending messages
- Receiving AI responses
- Chat history
- Context management
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db

router = APIRouter()


@router.post(
    "/messages",
    status_code=status.HTTP_201_CREATED,
    summary="Send Message",
    description="Send a message in the chat interface"
)
async def send_message(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Send a message to the chat interface.

    This endpoint will be implemented in a future story.
    """
    return {
        "message": "Send message endpoint - to be implemented",
        "status": "stub"
    }


@router.get(
    "/messages/{project_id}",
    status_code=status.HTTP_200_OK,
    summary="Get Chat History",
    description="Get chat history for a project"
)
async def get_chat_history(project_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get chat history for a project.

    This endpoint will be implemented in a future story.
    """
    return {
        "message": f"Get chat history for project {project_id} - to be implemented",
        "status": "stub"
    }


@router.delete(
    "/messages/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear Chat History",
    description="Clear chat history for a project"
)
async def clear_chat_history(project_id: int, db: Session = Depends(get_db)) -> None:
    """
    Clear chat history for a project.

    This endpoint will be implemented in a future story.
    """
    pass
