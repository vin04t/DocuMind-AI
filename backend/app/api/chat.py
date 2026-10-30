from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models import Conversation, Message, Citation, VerificationClaim, Feedback, User, Document
from app.schemas import (
    ConversationResponse, MessageCreate, MessageResponse,
    CitationResponse, VerificationClaimResponse, FeedbackCreate
)
from app.api.auth import get_current_user
from app.services.rag_engine import rag_engine

router = APIRouter(prefix="/chat", tags=["Chat & Intelligence"])


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(desc(Conversation.updated_at))
    )
    convs = res.scalars().all()
    return [
        ConversationResponse(
            id=c.id,
            title=c.title,
            document_id=c.document_id,
            collection_id=c.collection_id,
            created_at=c.created_at,
            updated_at=c.updated_at,
            messages=[]
        )
        for c in convs
    ]


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    title: Optional[str] = "New Research Session",
    document_id: Optional[str] = None,
    collection_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    conv = Conversation(
        title=title,
        document_id=document_id if document_id != "none" and document_id else None,
        collection_id=collection_id if collection_id != "none" and collection_id else None,
        user_id=current_user.id
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return ConversationResponse(
        id=conv.id,
        title=conv.title,
        document_id=conv.document_id,
        collection_id=conv.collection_id,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=[]
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conv = res.scalars().first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    # Fetch messages
    msg_res = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = msg_res.scalars().all()

    msg_responses = []
    for m in messages:
        # Fetch citations
        cit_res = await db.execute(select(Citation).where(Citation.message_id == m.id))
        citations = cit_res.scalars().all()

        # Fetch verification claims
        claim_res = await db.execute(select(VerificationClaim).where(VerificationClaim.message_id == m.id))
        claims = claim_res.scalars().all()

        msg_responses.append(MessageResponse(
            id=m.id,
            conversation_id=m.conversation_id,
            role=m.role,
            content=m.content,
            retrieval_latency_ms=m.retrieval_latency_ms,
            answer_latency_ms=m.answer_latency_ms,
            created_at=m.created_at,
            citations=[CitationResponse.model_validate(c) for c in citations],
            verification_claims=[VerificationClaimResponse.model_validate(vc) for vc in claims]
        ))

    return ConversationResponse(
        id=conv.id,
        title=conv.title,
        document_id=conv.document_id,
        collection_id=conv.collection_id,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=msg_responses
    )


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    msg_in: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conv = res.scalars().first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    # 1. Save user message
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=msg_in.content
    )
    db.add(user_msg)
    await db.commit()

    # Update conversation title if first message
    if conv.title == "New Research Session":
        conv.title = msg_in.content[:45] + ("..." if len(msg_in.content) > 45 else "")
        await db.commit()

    # Determine document scope
    target_doc_id = msg_in.document_id or conv.document_id

    # 2. Execute RAG Engine
    rag_result = await rag_engine.process_question(
        db=db,
        query=msg_in.content,
        user_id=current_user.id,
        conversation_id=conversation_id,
        document_id=target_doc_id,
        collection_id=msg_in.collection_id or conv.collection_id,
        enable_verification=msg_in.enable_verification
    )

    # 3. Save assistant message
    asst_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=rag_result["answer"],
        retrieval_latency_ms=rag_result["retrieval_latency_ms"],
        answer_latency_ms=rag_result["answer_latency_ms"]
    )
    db.add(asst_msg)
    await db.commit()
    await db.refresh(asst_msg)

    # 4. Save Citations
    saved_citations = []
    for cit in rag_result["citations"]:
        c_record = Citation(
            message_id=asst_msg.id,
            document_id=cit["document_id"],
            page_number=cit["page_number"],
            chunk_id=cit.get("chunk_id"),
            snippet=cit["snippet"],
            confidence_score=cit["confidence_score"]
        )
        db.add(c_record)
        saved_citations.append(c_record)

    # 5. Save Verification Claims
    saved_claims = []
    for vc in rag_result["verification_claims"]:
        vc_record = VerificationClaim(
            message_id=asst_msg.id,
            claim_text=vc["claim_text"],
            status=vc["status"],
            document_id=vc.get("document_id"),
            document_name=vc.get("document_name"),
            page_number=vc.get("page_number"),
            supporting_passage=vc.get("supporting_passage"),
            rationale=vc.get("rationale"),
            confidence_score=vc.get("confidence_score", 0.95)
        )
        db.add(vc_record)
        saved_claims.append(vc_record)

    await db.commit()

    return MessageResponse(
        id=asst_msg.id,
        conversation_id=asst_msg.conversation_id,
        role=asst_msg.role,
        content=asst_msg.content,
        retrieval_latency_ms=asst_msg.retrieval_latency_ms,
        answer_latency_ms=asst_msg.answer_latency_ms,
        created_at=asst_msg.created_at,
        citations=[
            CitationResponse(
                id=c.id,
                document_id=c.document_id,
                document_name=next((cit["document_name"] for cit in rag_result["citations"] if cit["document_id"] == c.document_id), "Document"),
                page_number=c.page_number,
                chunk_id=c.chunk_id,
                snippet=c.snippet,
                confidence_score=c.confidence_score
            )
            for c in saved_citations
        ],
        verification_claims=[
            VerificationClaimResponse(
                id=vc.id,
                claim_text=vc.claim_text,
                status=vc.status,
                document_id=vc.document_id,
                document_name=vc.document_name,
                page_number=vc.page_number,
                supporting_passage=vc.supporting_passage,
                rationale=vc.rationale,
                confidence_score=vc.confidence_score
            )
            for vc in saved_claims
        ]
    )


@router.post("/messages/{message_id}/feedback")
async def submit_feedback(
    message_id: str,
    feedback_in: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Message).where(Message.id == message_id))
    msg = res.scalars().first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found.")

    fb = Feedback(
        message_id=message_id,
        user_id=current_user.id,
        rating=feedback_in.rating,
        comment=feedback_in.comment
    )
    db.add(fb)
    await db.commit()
    return {"message": "Feedback recorded."}


@router.get("/suggested_questions")
async def get_suggested_questions():
    """Provides high-value suggested research prompts for the user interface."""
    return [
        "What was Acme Technologies' total revenue and net income in Q3 2024?",
        "Compare Acme's enterprise retention rate between Q3 2024 and Q4 2024.",
        "What is the annual home office stipend in the 2023 policy vs 2024 policy?",
        "What are the core working hours specified in the remote work policy?",
        "Which dense embedding model and vector dimension are used in DocuMind?",
        "What was the total R&D expenditure across Q3 and Q4 2024 combined?"
    ]
