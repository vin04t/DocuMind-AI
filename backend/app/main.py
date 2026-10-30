import os
import glob
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base, AsyncSessionLocal
from app.api import auth, documents, collections, chat, verification, conflicts, analytics, activity
from app.services.storage import storage_service
from app.models import Document, User
from app.core.security import get_password_hash
from sqlalchemy import select


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Initialize default demo user and ingest sample documents if empty
    async with AsyncSessionLocal() as db:
        # Check if demo user exists
        user_res = await db.execute(select(User).where(User.email == "demo@documind.ai"))
        user = user_res.scalars().first()
        if not user:
            user = User(
                email="demo@documind.ai",
                hashed_password=get_password_hash("DocuMind2026!"),
                full_name="Lead Researcher",
                is_active=True,
                is_superuser=True
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        # Check if documents exist; if empty, ingest samples
        doc_count_res = await db.execute(select(Document))
        existing_docs = doc_count_res.scalars().all()
        if len(existing_docs) == 0:
            sample_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../sample_documents"))
            pdf_files = glob.glob(os.path.join(sample_dir, "*.pdf"))
            for pdf_path in sorted(pdf_files):
                filename = os.path.basename(pdf_path)
                try:
                    with open(pdf_path, "rb") as f:
                        content = f.read()
                    dest_path, file_hash, file_size = storage_service.save_file(filename, content)
                    new_doc = Document(
                        user_id=user.id,
                        filename=filename,
                        file_path=dest_path,
                        file_size=file_size,
                        file_hash=file_hash,
                        status="UPLOADED"
                    )
                    db.add(new_doc)
                    await db.commit()
                    await db.refresh(new_doc)
                    # Process document pipeline
                    from app.api.documents import process_document_pipeline
                    await process_document_pipeline(new_doc.id, db, user.id)
                except Exception as e:
                    print(f"[Startup] Error ingesting sample document {filename}: {e}")

            # Run initial conflict detection
            try:
                from app.api.conflicts import run_conflict_detection
                await run_conflict_detection(db)
            except Exception as e:
                print(f"[Startup] Conflict detection initial scan: {e}")

    yield

    # Shutdown: clean up engine
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Evidence-Grounded Document Intelligence Platform API",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(documents.router, prefix=settings.API_V1_STR)
app.include_router(collections.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=settings.API_V1_STR)
app.include_router(verification.router, prefix=settings.API_V1_STR)
app.include_router(conflicts.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(activity.router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": "connected"
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to DocuMind AI API",
        "docs_url": "/docs",
        "health": "/health"
    }
