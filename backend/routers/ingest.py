"""
Ingest Router
POST /api/ingest — load PDFs into FAISS vector store for a given role
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.rag_service import ingest_knowledge_base, ROLE_TO_FOLDER

router = APIRouter(prefix="/api/ingest", tags=["ingest"])


class IngestRequest(BaseModel):
    role: str


@router.post("/")
async def ingest_role_knowledge_base(request: IngestRequest):
    if request.role not in ROLE_TO_FOLDER:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown role '{request.role}'. Valid: {list(ROLE_TO_FOLDER.keys())}",
        )
    try:
        chunks = ingest_knowledge_base(request.role)
        return {
            "role": request.role,
            "chunks_indexed": chunks,
            "message": f"Successfully indexed {chunks} chunks for {request.role}",
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.get("/status")
async def get_ingest_status():
    """Check which roles have vector stores ready."""
    import os
    from config import settings

    status = {}
    for role, folder in ROLE_TO_FOLDER.items():
        store_path = os.path.join(settings.VECTOR_STORE_PATH, folder)
        status[role] = os.path.exists(store_path)

    return {"status": status}