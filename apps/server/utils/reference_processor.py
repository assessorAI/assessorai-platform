import json
import base64
import secrets
from typing import Optional, List, Tuple
from fastapi import HTTPException
from sqlalchemy.orm import Session
from ..models import ContextItem
from ..routers.upload import store_bytes_to_gcs, resolve_ref
from ..db.models import File as FileModel
import logging

logger = logging.getLogger(__name__)

def process_references(
    referencias_json: Optional[str],
    session: Session,
    mandato_id: Optional[int],
    current_user
) -> Tuple[List[dict], List[str], Optional[str]]:
    """
    Process referencias JSON string into files and texts for LLM consumption.
    Returns: (files, texts, referencias_file_uri)
    """
    files: List[dict] = []
    texts: List[str] = []
    referencias_file_uri: Optional[str] = None

    if referencias_json:
        try:
            raw_items = json.loads(referencias_json)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON in referencias")
        if not isinstance(raw_items, list):
            raise HTTPException(status_code=400, detail="Referencias must be a JSON list")
        for raw in raw_items:
            try:
                item = ContextItem.model_validate(raw)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid context item: {e}")
            if item.type == 'text':
                texts.append(item.content)
            elif item.type == 'reference':
                # item.content should now be a file_id from the database
                try:
                    file_id = int(item.content)
                    file_obj = session.get(FileModel, file_id)
                    if file_obj:
                        files.append({"type": "remote", "path": file_obj.file_path})
                    else:
                        logger.warning(f"File with id {file_id} not found")
                except (ValueError, TypeError):
                    # Fallback to legacy resolve_ref for backward compatibility
                    meta = resolve_ref(item.content)
                    files.append({"type": "remote", "path": meta["file_uri"]})
            elif item.type == 'file':
                # Espera-se base64 no content
                try:
                    data_str = item.content
                    if "," in data_str and data_str.strip().startswith("data:"):
                        data_str = data_str.split(",", 1)[1]
                    raw = base64.b64decode(data_str)
                except Exception:
                    raise HTTPException(status_code=400, detail="Invalid base64 in file content")
                fname = f"context-{secrets.token_urlsafe(6)}.bin"
                result = store_bytes_to_gcs(raw, filename=fname, content_type=None, mandato_id=mandato_id, current_user=current_user, session=session)
                files.append({"type": "remote", "path": result["file_uri"]})
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported reference type: {item.type}")

    # Save references to GCS for audit trail
    if referencias_json:
        try:
            referencias_filename = f"referencias-{secrets.token_urlsafe(8)}.json"
            referencias_data = json.dumps(raw_items, ensure_ascii=False, indent=2)

            referencias_result = store_bytes_to_gcs(
                referencias_data.encode('utf-8'),
                filename=referencias_filename,
                content_type="application/json",
                mandato_id=mandato_id,
                current_user=current_user,
                session=session
            )
            referencias_file_uri = referencias_result["file_uri"]
            logger.info(f"Saved references to GCS: {referencias_file_uri}")
        except Exception as e:
            logger.warning(f"Failed to save references to GCS: {e}")
            # Continue execution even if saving references fails

    return files, texts, referencias_file_uri