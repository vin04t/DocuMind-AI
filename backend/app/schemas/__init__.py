from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: str
    is_active: bool
    is_superuser: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# Collection Schemas
class CollectionBase(BaseModel):
    name: str
    description: Optional[str] = None


class CollectionCreate(CollectionBase):
    pass


class CollectionResponse(CollectionBase):
    id: str
    user_id: str
    document_count: Optional[int] = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Document Schemas
class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_size: int
    page_count: int
    status: str
    error_message: Optional[str] = None
    is_scanned: bool = False
    collection_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentChunkResponse(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    page_number: int
    content: str
    clean_content: Optional[str] = None
    token_count: int

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailResponse(DocumentResponse):
    chunks: List[DocumentChunkResponse] = []


# Citation Schemas
class CitationResponse(BaseModel):
    id: str
    document_id: str
    document_name: Optional[str] = None
    page_number: int
    chunk_id: Optional[str] = None
    snippet: str
    confidence_score: float = 1.0

    model_config = ConfigDict(from_attributes=True)


# Verification Schemas
class VerificationClaimResponse(BaseModel):
    id: str
    claim_text: str
    status: str  # SUPPORTED, PARTIALLY_SUPPORTED, CONTRADICTED, NOT_SUPPORTED
    document_id: Optional[str] = None
    document_name: Optional[str] = None
    page_number: Optional[int] = None
    supporting_passage: Optional[str] = None
    rationale: Optional[str] = None
    confidence_score: float = 0.95

    model_config = ConfigDict(from_attributes=True)


# Chat & Conversation Schemas
class MessageCreate(BaseModel):
    content: str
    document_id: Optional[str] = None
    collection_id: Optional[str] = None
    enable_verification: bool = True


class FeedbackCreate(BaseModel):
    rating: str  # positive, negative
    comment: Optional[str] = None


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    retrieval_latency_ms: float = 0.0
    answer_latency_ms: float = 0.0
    citations: List[CitationResponse] = []
    verification_claims: List[VerificationClaimResponse] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(BaseModel):
    id: str
    title: str
    document_id: Optional[str] = None
    collection_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# Conflict Schemas
class ConflictResponse(BaseModel):
    id: str
    document_a_id: str
    document_a_name: str
    page_a: int
    statement_a: str
    passage_a: str

    document_b_id: str
    document_b_name: str
    page_b: int
    statement_b: str
    passage_b: str

    conflict_type: str
    explanation: str
    review_status: str  # NEEDS_INVESTIGATION, REVIEWED, RESOLVED
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConflictStatusUpdateRequest(BaseModel):
    review_status: str
    resolution_notes: Optional[str] = None


# Activity Schemas
class ActivityResponse(BaseModel):
    id: str
    event_type: str
    status: str
    document_id: Optional[str] = None
    document_name: Optional[str] = None
    message_id: Optional[str] = None
    duration_ms: float = 0.0
    details_json: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Analytics Schemas
class VolumeDataPoint(BaseModel):
    date: str
    count: int


class LatencyDataPoint(BaseModel):
    date: str
    avg_retrieval_ms: float
    avg_answer_ms: float


class VerificationStats(BaseModel):
    supported: int
    partially_supported: int
    contradicted: int
    not_supported: int


class AnalyticsSummaryResponse(BaseModel):
    total_documents: int
    indexed_pages: int
    total_questions: int
    total_collections: int
    avg_retrieval_latency_ms: float
    avg_answer_latency_ms: float
    evidence_coverage_percentage: float
    verification_stats: VerificationStats
    queries_over_time: List[VolumeDataPoint]
    latency_trends: List[LatencyDataPoint]
    frequently_queried_documents: List[Dict[str, Any]]
