from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models import Collection, Document, User
from app.schemas import CollectionCreate, CollectionResponse
from app.api.auth import get_current_user

router = APIRouter(prefix="/collections", tags=["Collections"])


@router.get("", response_model=List[CollectionResponse])
@router.get("/", response_model=List[CollectionResponse], include_in_schema=False)
async def list_collections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Collection).order_by(Collection.name)
    if not current_user.is_superuser:
        stmt = stmt.where((Collection.user_id == current_user.id) | (Collection.user_id.is_(None)))
    res = await db.execute(stmt)
    collections = res.scalars().all()

    result = []
    for c in collections:
        count_res = await db.execute(
            select(func.count(Document.id)).where(Document.collection_id == c.id)
        )
        doc_count = count_res.scalar() or 0
        c_dict = CollectionResponse.model_validate(c).model_dump()
        c_dict["document_count"] = doc_count
        result.append(CollectionResponse(**c_dict))

    return result


@router.post("", response_model=CollectionResponse, status_code=201)
@router.post("/", response_model=CollectionResponse, status_code=201, include_in_schema=False)
async def create_collection(
    collection_in: CollectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    col = Collection(
        name=collection_in.name,
        description=collection_in.description,
        user_id=current_user.id
    )
    db.add(col)
    await db.commit()
    await db.refresh(col)
    
    col_dict = CollectionResponse.model_validate(col).model_dump()
    col_dict["document_count"] = 0
    return CollectionResponse(**col_dict)


@router.delete("/{collection_id}")
async def delete_collection(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Collection).where(Collection.id == collection_id))
    col = res.scalars().first()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found.")

    if col.user_id and col.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You do not have permission to delete this collection."
        )

    await db.delete(col)
    await db.commit()
    return {"message": "Collection deleted successfully."}
