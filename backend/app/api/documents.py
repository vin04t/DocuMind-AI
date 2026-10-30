import os
import time
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, desc
from app.core.database import get_db
from app.models import Document, DocumentChunk, User
from app.schemas import DocumentResponse, DocumentDetailResponse
from app.api.auth import get_current_user
from app.services.storage import storage_service
from app.services.document_processor import document_processor, DocumentProcessingError
from app.services.chunker import chunker
from app.services.embedding import embedding_service
from app.services.vector_store import vector_store
from app.services.bm25_retriever import bm25_retriever
from app.services.activity_service import activity_service

router = APIRouter(prefix="/documents", tags=["Documents"])


async def process_document_pipeline(
    document_id: str,
    db: AsyncSession,
    user_id: str
):
    """
    Executes the complete document ingestion pipeline:
    Extraction -> Chunking -> Embedding -> Vector DB & BM25 indexing.
    """
    start_time = time.time()
    res = await db.execute(select(Document).where(Document.id == document_id))
    doc = res.scalars().first()
    if not doc:
        return

    try:
        # Stage 1: Extraction
        doc.status = "EXTRACTING"
        await db.commit()
        await activity_service.log_event(
            db, "PDF_EXTRACTION", "PENDING", user_id=user_id,
            document_id=doc.id, document_name=doc.filename
        )

        extraction_result = document_processor.extract_document(doc.file_path)
        doc.page_count = extraction_result["page_count"]
        doc.is_scanned = extraction_result["is_scanned"]
        pages = extraction_result["pages"]

        # Stage 2: Chunking
        doc.status = "CHUNKING"
        await db.commit()
        await activity_service.log_event(
            db, "CHUNK_GENERATION", "PENDING", user_id=user_id,
            document_id=doc.id, document_name=doc.filename,
            details={"page_count": doc.page_count}
        )

        chunks_data = chunker.chunk_pages(document_id=doc.id, pages=pages)

        # Clear any existing chunks (for reprocessing)
        await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc.id))
        
        # Save chunks to SQL
        db_chunks = []
        for c in chunks_data:
            db_chunk = DocumentChunk(
                id=c["id"],
                document_id=doc.id,
                chunk_index=c["chunk_index"],
                page_number=c["page_number"],
                content=c["content"],
                clean_content=c["clean_content"],
                start_char=c["start_char"],
                end_char=c["end_char"],
                token_count=c["token_count"]
            )
            db.add(db_chunk)
            db_chunks.append(db_chunk)
        await db.commit()

        # Stage 3: Embedding & Indexing
        doc.status = "EMBEDDING"
        await db.commit()
        await activity_service.log_event(
            db, "EMBEDDING_GENERATION", "PENDING", user_id=user_id,
            document_id=doc.id, document_name=doc.filename,
            details={"chunks_count": len(chunks_data)}
        )

        chunk_texts = [c["content"] for c in chunks_data]
        embeddings = embedding_service.embed_texts(chunk_texts)

        # Clean existing entries from ChromaDB and BM25 to prevent duplicate embeddings on reprocessing
        vector_store.delete_document(doc.id)
        bm25_retriever.remove_document(doc.id)

        # Add to ChromaDB vector store
        vector_store.add_chunks(chunks=chunks_data, embeddings=embeddings)

        # Index in BM25
        bm25_retriever.index_chunks(chunks_data, append=True)

        # Stage 4: Indexed Completion
        doc.status = "INDEXED"
        doc.error_message = None
        duration = (time.time() - start_time) * 1000
        await db.commit()

        await activity_service.log_event(
            db, "INDEXING", "SUCCESS", user_id=user_id,
            document_id=doc.id, document_name=doc.filename,
            duration_ms=duration,
            details={
                "pages": doc.page_count,
                "chunks": len(chunks_data),
                "is_scanned": doc.is_scanned
            }
        )

    except Exception as e:
        doc.status = "FAILED"
        doc.error_message = str(e)
        duration = (time.time() - start_time) * 1000
        await db.commit()

        await activity_service.log_event(
            db, "FAILURE", "FAILED", user_id=user_id,
            document_id=doc.id, document_name=doc.filename,
            duration_ms=duration,
            details={"error": str(e)}
        )


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    collection_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Uploads, validates, and processes a PDF file.
    Performs duplicate detection via SHA-256.
    """
    safe_filename = os.path.basename(file.filename)
    if not safe_filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents are supported."
        )

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty."
        )

    # Validate file size limit
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB."
        )

    # Validate PDF magic header
    if not content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PDF format: File is missing the standard '%PDF-' binary header."
        )

    file_path, file_hash, file_size = storage_service.save_file(safe_filename, content)

    # Check for duplicate document
    dup_res = await db.execute(select(Document).where(Document.file_hash == file_hash))
    existing_doc = dup_res.scalars().first()
    if existing_doc:
        # Return existing document or reprocess
        return DocumentResponse.model_validate(existing_doc)

    # Create new document record
    doc = Document(
        user_id=current_user.id,
        collection_id=collection_id if collection_id != "none" and collection_id else None,
        filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        file_hash=file_hash,
        status="UPLOADED"
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    await activity_service.log_event(
        db, "DOCUMENT_UPLOAD", "SUCCESS", user_id=current_user.id,
        document_id=doc.id, document_name=doc.filename,
        details={"file_size": file_size}
    )

    # Run ingestion pipeline
    await process_document_pipeline(doc.id, db, current_user.id)
    await db.refresh(doc)

    return DocumentResponse.model_validate(doc)


@router.get("", response_model=List[DocumentResponse])
@router.get("/", response_model=List[DocumentResponse], include_in_schema=False)
async def list_documents(
    query: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    collection_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Document).order_by(desc(Document.created_at))
    if status_filter and status_filter != "ALL":
        stmt = stmt.where(Document.status == status_filter)
    if collection_id and collection_id != "ALL":
        stmt = stmt.where(Document.collection_id == collection_id)
    if query:
        stmt = stmt.where(Document.filename.ilike(f"%{query}%"))

    res = await db.execute(stmt)
    docs = res.scalars().all()
    return [DocumentResponse.model_validate(d) for d in docs]


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Document).where(Document.id == document_id))
    doc = res.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    chunks_res = await db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
    )
    chunks = chunks_res.scalars().all()
    
    doc_dict = DocumentResponse.model_validate(doc).model_dump()
    doc_dict["chunks"] = [
        {
            "id": c.id,
            "document_id": c.document_id,
            "chunk_index": c.chunk_index,
            "page_number": c.page_number,
            "content": c.content,
            "clean_content": c.clean_content,
            "token_count": c.token_count
        }
        for c in chunks
    ]
    return DocumentDetailResponse(**doc_dict)


@router.get("/{document_id}/file")
async def get_document_file(document_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Document).where(Document.id == document_id))
    doc = res.scalars().first()
    if not doc or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="Document file not found.")

    return FileResponse(
        doc.file_path,
        media_type="application/pdf",
        filename=doc.filename
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Document).where(Document.id == document_id))
    doc = res.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if doc.user_id and doc.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to delete this document."
        )

    # Remove from ChromaDB vector store
    vector_store.delete_document(document_id)
    # Remove from BM25 index
    bm25_retriever.remove_document(document_id)
    # Remove file from storage
    storage_service.delete_file(doc.file_path)

    filename = doc.filename
    await db.delete(doc)
    await db.commit()

    await activity_service.log_event(
        db, "DOCUMENT_DELETE", "SUCCESS", user_id=current_user.id,
        document_id=document_id, document_name=filename
    )

    return {"message": "Document deleted successfully."}


@router.post("/{document_id}/reprocess", response_model=DocumentResponse)
async def reprocess_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Document).where(Document.id == document_id))
    doc = res.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if doc.user_id and doc.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to reprocess this document."
        )

    await process_document_pipeline(document_id, db, current_user.id)
    await db.refresh(doc)
    return DocumentResponse.model_validate(doc)
