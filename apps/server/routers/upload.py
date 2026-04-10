from fastapi import HTTPException, APIRouter, UploadFile, Query, Depends
from google.cloud import storage
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func
from typing import Optional, List
import os
import logging

from ..db.session import get_session
from ..db.models import File as FileModel, User as UserORM
from ..models import PermissionLevel
from .deps import get_current_user, resolve_mandato_with_permissions
from ..services.file_processing import FileTextExtractor, should_generate_embeddings, generate_file_embedding
from ..services.embeddings import get_embedding_provider

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/files",
    tags=["files"]
)

def _get_bucket_and_client():
    client = storage.Client()
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    if not bucket_name:
        raise HTTPException(status_code=500, detail="GCS_BUCKET_NAME not configured")
    bucket = client.bucket(bucket_name)
    return client, bucket, bucket_name


@router.post("/upload")
async def upload_file(
    file: UploadFile,
    mandato_id: int,
    title: Optional[str] = None,
    file_type: Optional[str] = "document",
    current_user: UserORM = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Upload a file to the specified mandato with optional embedding generation."""
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    # Validate mandato access
    mandato = resolve_mandato_with_permissions(session, current_user, mandato_id)

    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    # Validate file size
    max_file_size = int(os.getenv("MAX_UPLOAD_FILE_SIZE", "52_428_800"))  # 50MB default
    if file_size > max_file_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {max_file_size / (1024*1024):.1f}MB"
        )

    # Upload to GCS
    _, bucket, bucket_name = _get_bucket_and_client()
    blob_name = f"{mandato_id}/{current_user.id}/{file.filename}"
    blob = bucket.blob(blob_name)

    try:
        # Check if file already exists
        if blob.exists():
            # Return existing file info
            existing_file = session.scalar(
                select(FileModel).where(
                    and_(
                        FileModel.mandato_id == mandato_id,
                        FileModel.user_id == current_user.id,
                        FileModel.filename == file.filename
                    )
                )
            )
            if existing_file:
                return {
                    "message": "File already exists",
                    "file_id": existing_file.id,
                    "file_path": existing_file.file_path,
                    "has_embeddings": existing_file.has_embeddings
                }

        # Upload new file
        blob.upload_from_string(file_content, content_type=file.content_type)
        gs_path = f"gs://{bucket_name}/{blob.name}"

        # Extract text if possible
        extracted_text = None
        if file.content_type:
            extracted_text = FileTextExtractor.extract_text(file_content, file.content_type)

        # Generate embedding if configured and applicable
        embedding = None
        has_embeddings = False
        if extracted_text and should_generate_embeddings(file_size, file.content_type or ""):
            try:
                provider = get_embedding_provider()
                embedding = generate_file_embedding(extracted_text, provider)
                has_embeddings = embedding is not None and len(embedding) > 0
            except Exception as e:
                logger.warning(
                    "Failed to generate embedding for file",
                    extra={
                        "filename": file.filename,
                        "mandato_id": mandato_id,
                        "user_id": current_user.id,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )

        # Save to database
        file_record = FileModel(
            mandato_id=mandato_id,
            user_id=current_user.id,
            filename=file.filename,
            title=title or file.filename,
            file_type=file_type,
            file_path=gs_path,
            file_size=file_size,
            content_type=file.content_type,
            extracted_text=extracted_text,
            embedding=embedding,
            has_embeddings=has_embeddings
        )
        session.add(file_record)
        session.commit()
        session.refresh(file_record)

        return {
            "message": "File uploaded successfully",
            "file_id": file_record.id,
            "file_path": gs_path,
            "has_embeddings": has_embeddings
        }

    except Exception as e:
        session.rollback()
        logger.error(
            "File upload failed",
            extra={
                "filename": file.filename,
                "mandato_id": mandato_id,
                "user_id": current_user.id,
                "file_size": file_size,
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to upload file. Please try again or contact support.")


@router.get("/list")
async def list_files(
    mandato_id: int,
    file_types: Optional[str] = Query(None, description="Comma-separated list of file types to filter by (e.g., 'document,image,video'). Supports single types like 'document' or multiple types with spaces trimmed automatically."),
    user_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: UserORM = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """List files for a mandato with optional filtering and pagination.

    Supports filtering by multiple file types using comma-separated values.
    Examples:
    - Single type: ?file_types=document
    - Multiple types: ?file_types=document,image,video
    - With spaces: ?file_types=document, image , video (spaces are trimmed)
    """
    # Validate mandato access
    mandato = resolve_mandato_with_permissions(session, current_user, mandato_id)

    # Build base query
    base_query = select(FileModel).where(FileModel.mandato_id == mandato_id)

    if file_types:
        # Parse comma-separated values and filter empty strings
        types_list = [t.strip() for t in file_types.split(',') if t.strip()]
        if types_list:  # Only filter if we have valid types
            base_query = base_query.where(FileModel.file_type.in_(types_list))
    if user_id:
        base_query = base_query.where(FileModel.user_id == user_id)

    # Get total count
    total_count = session.scalar(
        select(func.count()).select_from(base_query.subquery())
    )

    # Apply pagination and ordering
    query = base_query.order_by(FileModel.upload_date.desc()).limit(limit).offset(offset)

    files = session.scalars(query).all()

    # Format response
    file_list = []
    for file_obj in files:
        file_list.append({
            "id": file_obj.id,
            "filename": file_obj.filename,
            "title": file_obj.title,
            "file_type": file_obj.file_type,
            "file_size": file_obj.file_size,
            "content_type": file_obj.content_type,
            "upload_date": file_obj.upload_date.isoformat(),
            "has_embeddings": file_obj.has_embeddings,
            "user": {
                "id": file_obj.user.id,
                "email": file_obj.user.email,
                "first_name": file_obj.user.first_name,
                "last_name": file_obj.user.last_name
            }
        })

    return {
        "files": file_list,
        "total": total_count,
        "limit": limit,
        "offset": offset
    }


@router.delete("/delete/{file_id}")
async def delete_file(
    file_id: int,
    current_user: UserORM = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete a file with proper authorization."""
    # Get file
    file_obj = session.get(FileModel, file_id)
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")

    # Check permissions
    is_manager = current_user.permission_level == PermissionLevel.manager
    is_file_owner = file_obj.user_id == current_user.id
    has_mandato_access = any(m.id == file_obj.mandato_id for m in current_user.mandatos)

    if not (is_file_owner or (is_manager and has_mandato_access) or current_user.permission_level == PermissionLevel.admin):
        raise HTTPException(status_code=403, detail="Not authorized to delete this file")

    try:
        # Delete from GCS
        _, bucket, _ = _get_bucket_and_client()
        blob_name = file_obj.file_path.replace(f"gs://{bucket.name}/", "")
        blob = bucket.blob(blob_name)
        blob.delete()

        # Delete from database (cascade will handle chunks)
        session.delete(file_obj)
        session.commit()

        return {"message": f"File {file_obj.filename} deleted successfully"}

    except Exception as e:
        session.rollback()
        logger.error(
            "File deletion failed",
            extra={
                "file_id": file_id,
                "filename": file_obj.filename,
                "mandato_id": file_obj.mandato_id,
                "user_id": current_user.id,
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to delete file. Please try again or contact support.")


@router.get("/{file_id}/content")
async def get_file_content(
    file_id: int,
    current_user: UserORM = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Download the content of a specific file."""
    # Get file
    file_obj = session.get(FileModel, file_id)
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")

    # Check permissions - user must have access to the file's mandato
    has_access = any(m.id == file_obj.mandato_id for m in current_user.mandatos)
    if not has_access and current_user.permission_level not in [PermissionLevel.admin, PermissionLevel.manager]:
        raise HTTPException(status_code=403, detail="Not authorized to access this file")

    try:
        # Download from GCS
        _, bucket, _ = _get_bucket_and_client()
        blob_name = file_obj.file_path.replace(f"gs://{bucket.name}/", "")
        blob = bucket.blob(blob_name)

        if not blob.exists():
            raise HTTPException(status_code=404, detail="File not found in storage")

        # Download content
        content = blob.download_as_bytes()

        # Return file content with appropriate headers
        from fastapi.responses import Response
        return Response(
            content=content,
            media_type=file_obj.content_type or "application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename=\"{file_obj.filename}\""
            }
        )

    except Exception as e:
        logger.error(
            "File download failed",
            extra={
                "file_id": file_id,
                "filename": file_obj.filename,
                "mandato_id": file_obj.mandato_id,
                "user_id": current_user.id,
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to download file. Please try again or contact support.")


@router.get("/ref/{ref_id}")
async def get_reference(ref_id: str):
    """Legacy endpoint for backward compatibility."""
    # This endpoint is kept for backward compatibility but now returns minimal info
    # In the new system, files are accessed by ID through the list endpoint
    raise HTTPException(status_code=410, detail="This endpoint is deprecated. Use /files/list instead.")


def store_bytes_to_gcs(data: bytes, filename: str, content_type: Optional[str] = None, userId: str = 'dummy', mandato_id: Optional[int] = None, current_user: Optional[UserORM] = None, session: Optional[Session] = None) -> dict:
    """Legacy compatibility function for expertPL.py"""
    if mandato_id and current_user and session:
        # Use new system
        _, bucket, bucket_name = _get_bucket_and_client()
        blob_name = f"{mandato_id}/{current_user.id}/{filename}"
        blob = bucket.blob(blob_name)

        try:
            blob.upload_from_string(data, content_type=content_type)
            gs_path = f"gs://{bucket_name}/{blob.name}"

            # Extract text if possible
            extracted_text = None
            if content_type:
                extracted_text = FileTextExtractor.extract_text(data, content_type)

            # Generate embedding if configured
            embedding = None
            has_embeddings = False
            if extracted_text and should_generate_embeddings(len(data), content_type or ""):
                try:
                    provider = get_embedding_provider()
                    embedding = generate_file_embedding(extracted_text, provider)
                    has_embeddings = embedding is not None and len(embedding) > 0
                except Exception as e:
                    logger.debug(
                        "Embedding generation skipped for legacy upload",
                        extra={
                            "filename": filename,
                            "mandato_id": mandato_id,
                            "error_type": type(e).__name__
                        }
                    )

            # Save to database
            file_record = FileModel(
                mandato_id=mandato_id,
                user_id=current_user.id,
                filename=filename,
                title=filename,
                file_type="document",
                file_path=gs_path,
                file_size=len(data),
                content_type=content_type,
                extracted_text=extracted_text,
                embedding=embedding,
                has_embeddings=has_embeddings
            )
            session.add(file_record)
            session.commit()
            session.refresh(file_record)

            return {
                "message": "File uploaded successfully",
                "file_uri": gs_path,
                "public_url": blob.public_url,
                "ref_id": str(file_record.id)
            }
        except Exception as e:
            session.rollback()
            logger.error(
                "Failed to store file in legacy upload function",
                extra={
                    "filename": filename,
                    "mandato_id": mandato_id,
                    "user_id": current_user.id if current_user else None,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise HTTPException(status_code=500, detail="Failed to store file. Please try again or contact support.")
    else:
        # Fallback for old usage
        _, bucket, bucket_name = _get_bucket_and_client()
        blob = bucket.blob(f"{userId}/{filename}")
        blob.upload_from_string(data, content_type=content_type)
        gs_path = f"gs://{bucket_name}/{blob.name}"
        return {
            "message": "File uploaded successfully",
            "file_uri": gs_path,
            "public_url": blob.public_url,
            "ref_id": "legacy"
        }


def resolve_ref(ref_id: str) -> dict:
    """Legacy compatibility function for expertPL.py"""
    # Try to find file by ID first
    try:
        file_id = int(ref_id)
        # This would need session, but for compatibility we'll return a mock response
        return {
            "userId": "legacy",
            "blob_name": f"legacy/{ref_id}",
            "public_url": f"https://legacy-url/{ref_id}",
            "file_uri": f"gs://legacy/{ref_id}",
            "filename": f"file_{ref_id}",
            "content_type": "application/octet-stream"
        }
    except ValueError:
        # Legacy ref_id format
        return {
            "userId": "legacy",
            "blob_name": f"legacy/{ref_id}",
            "public_url": f"https://legacy-url/{ref_id}",
            "file_uri": f"gs://legacy/{ref_id}",
            "filename": f"file_{ref_id}",
            "content_type": "application/octet-stream"
        }