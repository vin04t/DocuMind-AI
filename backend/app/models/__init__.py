import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    collections = relationship("Collection", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    activities = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")


class Collection(Base):
    __tablename__ = "collections"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="collections")
    documents = relationship("Document", back_populates="collection")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    collection_id = Column(String(36), ForeignKey("collections.id", ondelete="SET NULL"), nullable=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    file_hash = Column(String(64), nullable=False, index=True)  # SHA-256 for duplicate detection
    page_count = Column(Integer, default=0, nullable=False)
    status = Column(String(32), default="UPLOADED", nullable=False, index=True)
    # Statuses: UPLOADED, EXTRACTING, CHUNKING, EMBEDDING, INDEXED, FAILED
    error_message = Column(Text, nullable=True)
    is_scanned = Column(Boolean, default=False)
    metadata_json = Column(Text, nullable=True)  # Extra metadata, title, author, etc.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="documents")
    collection = relationship("Collection", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    citations = relationship("Citation", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=False, index=True)  # 1-indexed
    content = Column(Text, nullable=False)
    clean_content = Column(Text, nullable=True)
    start_char = Column(Integer, default=0)
    end_char = Column(Integer, default=0)
    token_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="chunks")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), default="New Research Session", nullable=False)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    collection_id = Column(String(36), ForeignKey("collections.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(16), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    retrieval_latency_ms = Column(Float, default=0.0)
    answer_latency_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    citations = relationship("Citation", back_populates="message", cascade="all, delete-orphan")
    verification_claims = relationship("VerificationClaim", back_populates="message", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="message", uselist=False, cascade="all, delete-orphan")


class Citation(Base):
    __tablename__ = "citations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    chunk_id = Column(String(36), nullable=True)
    snippet = Column(Text, nullable=False)
    confidence_score = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    message = relationship("Message", back_populates="citations")
    document = relationship("Document", back_populates="citations")


class VerificationClaim(Base):
    __tablename__ = "verification_claims"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    claim_text = Column(Text, nullable=False)
    status = Column(String(32), default="SUPPORTED", nullable=False)
    # Statuses: SUPPORTED, PARTIALLY_SUPPORTED, CONTRADICTED, NOT_SUPPORTED
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    document_name = Column(String(255), nullable=True)
    page_number = Column(Integer, nullable=True)
    supporting_passage = Column(Text, nullable=True)
    rationale = Column(Text, nullable=True)
    confidence_score = Column(Float, default=0.95)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    message = relationship("Message", back_populates="verification_claims")


class ConflictRecord(Base):
    __tablename__ = "conflict_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_a_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    document_a_name = Column(String(255), nullable=False)
    page_a = Column(Integer, nullable=False)
    statement_a = Column(Text, nullable=False)
    passage_a = Column(Text, nullable=False)

    document_b_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    document_b_name = Column(String(255), nullable=False)
    page_b = Column(Integer, nullable=False)
    statement_b = Column(Text, nullable=False)
    passage_b = Column(Text, nullable=False)

    conflict_type = Column(String(64), nullable=False)  # 'numerical', 'policy', 'date', 'version'
    explanation = Column(Text, nullable=False)
    review_status = Column(String(32), default="NEEDS_INVESTIGATION", nullable=False)
    # Statuses: NEEDS_INVESTIGATION, REVIEWED, RESOLVED
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    # Event types: DOCUMENT_UPLOAD, PDF_EXTRACTION, CHUNK_GENERATION, EMBEDDING_GENERATION,
    # INDEXING, USER_QUERY, RETRIEVAL, ANSWER_GENERATION, VERIFICATION, CONFLICT_DETECTION, FAILURE
    status = Column(String(32), default="SUCCESS", nullable=False)
    # Statuses: SUCCESS, FAILED, WARNING, PENDING
    document_id = Column(String(36), nullable=True)
    document_name = Column(String(255), nullable=True)
    message_id = Column(String(36), nullable=True)
    duration_ms = Column(Float, default=0.0)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="activities")


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, unique=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = Column(String(16), nullable=False)  # 'positive', 'negative'
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    message = relationship("Message", back_populates="feedback")
