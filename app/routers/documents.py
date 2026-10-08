from fastapi import APIRouter, Request, HTTPException, Depends, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, List
import uuid
import magic
from datetime import datetime
from app.auth import get_current_user
from app.database import db
from app.services.document_processor import document_processor
from app.services.embedding_service import embedding_service
from app.services.openai_service import openai_service
import os
from app.auth import get_current_user  # Add 'app.'
from app.database import db  # Add 'app.'
from app.services.document_processor import document_processor  # Add 'app.'
from app.services.embedding_service import embedding_service  # Add 'app.'
from app.services.openai_service import openai_service  # Add 'app.'
router = APIRouter(prefix="/dashboard", tags=["documents"])
templates = Jinja2Templates(directory="app/templates")

# Allowed file types
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt'}
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword',
    'text/plain'
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# ==================== HTML PAGES ====================


@router.get("/documents", response_class=HTMLResponse)
async def documents_page(
    request: Request,
    bot_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Show documents page with option to filter by bot"""

    # Get user's bots for dropdown
    bots = db.execute(
        "SELECT id, name FROM bots WHERE user_id = %s ORDER BY created_at DESC",
        (current_user['id'],),
        fetch_all=True
    )

    # Get documents (filter by bot if specified)
    if bot_id:
        # Verify bot belongs to user
        bot = db.execute(
            "SELECT id FROM bots WHERE id = %s AND user_id = %s",
            (bot_id, current_user['id']),
            fetch_one=True
        )

        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")

        documents = db.execute(
            """SELECT d.*, b.name as bot_name 
               FROM documents d
               JOIN bots b ON d.bot_id = b.id
               WHERE d.bot_id = %s AND b.user_id = %s
               ORDER BY d.uploaded_at DESC""",
            (bot_id, current_user['id']),
            fetch_all=True
        )
    else:
        # Get all documents for user's bots
        documents = db.execute(
            """SELECT d.*, b.name as bot_name 
               FROM documents d
               JOIN bots b ON d.bot_id = b.id
               WHERE b.user_id = %s
               ORDER BY d.uploaded_at DESC""",
            (current_user['id'],),
            fetch_all=True
        )

    # Get bot details if specified
    selected_bot = None
    if bot_id:
        selected_bot = db.execute(
            "SELECT id, name FROM bots WHERE id = %s AND user_id = %s",
            (bot_id, current_user['id']),
            fetch_one=True
        )

    # Calculate stats
    stats = {
        'total_documents': len(documents) if documents else 0,
        'total_size': sum(doc['file_size'] for doc in documents) if documents else 0,
        'processed': sum(1 for doc in documents if doc['processed']) if documents else 0,
        'pending': sum(1 for doc in documents if not doc['processed']) if documents else 0
    }

    return templates.TemplateResponse(
        "dashboard/documents.html",
        {
            "request": request,
            "bots": bots or [],
            "documents": documents or [],
            "selected_bot": selected_bot,
            "stats": stats,
            "current_user": current_user,
            "max_file_size": MAX_FILE_SIZE
        }
    )

# ==================== API ENDPOINTS ====================


@router.post("/api/documents/upload")
async def upload_document(
    request: Request,
    bot_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload and process a document"""

    # Verify bot belongs to user
    bot = db.execute(
        "SELECT id, user_id FROM bots WHERE id = %s AND user_id = %s",
        (bot_id, current_user['id']),
        fetch_one=True
    )

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset position

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    # Check file type
    file_content = await file.read()
    mime_type = magic.from_buffer(file_content, mime=True)

    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: PDF, DOCX, DOC, TXT"
        )

    # Check document limit based on plan
    doc_count = db.execute(
        "SELECT COUNT(*) as count FROM documents WHERE bot_id = %s",
        (bot_id,),
        fetch_one=True
    )

    limits = {
        'free': 5,
        'pro': 100,
        'business': 1000
    }

    max_docs = limits.get(current_user['plan_type'], 5)

    if doc_count['count'] >= max_docs:
        raise HTTPException(
            status_code=400,
            detail=f"Your {current_user['plan_type']} plan allows maximum {max_docs} documents per bot. Please upgrade to upload more."
        )

    # Save document to database
    document_id = str(uuid.uuid4())

    db.execute(
        """INSERT INTO documents (id, bot_id, file_name, file_type, file_data, file_size, processed)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (document_id, bot_id, file.filename,
         mime_type, file_content, file_size, False)
    )

    # Start processing in background (we'll do it synchronously for now)
    try:
        # Process document and generate embeddings
        chunks_created = embedding_service.process_document(
            bot_id=bot_id,
            document_id=document_id,
            file_data=file_content,
            file_type=mime_type
        )

        return {
            "success": True,
            "document_id": document_id,
            "file_name": file.filename,
            "chunks_created": chunks_created,
            "message": f"Document uploaded and processed successfully. Created {chunks_created} knowledge chunks."
        }

    except Exception as e:
        # Mark document as failed (we'll add a status field later)
        print(f"Error processing document: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error processing document: {str(e)}")


@router.get("/api/documents")
async def get_documents(
    bot_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get list of documents"""

    if bot_id:
        # Verify bot belongs to user
        bot = db.execute(
            "SELECT id FROM bots WHERE id = %s AND user_id = %s",
            (bot_id, current_user['id']),
            fetch_one=True
        )

        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")

        documents = db.execute(
            """SELECT id, bot_id, file_name, file_type, file_size, processed, uploaded_at
               FROM documents 
               WHERE bot_id = %s 
               ORDER BY uploaded_at DESC""",
            (bot_id,),
            fetch_all=True
        )
    else:
        documents = db.execute(
            """SELECT d.id, d.bot_id, d.file_name, d.file_type, d.file_size, d.processed, d.uploaded_at,
                      b.name as bot_name
               FROM documents d
               JOIN bots b ON d.bot_id = b.id
               WHERE b.user_id = %s
               ORDER BY d.uploaded_at DESC""",
            (current_user['id'],),
            fetch_all=True
        )

    # Format file sizes
    for doc in documents:
        doc['file_size_formatted'] = format_file_size(doc['file_size'])
        doc['uploaded_at_formatted'] = doc['uploaded_at'].strftime(
            '%Y-%m-%d %H:%M')

    return documents


@router.get("/api/documents/{document_id}")
async def get_document(document_id: str, current_user: dict = Depends(get_current_user)):
    """Get document details"""

    doc = db.execute(
        """SELECT d.*, b.name as bot_name, b.user_id 
           FROM documents d
           JOIN bots b ON d.bot_id = b.id
           WHERE d.id = %s""",
        (document_id,),
        fetch_one=True
    )

    if not doc or doc['user_id'] != current_user['id']:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get chunk count
    chunks = db.execute(
        "SELECT COUNT(*) as count FROM embeddings WHERE document_id = %s",
        (document_id,),
        fetch_one=True
    )

    # Remove binary data from response
    doc.pop('file_data', None)
    doc['chunk_count'] = chunks['count'] if chunks else 0
    doc['file_size_formatted'] = format_file_size(doc['file_size'])

    return doc


@router.delete("/api/documents/{document_id}")
async def delete_document(document_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a document and its embeddings"""

    # Check if document exists and belongs to user
    doc = db.execute(
        """SELECT d.id, b.user_id 
           FROM documents d
           JOIN bots b ON d.bot_id = b.id
           WHERE d.id = %s""",
        (document_id,),
        fetch_one=True
    )

    if not doc or doc['user_id'] != current_user['id']:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete document (cascade will delete embeddings)
    db.execute("DELETE FROM documents WHERE id = %s", (document_id,))

    return {"success": True, "message": "Document deleted successfully"}


@router.post("/api/documents/{document_id}/reprocess")
async def reprocess_document(document_id: str, current_user: dict = Depends(get_current_user)):
    """Reprocess a document (delete existing embeddings and recreate)"""

    # Check if document exists and belongs to user
    doc = db.execute(
        """SELECT d.*, b.user_id 
           FROM documents d
           JOIN bots b ON d.bot_id = b.id
           WHERE d.id = %s""",
        (document_id,),
        fetch_one=True
    )

    if not doc or doc['user_id'] != current_user['id']:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete existing embeddings
    db.execute("DELETE FROM embeddings WHERE document_id = %s", (document_id,))

    # Reprocess document
    try:
        chunks_created = embedding_service.process_document(
            bot_id=doc['bot_id'],
            document_id=document_id,
            file_data=doc['file_data'],
            file_type=doc['file_type']
        )

        return {
            "success": True,
            "chunks_created": chunks_created,
            "message": f"Document reprocessed successfully. Created {chunks_created} knowledge chunks."
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error reprocessing document: {str(e)}")

# Helper function to format file size


def format_file_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
